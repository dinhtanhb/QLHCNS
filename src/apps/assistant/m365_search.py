"""Tìm tài liệu trong đúng thư viện/thư mục và theo chính sách chủ dự án.

Công văn đến/đi và báo cáo hoạt động dùng chung; CV theo quyền ứng viên.
Graph chạy app-only nên mỗi nguồn phải xác minh metadata root và lọc origin/path.
Tìm drive có đường lùi duyệt phân trang/thư mục con khi chỉ mục chưa thấy tệp
hoặc Search bị từ chối; lỗi mạng/giới hạn trả trạng thái chưa đầy đủ.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
import re
from urllib.parse import unquote, urlsplit

from django.conf import settings

from apps.m365.graph_client import GraphAPIError, GraphNotConfigured, get_graph_client
from apps.security.data_access import FULL_DISPATCH_SECURITY_ROLES
from apps.security.permissions import get_role_code, has_permission

from .nlp import ParsedQuery, normalize

MAX_RESULTS = 20
# Graph trả lỗi 400 khi query quá dài hoặc cú pháp search không chấp nhận.
MAX_QUERY_LENGTH = 200
SCORE_NUMBER = 100
SCORE_NAME_MATCH = 10
# (connect, read) cho một lượt gọi Graph trong khung chat. Mặc định của
# `_request` là 60s, hợp lý khi upload nhưng một câu hỏi không được chiếm
# worker nhiều phút, nhất là khi đường lùi có thể gọi thêm vài lượt nữa.
ASSISTANT_TIMEOUT = (3, 10)
# Ba thư mục mà nghiệp vụ công văn thực sự ghi tệp vào; cũng là allowlist duy
# nhất cho kết quả search.
DISPATCH_FOLDER_KEYS = ("dispatches", "incoming_docs", "outgoing_docs")
# Hai thư mục cuối không chỉ chứa OfficialDispatch: sổ văn thư cũng ghi tệp đính
# kèm vào đó, và cổng mở chúng bằng đúng hai quyền này (hai nhánh
# `office.incomingdocument`/`office.outgoingdocument` của `can_read_file`).
SHARED_LIBRARY_PERMISSIONS = ("manage_office", "access_outgoing_document")
# Không phải sự cố và không phải "chưa bật": người hỏi đơn giản không thuộc
# phạm vi nguồn này, nên `services.PARTIAL_NOTES` không liệt kê nó.
RESTRICTED_NOTE = "restricted"


def _dispatch_folders() -> tuple[str, ...]:
    """Tên thư mục công văn, lấy từ `M365_FOLDER_MAP` - bảng mà
    `apps.m365.storage` dùng để ghi tệp, không phải biến môi trường trong
    settings.py. rỗng nghĩa là chưa cấu hình, và khi đó không nên đoán."""
    folder_map = getattr(settings, "M365_FOLDER_MAP", {}) or {}
    seen: list[str] = []
    for kind in DISPATCH_FOLDER_KEYS:
        folder = (folder_map.get(kind) or "").strip("/")
        if folder and folder.casefold() not in [name.casefold() for name in seen]:
            seen.append(folder)
    return tuple(seen)


def _location(url: str):
    """Canonical origin and ordered path; reject ambiguous path separators."""
    try:
        parsed = urlsplit(url or "")
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        segments = []
        for raw in parsed.path.split("/"):
            if not raw:
                continue
            decoded = unquote(raw)
            # A second escape could become traversal after another decoder.
            if decoded in (".", "..") or any(c in decoded for c in ("/", "\\", "%")):
                return None
            segments.append(decoded.casefold())
        return (parsed.hostname.casefold(), parsed.port or 443), tuple(segments)
    except ValueError:
        return None


def _in_dispatch_folder(url: str, roots: tuple[str, ...]) -> bool:
    location = _location(url)
    if location is None:
        return False
    origin, path = location
    for root in roots:
        boundary = _location(root)
        if boundary is None:
            continue
        root_origin, root_path = boundary
        if origin == root_origin and len(path) > len(root_path) and path[:len(root_path)] == root_path:
            return True
    return False


def _folder_roots(client, folders=None) -> dict[str, str]:
    """Resolve only folders of the configured library; never guess URL aliases."""
    roots = {}
    for library, folder in _fallback_folders():
        if folders is not None and folder not in folders:
            continue
        try:
            url = client.get_folder_web_url(library, folder, timeout=ASSISTANT_TIMEOUT)
        except GraphNotConfigured:
            raise
        except GraphAPIError as exc:
            if exc.status_code == 404:
                continue
            raise
        location = _location(url)
        if location is None or not location[1]:
            raise GraphAPIError("Không xác minh được biên thư mục tài liệu.", status_code=502)
        roots[folder] = url
    return roots


def can_query_sharepoint(user) -> bool:
    """Shared sources require an authenticated, active account; roots add scope."""
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    return True


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


def _decision_period(hit):
    """Imported decisions use a filename date, then YYYY/MM folders, never upload date."""
    for day, month, year in re.findall(r"(?<!\d)(\d{1,2})[._-](\d{1,2})[._-]((?:19|20)\d{2})(?!\d)", hit.get("name", "")):
        try:
            value = date(int(year), int(month), int(day))
            return value, value, "ngày trong tên tệp"
        except ValueError:
            continue
    location = _location(hit.get("web_url", ""))
    if location:
        parts = location[1][:-1]
        for index, part in enumerate(parts):
            if not re.fullmatch(r"(?:19|20)\d{2}", part):
                continue
            year = int(part)
            if index + 1 < len(parts) and re.fullmatch(r"0?[1-9]|1[0-2]", parts[index + 1]):
                month = int(parts[index + 1])
                return date(year, month, 1), date(year, month, monthrange(year, month)[1]), "tháng từ thư mục"
            return date(year, 1, 1), date(year, 12, 31), "năm từ thư mục"
    return None


def _to_result(hit: dict, parsed: ParsedQuery) -> dict:
    name = hit.get("name", "")
    name_fold = normalize(name)
    number_fold = normalize(parsed.doc_number) if parsed.doc_number else ""
    score = SCORE_NUMBER if number_fold and number_fold in name_fold else 0
    for needle in _needles(parsed):
        if needle in name_fold:
            score += SCORE_NAME_MATCH
    period = _decision_period(hit) if parsed.doc_type == "personnel_decision" else None
    return {
        "source": "sharepoint",
        "type": "file",
        "title": name,
        "meta": "SharePoint · " + period[2] if period else "SharePoint · ngày cập nhật",
        "url": hit.get("web_url", ""),
        "date": (period[0] if period[0] == period[1] else None) if period else _as_date(hit.get("last_modified", "")),
        "score": score,
    }


def _fallback_folders() -> list[tuple[str, str]]:
    """Danh mục nguồn; caller chỉ duyệt các root đã được phép cho người hỏi."""
    library = getattr(settings, "M365_SHAREPOINT_LIBRARY", "Documents") or "Documents"
    folders = list(_dispatch_folders())
    report_folder = (getattr(settings, "M365_FOLDER_MAP", {}).get("activity_reports") or "").strip("/")
    if report_folder and report_folder not in folders:
        folders.append(report_folder)
    cv_folder = (getattr(settings, "M365_FOLDER_MAP", {}).get("recruitment_cv") or "").strip("/")
    if cv_folder and cv_folder not in folders:
        folders.append(cv_folder)
    decision_folder = (getattr(settings, "M365_FOLDER_MAP", {}).get("personnel_decisions") or "").strip("/")
    if decision_folder and decision_folder not in folders:
        folders.append(decision_folder)
    return [(library, folder) for folder in folders]


def _fallback_listing(client, parsed: ParsedQuery, roots: dict[str, str]) -> list[dict]:
    needles = _needles(parsed)
    results: list[dict] = []
    seen_urls: set[str] = set()
    for library, folder in _fallback_folders():
        if folder not in roots:
            continue
        try:
            hits = client.list_folder_files(library, folder, timeout=ASSISTANT_TIMEOUT, recursive=True)
        except GraphAPIError as exc:
            # Thiếu cấu hình site thì `_drive_id` gọi `site_id` và raise
            # GraphNotConfigured - phải để nó thoát lên để báo "not_configured",
            # còn thiếu thư nghiệp vụ (404) thì bỏ qua và thử thư mục kế.
            if isinstance(exc, GraphNotConfigured):
                raise
            if exc.status_code == 404:
                continue
            raise
        for hit in hits:
            if not _in_dispatch_folder(hit.get("web_url", ""), (roots[folder],)):
                continue
            name_fold = normalize(hit.get("name", ""))
            if needles and not any(needle in name_fold for needle in needles):
                continue
            if not _matches_date(hit, parsed):
                continue
            # Các root cấu hình có thể chồng nhau; webUrl loại tệp trùng.
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


def _matches_date(hit, parsed):
    """Graph exposes modification date; use it only when a date was requested."""
    if not parsed.date_from and not parsed.date_to:
        return True
    if parsed.doc_type == "personnel_decision":
        period = _decision_period(hit)
        return bool(period and (not parsed.date_from or period[1] >= parsed.date_from)
                    and (not parsed.date_to or period[0] <= parsed.date_to))
    value = _as_date(hit.get("last_modified", ""))
    return bool(value and (not parsed.date_from or value >= parsed.date_from)
                and (not parsed.date_to or value <= parsed.date_to))


def allowed_file_folders(user):
    """Shared boundary for search and every signed file GET."""
    if not can_query_sharepoint(user):
        return []
    keys = ["incoming_docs", "outgoing_docs", "activity_reports"]
    if has_permission(user, "view_candidate"):
        keys.append("recruitment_cv")
    if has_permission(user, "view_all_personnel_decisions"):
        keys.append("personnel_decisions")
    if getattr(user, "is_superuser", False) or (
        get_role_code(user) in FULL_DISPATCH_SECURITY_ROLES
        and all(has_permission(user, code) for code in SHARED_LIBRARY_PERMISSIONS)
    ):
        keys.append("dispatches")
    folder_map = getattr(settings, "M365_FOLDER_MAP", {}) or {}
    return [folder_map[key].strip("/") for key in keys if folder_map.get(key)]


def search_sharepoint(parsed: ParsedQuery, user) -> tuple[list[dict], str | None]:
    """Trả `(results, error_note)`; `error_note=None` nghĩa là nguồn này OK.

    - `not_configured` : thiếu M365 (cờ bật/tắt, credentials hoặc site) - caller
      không nên hiển thị cảnh báo lỗi, chỉ là nguồn chưa bật.
    - `restricted`     : người hỏi không có quyền xem sổ công văn - nguồn bị tắt
      riêng cho họ, cũng không phải sự cố.
    - `search_fallback`: Graph search bị từ chối, hoặc mọi kết quả bị loại vì
      ngoài thư mục công văn, đã duyệt thư mục thay.
    - `unavailable`    : lỗi mạng/5xx/429 - caller trả kết quả DB kèm `partial`.
    """
    if not getattr(settings, "M365_STORAGE_ENABLED", False):
        return [], "not_configured"
    if not can_query_sharepoint(user):
        return [], RESTRICTED_NOTE
    folder_map = getattr(settings, "M365_FOLDER_MAP", {}) or {}
    kinds = {
        "Incoming": ("incoming_docs",), "Outgoing": ("outgoing_docs",),
        "dispatch": ("incoming_docs", "outgoing_docs"),
        "activity_report": ("activity_reports",), "candidate": ("recruitment_cv",),
        "leave": (), "asset": (), "personnel_decision": ("personnel_decisions",),
        "InternalDirective": (), "document": (),
    }
    selected = kinds.get(parsed.doc_type, ("incoming_docs", "outgoing_docs", "activity_reports"))
    allowed = allowed_file_folders(user)
    folders = [folder_map[key].strip("/") for key in selected if folder_map.get(key)
               and folder_map[key].strip("/") in allowed]
    # CongVan also contains internal directives. Keep its previous narrow gate;
    # raw Graph results cannot distinguish legacy incoming files from directives.
    if (parsed.doc_type in (None, "dispatch") and folder_map.get("dispatches")
            and folder_map["dispatches"].strip("/") in allowed):
        folders.append(folder_map["dispatches"].strip("/"))
    if not folders:
        return [], RESTRICTED_NOTE if _fallback_folders() else "not_configured"
    client = get_graph_client()
    if not client.is_configured():
        return [], "not_configured"
    query = _build_query(parsed)
    if not query.strip():
        try:
            return _fallback_listing(client, parsed, _folder_roots(client, folders)), None
        except GraphNotConfigured:
            return [], "not_configured"
        except GraphAPIError:
            return [], "unavailable"
    roots = None
    try:
        hits = client.search_files(query, top=MAX_RESULTS, timeout=ASSISTANT_TIMEOUT)
        if hits:
            roots = _folder_roots(client, folders)
    except GraphNotConfigured:
        return [], "not_configured"
    except GraphAPIError as exc:
        if exc.status_code not in (400, 403):
            return [], "unavailable"
        try:
            if roots is None:
                roots = _folder_roots(client, folders)
            return _fallback_listing(client, parsed, roots), "search_fallback"
        except GraphNotConfigured:
            return [], "not_configured"
        except GraphAPIError:
            return [], "unavailable"
    # Drive search vẫn có tệp ngoài các root được phép của người hỏi.
    boundaries = tuple((roots or {}).values())
    kept = [hit for hit in hits if _in_dispatch_folder(hit.get("web_url", ""), boundaries)
            and _matches_date(hit, parsed)]
    if not kept:
        # Chỉ mục rỗng hoặc top hit ngoài root chưa chứng minh thư mục hết tệp.
        try:
            return _fallback_listing(client, parsed, roots if roots is not None else _folder_roots(client, folders)), "search_fallback"
        except GraphNotConfigured:
            return [], "not_configured"
        except GraphAPIError:
            return [], "unavailable"
    results = [_to_result(hit, parsed) for hit in kept[:MAX_RESULTS]]
    # Graph xếp theo điểm liên quan của riêng nó, còn `score` ở đây so được với
    # kết quả DB trong `services.ask`, nên phải theo điểm của ta.
    results.sort(key=lambda item: -item["score"])
    return results, None
