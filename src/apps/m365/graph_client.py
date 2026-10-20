"""
Client Microsoft Graph API (app-only / client credentials flow) dùng để đọc/ghi
tệp lên SharePoint Document Library (và OneDrive dạng "drive" bất kỳ — cá nhân
hay dùng chung — vì trong Graph, SharePoint library và OneDrive đều là "drive").

Vì đây là kết nối chạy ngầm (server-side, không có người dùng đăng nhập tương
tác), ta dùng "Application permissions" (không phải "Delegated permissions").
App Registration trên Azure AD cần các quyền: Sites.ReadWrite.All,
Files.ReadWrite.All, và đã được admin M365 bấm "Grant admin consent".

Xem hướng dẫn lấy Tenant ID / Client ID / Client Secret / Site URL trong
docs/16_M365_Integration_Setup.md.
"""
from __future__ import annotations

import io
import posixpath
import threading
import time

import requests

from django.conf import settings

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
AUTH_AUTHORITY = "https://login.microsoftonline.com/{tenant_id}"
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]

# Ngưỡng theo tài liệu Graph API: tệp <= 4MB dùng PUT trực tiếp; lớn hơn phải
# dùng "upload session" (upload theo từng khối).
SIMPLE_UPLOAD_LIMIT = 4 * 1024 * 1024  # 4 MB
CHUNK_SIZE = 5 * 1024 * 1024  # phải là bội số của 320 KiB theo yêu cầu Graph

# Graph nhận $top tối đa 200 mục cho /children; lớn hơn phải đi tiếp con trỏ
# phân trang mà phương án này không dùng.
FOLDER_PAGE_SIZE = 200

# Mặc định cho mọi lời gọi: đủ dài cho một lượt upload tệp. Ngắn hơn chỉ nên đặt
# ở phía caller có người chờ (trợ lý tài liệu truyền `timeout` xuống).
REQUEST_TIMEOUT = 60


