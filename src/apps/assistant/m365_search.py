"""Tìm kiếm tệp trên SharePoint Document Library cho trợ lý tài liệu.

Ưu tiên Graph `POST /search/query`. Khi search chưa được admin consent
(400/403), lùi về duyệt các thư mục nghiệp vụ đã cấu hình và khớp theo tên tệp -
chậm hơn và không có full-text, nhưng chỉ cần quyền Files mà dự án đã cấp.

Hai giới hạn cần biết trước khi đọc code:
- Kết quả SharePoint chỉ gồm tên và `webUrl`; ai mở được tệp do quyền M365 của
  chính người đó quyết định (spec mục 4). Tên tệp vì thế vẫn lộ cho mọi tài khoản
  đăng nhập, kể cả tệp của công văn mật.
- Không có bộ lọc RBAC theo từng tệp như `db_search`: Graph app-only nhìn thấy
  cả thư viện, không nhìn thấy quyền của người đang hỏi.
"""
from __future__ import annotations

from datetime import datetime

from django.conf import settings

from apps.m365.graph_client import GraphAPIError, GraphNotConfigured, get_graph_client

from .nlp import ParsedQuery, normalize

MAX_RESULTS = 20
# Graph trả lỗi 400 khi query quá dài hoặc cú pháp search không chấp nhận.
MAX_QUERY_LENGTH = 200
SCORE_NUMBER = 100
SCORE_NAME_MATCH = 10


def _needles(parsed: ParsedQuery) -> list[str]:
    needles = [normalize(phrase) for phrase in parsed.phrases]
    needles.extend(parsed.keywords)
    if parsed.doc_number:
        needles.append(normalize(parsed.doc_number))
    return [needle for needle in needles if needle]


def _as_date(value: str):
    """`lastModifiedDateTime` kiểu ISO 8601 ("...Z") thành `date`, lỗi thì None."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _to_result(hit: dict, parsed: ParsedQuery) -> dict:
    name = hit.get("name", "")
    name_fold = normalize(name)
    number_fold = normalize(parsed.doc_number) if parsed.doc_number else ""
    score = SCORE_NUMBER if number_fold and number_fold in name_fold else 0
    for needle in _needles(parsed):
        if needle in name_fold:
            score += SCORE_NAME_MATCH
    return {
        "source": "sharepoint",
        "type": "file",
        "title": name,
        "meta": "SharePoint",
        "url": hit.get("web_url", ""),
        "date": _as_date(hit.get("last_modified", "")),
        "score": score,
    }


def _fallback_folders() -> list[tuple[str, str]]:
    """Các cặp (thư viện, thư mục) được duyệt khi Graph search bị từ chối.

    Tên thư mục lấy từ `M365_FOLDER_MAP` - cùng bảng mà `apps.m365.storage` và
    `upload_to_dispatches` dùng để ghi tệp, nên danh mục trợ lý duyệt đúng nơi
    nghiệp vụ thực sự lưu. (`M365_FOLDER_*` chỉ là tên biến môi trường trong
    settings.py, không phải attribute của settings.)
    """
    library = getattr(settings, "M365_SHAREPOINT_LIBRARY", "Documents") or "Documents"
    folder_map = getattr(settings, "M365_FOLDER_MAP", {}) or {}
    seen, pairs = set(), []
    for kind in ("dispatches", "incoming_docs", "outgoing_docs"):
        folder = (folder_map.get(kind) or "").strip("/")
        if folder and folder not in seen:
            seen.add(folder)
            pairs.append((library, folder))
    pairs.append((library, ""))
    return pairs


def _fallback_listing(client, parsed: ParsedQuery) -> list[dict]:
    needles = _needles(parsed)
    if not needles:
        return []
    results: list[dict] = []
    seen_urls: set[str] = set()
    for library, folder in _fallback_folders():
        try:
            hits = client.list_folder_files(library, folder)
        except GraphAPIError as exc:
            # Thiếu cấu hình site thì `_drive_id` gọi `site_id` và raise
            # GraphNotConfigured - phải để nó thoát lên để báo "not_configured",
            # còn thiếu thư nghiệp vụ (404) thì bỏ qua và thử thư mục kế.
            if isinstance(exc, GraphNotConfigured):
                raise
            continue
        for hit in hits:
            name_fold = normalize(hit.get("name", ""))
            if not any(needle in name_fold for needle in needles):
                continue
            # Thư mục con và thư viện gốc cùng liệt kê một tệp: webUrl là khóa
            # duy nhất để không trả trùng, nếu không SharePoint nhấn chìm DB.
            url = hit.get("web_url", "")
            key = url or hit.get("name", "")
            if not key or key in seen_urls:
                continue
            seen_urls.add(key)
            results.append(_to_result(hit, parsed))
            if len(results) >= MAX_RESULTS:
                return results
    return results


def _build_query(parsed: ParsedQuery) -> str:
    terms = list(parsed.phrases) + list(parsed.keywords)
    if terms:
        return " ".join(terms)[:MAX_QUERY_LENGTH]
    return (parsed.doc_number or "")[:MAX_QUERY_LENGTH]


def search_sharepoint(parsed: ParsedQuery) -> tuple[list[dict], str | None]:
    """Trả `(results, error_note)`; `error_note=None` nghĩa là nguồn này OK.

    - `not_configured` : thiếu M365 (credentials hoặc site) - caller không nên
      hiển thị cảnh báo lỗi, chỉ là nguồn chưa bật.
    - `search_fallback`: Graph search bị từ chối, đã duyệt thư mục thay.
    - `unavailable`    : lỗi mạng/5xx/429 - caller trả kết quả DB kèm `partial`.
    """
    client = get_graph_client()
    if not client.is_configured():
        return [], "not_configured"
    query = _build_query(parsed)
    if not query.strip():
        return [], None
    try:
        hits = client.search_files(query, top=MAX_RESULTS)
    except GraphNotConfigured:
        return [], "not_configured"
    except GraphAPIError as exc:
        if exc.status_code not in (400, 403):
            return [], "unavailable"
        try:
            return _fallback_listing(client, parsed), "search_fallback"
        except GraphNotConfigured:
            return [], "not_configured"
    results = [_to_result(hit, parsed) for hit in hits[:MAX_RESULTS]]
    # Graph xếp theo điểm liên quan của riêng nó, còn `score` ở đây so được với
    # kết quả DB trong `services.ask`, nên phải theo điểm của ta.
    results.sort(key=lambda item: -item["score"])
    return results, None
