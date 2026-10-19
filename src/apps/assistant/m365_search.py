"""Tìm kiếm tệp trên SharePoint Document Library cho trợ lý tài liệu.

Ưu tiên Graph `POST /search/query`. Khi search chưa được admin consent
(400/403), lùi về duyệt các thư mục nghiệp vụ đã cấu hình và khớp theo tên tệp -
chậm hơn và không có full-text, nhưng chỉ cần quyền Files mà dự án đã cấp.

Ba cửa phải qua trước khi gọi mạng, vì Graph chạy app-only:
- `M365_STORAGE_ENABLED` là công tắc duy nhất của toàn dự án cho M365 (xem
  `apps/m365/storage.py` và `ops/run_tests.py`). Chỉ đọc credentials thì không
  phân biệt được "chưa bật" với "bật nhưng sai", và test sẽ tùy thuộc `.env`.
- Người hỏi phải xem được CẢ BA loại tệp mà nguồn này có thể trả về. App-only
  nghĩa là token thấy cả thư viện, không thấy quyền của người đang hỏi, và Graph
  không biết một tệp thuộc đối tượng nào - nên không thể lọc từng kết quả như
  `db_search` làm với `visible_dispatches_for`/`can_read_file`. Ba thư mục
  allowlist không chỉ chứa công văn: `CongVanDen`/`CongVanDi` còn nhận tệp đính
  kèm của `IncomingDocument`/`OutgoingDocument` (`apps/common/uploads.py:80-85`),
  và cổng chặn hai đối tượng đó bằng quyền văn thư. Cửa vì vậy là GIAO của phạm vi
  độ mật (`FULL_DISPATCH_SECURITY_ROLES`) và hai quyền sổ văn thư
  (`SHARED_LIBRARY_PERMISSIONS`) - vai trò nào còn bị cổng chặn một kiểu tệp thì
  không được nghe tên tệp kiểu đó từ SharePoint.
- Kết quả chỉ được giữ nếu nằm trong một thư mục công văn đã cấu hình, theo từng
  đoạn đường dẫn. Tên hồ sơ ứng viên hay đơn nghỉ phép tự hiện ra trong khung
  chat là lộ dữ liệu, kể cả khi liên kết không mở được.
"""
from __future__ import annotations

from datetime import datetime
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
# kèm vào đó, và cổng mở chúng bằng đúng hai quyền này (`data_access.py:99-100`).
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


def _url_segments(url: str) -> set[str]:
    """Các đoạn của ĐƯỜNG DẪN trong webUrl, không phân biệt hoa/thường.

    Chỉ `path`, không đọc query string hay fragment: tham số kiểu
    `view.aspx?initialid=%2F...%2FCongVan%2F` mô tả một VIEW của danh sách, không
    phải vị trí của tệp, nên giải mã cả URL sẽ biến hai chữ "CongVan" trong tham
    số thành một đoạn đường dẫn giả và giữ lại tệp nằm ở thư mục khác.
    `%20` vẫn được giải mã (tên thư viện có dấu cách là chuyện bình thường), còn
    `%2F` trong đường dẫn thì không bao giờ được phép thành dấu phân cách - webUrl
    thật của Graph không có dạng đó, nên thà bỏ sót còn hơn lộ.
    """
    path = urlsplit(url or "").path
    if "%2f" in path.lower():
        return set()
    return {
        unquote(segment).casefold()
        for segment in path.split("/")
        if unquote(segment)
    }


def _in_dispatch_folder(url: str, folders: tuple[str, ...]) -> bool:
    segments = _url_segments(url)
    return any(folder.casefold() in segments for folder in folders)


def can_query_sharepoint(user) -> bool:
    """Người hỏi có được xem MỌI tệp mà nguồn này có thể trả về không.

    Hai điểm dễ tưởng sai:

    - `manage_office` một mình thì rộng ở cửa độ mật (SYS_ADMIN là văn thư nhưng
      cổng vẫn ẩn công văn Mật) và `FULL_DISPATCH_SECURITY_ROLES` một mình thì
      rộng ở cửa sổ văn thư (DIRECTOR xem được mọi độ mật nhưng không có
      `manage_office`, tức cổng từ chối tệp đính kèm của `IncomingDocument`).
      Graph không lọc hộ theo từng tệp được, nên phải lấy giao của hai phạm vi.
    - `is_active` phải kiểm trước `is_superuser`: `login_required` chỉ hỏi
      `is_authenticated` và `ModelBackend` không kiểm lại `is_active` giữa phiên,
      trong khi `visible_dispatches_for` đã trả `qs.none()` cho tài khoản chết.
    """
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if get_role_code(user) not in FULL_DISPATCH_SECURITY_ROLES:
        return False
    return all(has_permission(user, code) for code in SHARED_LIBRARY_PERMISSIONS)


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

    Chỉ ba thư mục công văn trong `M365_FOLDER_MAP` - cùng bảng mà
    `apps.m365.storage` và `upload_to_dispatches` dùng để ghi tệp, nên danh mục
    trợ lý duyệt đúng nơi nghiệp vụ thực sự lưu. KHÔNG kèm thư viện gốc: listing
    gốc liệt kê mọi tệp của cả site, tức là lộ tên hồ sơ ứng viên và đơn nghỉ
    phép cho một tài khoản chỉ có quyền văn thư.
    """
    library = getattr(settings, "M365_SHAREPOINT_LIBRARY", "Documents") or "Documents"
    return [(library, folder) for folder in _dispatch_folders()]


def _fallback_listing(client, parsed: ParsedQuery) -> list[dict]:
    needles = _needles(parsed)
    if not needles:
        return []
    results: list[dict] = []
    seen_urls: set[str] = set()
    for library, folder in _fallback_folders():
        try:
            hits = client.list_folder_files(library, folder, timeout=ASSISTANT_TIMEOUT)
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
    folders = _dispatch_folders()
    if not folders:
        return [], "not_configured"
    if not can_query_sharepoint(user):
        return [], RESTRICTED_NOTE
    client = get_graph_client()
    if not client.is_configured():
        return [], "not_configured"
    query = _build_query(parsed)
    if not query.strip():
        return [], None
    try:
        hits = client.search_files(query, top=MAX_RESULTS, timeout=ASSISTANT_TIMEOUT)
    except GraphNotConfigured:
        return [], "not_configured"
    except GraphAPIError as exc:
        if exc.status_code not in (400, 403):
            return [], "unavailable"
        try:
            return _fallback_listing(client, parsed), "search_fallback"
        except GraphNotConfigured:
            return [], "not_configured"
    # Graph tìm cấp tenant rồi mới lọc theo site trong `search_files`, nên vẫn
    # còn tệp ngoài phạm vi công văn. Giữ lại có nghĩa là lộ tên tệp.
    kept = [hit for hit in hits if _in_dispatch_folder(hit.get("web_url", ""), folders)]
    if not kept and hits:
        # 20 kết quả liên quan nhất đều thuộc site/thư mục khác: thư mục công
        # văn vẫn có thể có tệp khớp, nên phải thử đường lùi thay vì báo "hết".
        try:
            return _fallback_listing(client, parsed), "search_fallback"
        except GraphNotConfigured:
            return [], "not_configured"
    results = [_to_result(hit, parsed) for hit in kept[:MAX_RESULTS]]
    # Graph xếp theo điểm liên quan của riêng nó, còn `score` ở đây so được với
    # kết quả DB trong `services.ask`, nên phải theo điểm của ta.
    results.sort(key=lambda item: -item["score"])
    return results, None