class GraphAPIError(Exception):
    """Lỗi khi gọi Microsoft Graph API (mạng, xác thực, hoặc phản hồi lỗi)."""
    def __init__(self, message, *, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after



class GraphNotConfigured(GraphAPIError):
    """Chưa điền đủ M365_TENANT_ID / M365_CLIENT_ID / M365_CLIENT_SECRET trong .env."""


class GraphClient:
    """
    Wrapper mỏng quanh Microsoft Graph API. Tự lấy & cache access token,
    tự dò site_id / drive_id theo tên site + tên thư viện, và cung cấp các
    thao tác tệp cơ bản (upload/download/delete/exists/url).

    Instance này an toàn dùng lại nhiều lần (token được cache trong tiến
    trình, tự làm mới khi gần hết hạn).
    """

    _lock = threading.Lock()

    def __init__(self):
        self.tenant_id = getattr(settings, "M365_TENANT_ID", "") or ""
        self.client_id = getattr(settings, "M365_CLIENT_ID", "") or ""
        self.client_secret = getattr(settings, "M365_CLIENT_SECRET", "") or ""
        self.site_hostname = getattr(settings, "M365_SHAREPOINT_HOSTNAME", "") or ""
        self.site_path = getattr(settings, "M365_SHAREPOINT_SITE_PATH", "") or ""

        self._token = None
        self._token_expires_at = 0
        self._site_id_cache = None
        self._drive_id_cache = {}

    # ------------------------------------------------------------------
    # Xác thực
    # ------------------------------------------------------------------
    def is_configured(self) -> bool:
        return bool(self.tenant_id and self.client_id and self.client_secret)

    def _require_configured(self):
        if not self.is_configured():
            raise GraphNotConfigured(
                "Chưa cấu hình M365_TENANT_ID / M365_CLIENT_ID / M365_CLIENT_SECRET "
                "trong .env. Xem docs/16_M365_Integration_Setup.md."
            )

    def _get_token(self) -> str:
        self._require_configured()
        with self._lock:
            if self._token and time.time() < self._token_expires_at - 60:
                return self._token

            try:
                import msal
            except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
                raise GraphAPIError(
                    "Thiếu thư viện 'msal'. Chạy: pip install -r requirements.txt"
                ) from exc

            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=AUTH_AUTHORITY.format(tenant_id=self.tenant_id),
            )
            result: dict = app.acquire_token_for_client(scopes=GRAPH_SCOPE)  # type: ignore[assignment]
            if "access_token" not in result:
                raise GraphAPIError(
                    "Không xác thực được với dịch vụ lưu trữ.", status_code=503
                )

            self._token = result["access_token"]
            self._token_expires_at = time.time() + result.get("expires_in", 3600)
            return self._token

    def _headers(self, extra=None):
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        if extra:
            headers.update(extra)
        return headers

    def _request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {}) or {}
        # `timeout=None` từ caller có nghĩa "dùng mặc định của dự án", không phải
        # "không chờ" - requests hiểu None là chờ vô hạn.
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = REQUEST_TIMEOUT
        try:
            response = requests.request(method, url, headers=self._headers(headers), **kwargs)
        except requests.RequestException as error:
            raise GraphAPIError("Không kết nối được dịch vụ lưu trữ.", status_code=503) from error
        if response.status_code >= 400:
            retry_after = response.headers.get("Retry-After")
            raise GraphAPIError(f"Graph trả lỗi HTTP {response.status_code}.",
                status_code=response.status_code, retry_after=retry_after)
        return response

    # ------------------------------------------------------------------
    # Dò site_id / drive_id (cache lại vì hiếm khi đổi)
    # ------------------------------------------------------------------
    @property
    def site_id(self) -> str:
        if self._site_id_cache:
            return self._site_id_cache
        if not (self.site_hostname and self.site_path):
            raise GraphNotConfigured(
                "Chưa cấu hình M365_SHAREPOINT_HOSTNAME / M365_SHAREPOINT_SITE_PATH trong .env."
            )
        url = f"{GRAPH_BASE}/sites/{self.site_hostname}:{self.site_path}"
        data = self._request("GET", url).json()
        self._site_id_cache = data["id"]
        return self._site_id_cache

    def _drive_id(self, library_name: str) -> str:
        """Trả về drive_id của một Document Library (ví dụ 'Documents', 'CongVan')."""
        if library_name in self._drive_id_cache:
            return self._drive_id_cache[library_name]

        url = f"{GRAPH_BASE}/sites/{self.site_id}/drives"
        data = self._request("GET", url).json()
        for drive in data.get("value", []):
            if drive.get("name", "").lower() == library_name.lower():
                self._drive_id_cache[library_name] = drive["id"]
                return drive["id"]

        raise GraphAPIError(
            f"Không tìm thấy thư viện tài liệu '{library_name}' trong site SharePoint. "
            "Kiểm tra lại tên thư viện (Document Library) trên SharePoint."
        )

    def _item_url(self, library_name: str, path: str, suffix: str = "") -> str:
        drive_id = self._drive_id(library_name)
        path = path.lstrip("/")
        return f"{GRAPH_BASE}/drives/{drive_id}/root:/{path}{suffix}"

    def _ensure_parent_folders(self, library_name: str, path: str) -> None:
        """Create missing parent folders in a drive before uploading a file."""
        parent_path = posixpath.dirname(path.strip("/"))
        if not parent_path:
            return

        drive_id = self._drive_id(library_name)
        parent = ""
        for folder_name in parent_path.split("/"):
            if not folder_name:
                continue
            children_url = (
                f"{GRAPH_BASE}/drives/{drive_id}/root/children"
                if not parent
                else f"{GRAPH_BASE}/drives/{drive_id}/root:/{parent}:/children"
            )
            try:
                self._request(
                    "POST",
                    children_url,
                    json={
                        "name": folder_name,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "fail",
                    },
                )
            except GraphAPIError as exc:
                if exc.status_code != 409:
                    raise
            parent = posixpath.join(parent, folder_name)

    # ------------------------------------------------------------------
    # Thao tác tệp
    # ------------------------------------------------------------------
    def upload_file(self, library_name: str, path: str, content: bytes) -> dict:
        """Tải tệp lên thư viện. Tự chọn upload đơn giản hoặc upload session
        theo dung lượng tệp. Trả về JSON metadata (driveItem) của Graph."""
        self._ensure_parent_folders(library_name, path)
        if len(content) <= SIMPLE_UPLOAD_LIMIT:
            url = self._item_url(library_name, path, ":/content")
            response = self._request(
                "PUT", url, data=content,
                headers={"Content-Type": "application/octet-stream"},
            )
            return response.json()

        return self._upload_large_file(library_name, path, content)

    def _upload_large_file(self, library_name: str, path: str, content: bytes) -> dict:
        session_url = self._item_url(library_name, path, ":/createUploadSession")
        session = self._request("POST", session_url, json={}).json()
        upload_url = session["uploadUrl"]

        stream = io.BytesIO(content)
        total = len(content)
        start = 0
        last_response = None
        while start < total:
            chunk = stream.read(CHUNK_SIZE)
            end = start + len(chunk) - 1
            # Upload session dùng URL đã ký sẵn, KHÔNG cần header Authorization.
            last_response = requests.put(
                upload_url,
                data=chunk,
                headers={
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {start}-{end}/{total}",
                },
                timeout=120,
            )
            if last_response.status_code >= 400:
                raise GraphAPIError(
                    f"Upload session lỗi tại byte {start}: "
                    f"HTTP {last_response.status_code}.", status_code=last_response.status_code,
                    retry_after=last_response.headers.get("Retry-After")
                )
            start = end + 1

        return last_response.json()

    def download_file(self, library_name: str, path: str) -> bytes:
        url = self._item_url(library_name, path, ":/content")
        return self._request("GET", url).content

    def delete_file(self, library_name: str, path: str) -> None:
        url = self._item_url(library_name, path)
        try:
            self._request("DELETE", url)
        except GraphAPIError as exc:
            if exc.status_code != 404:
                raise

    def exists(self, library_name: str, path: str) -> bool:
        url = self._item_url(library_name, path)
        try:
            self._request("GET", url)
            return True
        except GraphAPIError as exc:
            if exc.status_code == 404:
                return False
            raise

    def get_metadata(self, library_name: str, path: str) -> dict:
        url = self._item_url(library_name, path)
        return self._request("GET", url).json()

    # ------------------------------------------------------------------
    # Truy vấn (assistant): tìm tệp toàn site và liệt kê một thư mục
    # ------------------------------------------------------------------
    def _file_entry(self, item: dict) -> dict:
        return {
            "name": item.get("name", ""),
            "web_url": item.get("webUrl", ""),
            "last_modified": item.get("lastModifiedDateTime", ""),
        }

    def _site_prefix(self) -> str:
        """`https://<hostname><site_path>` - biên lọc kết quả theo site IHRMS.

        Thiếu một trong hai cấu phần thì prefix rỗng sẽ khớp mọi webUrl, tức là
        lộ tệp của site khác, nên THA mà không suy đoán.

        Dấu `/` thừa ở cuối `site_path` bị cắt vì `.env` là chuỗi gõ tay: giữ nó
        lại thì prefix thành `.../sites/IHRMS/` và mọi `webUrl` thật của chính
        site này không còn khớp, tức nguồn SharePoint im lặng trả rỗng. Cắt xong
        mà không còn đường dẫn nào thì rơi lại đúng trường hợp prefix trụi nói
        trên, nên vẫn THA.
        """
        site_path = self.site_path.rstrip("/")
        if not (self.site_hostname and site_path) or not site_path.startswith("/"):
            raise GraphNotConfigured(
                "Chưa cấu hình M365_SHAREPOINT_HOSTNAME / M365_SHAREPOINT_SITE_PATH trong .env."
            )
        return f"https://{self.site_hostname}{site_path}"

    def _is_site_url(self, web_url: str, prefix: str) -> bool:
        """`web_url` có thật thuộc site này không, so theo ĐOẠN đường dẫn.

        `startswith(prefix)` trần coi `/sites/IHRMS-IT/...` là của `/sites/IHRMS`
        vì site_path là tiền tố chuỗi của site láng giềng; webUrl của site khác
        khi đó còn lọt được cả bộ lọc thư mục phía sau.
        """
        if not web_url.startswith(prefix):
            return False
        remainder = web_url[len(prefix):]
        return remainder in ("", "/") or remainder.startswith("/")

    def search_files(self, query: str, top: int = 20, timeout=None) -> list[dict]:
        """Tìm driveItem bằng Graph /search/query, chỉ giữ kết quả thuộc site IHRMS.

        Graph trả cả những tệp ngoài site (search cấp tenant) nên bước lọc theo
        `_site_prefix()` là bắt buộc, không phải tối ưu.

        Cần quyền app cho phép search (Sites.Read.All / Sites.ReadWrite.All).
        GraphAPIError 400/403 nghĩa là chưa được admin consent; caller tự fallback.
        """
        self._require_configured()
        prefix = self._site_prefix()
        payload = {
            "requests": [{
                "entityTypes": ["driveItem"],
                "query": {"queryString": query[:200]},
                "from": 0,
                "size": top,
                "fields": ["name", "webUrl", "lastModifiedDateTime"],
            }]
        }
        data = self._request("POST", f"{GRAPH_BASE}/search/query", json=payload,
                             timeout=timeout).json()
        results = []
        for block in data.get("value") or []:
            for container in block.get("hitsContainers") or []:
                for hit in container.get("hits") or []:
                    resource = (hit or {}).get("resource") or {}
                    if self._is_site_url(resource.get("webUrl") or "", prefix):
                        results.append(self._file_entry(resource))
                        if len(results) >= top:
                            return results
        return results

    def list_folder_files(self, library_name: str, folder: str = "", timeout=None) -> list[dict]:
        """Liệt kê tệp (không đệ quy, không gồm thư mục con) trong một thư mục.

        Đường lùi cho `search_files`: endpoint `/children` chỉ cần quyền Files
        đã có sẵn, không cần admin consent cho Search.
        """
        drive_id = self._drive_id(library_name)
        folder = (folder or "").strip("/")
        base = f"{GRAPH_BASE}/drives/{drive_id}/root"
        url = f"{base}:/{folder}:/children" if folder else f"{base}/children"
        data = self._request("GET", url, params={"$top": FOLDER_PAGE_SIZE},
                             timeout=timeout).json()
        return [
            self._file_entry(entry)
            for entry in data.get("value") or []
            if "folder" not in entry
        ]

    def get_folder_web_url(self, library_name: str, folder: str, timeout=None) -> str:
        """Resolve a folder through its configured drive, not its display name.

        A library named Documents may use Shared Documents in webUrl. Only
        metadata returned for this exact drive/path establishes that boundary.
        """
        self._require_configured()
        prefix = self._site_prefix()
        data = self._request("GET", self._item_url(library_name, folder), timeout=timeout).json()
        url = data.get("webUrl") or ""
        if "folder" not in data or not self._is_site_url(url, prefix):
            raise GraphAPIError("Không xác minh được thư mục tài liệu đã cấu hình.", status_code=502)
        return url

    def get_web_url(self, library_name: str, path: str) -> str:
        """Link xem tệp trực tiếp trên SharePoint/OneDrive (mở trình duyệt)."""
        return self.get_metadata(library_name, path).get("webUrl", "")


_default_client = None


def get_graph_client() -> GraphClient:
    """Trả về một GraphClient dùng chung (singleton nhẹ trong tiến trình)."""
    global _default_client
    if _default_client is None:
        _default_client = GraphClient()
    return _default_client

