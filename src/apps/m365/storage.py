"""
Storage backend cho Django FileField, lưu tệp thật lên SharePoint (hoặc một
drive OneDrive bất kỳ) qua Microsoft Graph API thay vì đĩa cục bộ.

Theo đúng kiến trúc trong docs/02_Solution_Architecture.md mục 13: SQL Server
chỉ lưu metadata (tên tệp, đường dẫn tương đối, kích thước...); tệp thật nằm
trên SharePoint/OneDrive.

Cách dùng trong models.py:

    from apps.m365.storage import get_storage

    attachment = models.FileField(
        upload_to=upload_to_dispatches,
        storage=get_storage("dispatches"),   # None nếu M365 chưa bật -> dùng đĩa cục bộ
    )

`get_storage(kind)` tra cứu M365_FOLDER_MAP trong settings để biết thư mục
nghiệp vụ trong thư viện M365_SHAREPOINT_LIBRARY. Nếu M365_STORAGE_ENABLED=False
(mặc định, khi chưa có đủ
Tenant ID/Client ID/Secret), get_storage trả về None và Django tự dùng
FileSystemStorage mặc định — hệ thống vẫn chạy bình thường trong lúc chờ IT
cấp thông tin Azure.
"""
from __future__ import annotations

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible

from apps.m365.graph_client import GraphAPIError, get_graph_client


@deconstructible
class SharePointStorage(Storage):
    """Storage Django đọc/ghi trực tiếp vào một thư viện tài liệu SharePoint.

    `library_name` phải khớp tên hiển thị của Document Library trên SharePoint
    (ví dụ 'Documents', 'CongVan', 'DonNghiPhep', 'TaiSanCongTy').
    """

    def __init__(self, library_name: str):
        self.library_name = library_name
        self.client = get_graph_client()

    # -- API bắt buộc của Django Storage --------------------------------
    def _save(self, name, content):
        data = content.read()
        self.client.upload_file(self.library_name, name, data)
        return name

    def _open(self, name, mode="rb"):
        data = self.client.download_file(self.library_name, name)
        return ContentFile(data, name=name)

    def exists(self, name):
        # If lookup fails, abort the save. False can overwrite an existing file;
        # True would make Django retry alternative names indefinitely.
        return self.client.exists(self.library_name, name)

    def delete(self, name):
        self.client.delete_file(self.library_name, name)

    def size(self, name):
        meta = self.client.get_metadata(self.library_name, name)
        return meta.get("size", 0)

    def url(self, name):
        try:
            return self.client.get_web_url(self.library_name, name)
        except GraphAPIError:
            return ""

    def get_accessed_time(self, name):  # pragma: no cover - Graph không cung cấp
        raise NotImplementedError("SharePoint không cung cấp thời gian truy cập gần nhất.")


def m365_enabled() -> bool:
    return bool(getattr(settings, "M365_STORAGE_ENABLED", False))


def get_storage(kind: str):
    """Return a stable storage adapter; choose the backend per file operation."""
    return ConfiguredStorage(kind)


@deconstructible
class ConfiguredStorage(Storage):
    """Migration-stable wrapper around local and SharePoint storage."""

    def __init__(self, kind: str):
        self.kind = kind

    def _remote_name(self, name: str) -> str:
        name = name.lstrip("/")
        upload_prefix = getattr(settings, "M365_UPLOAD_PREFIX_MAP", {}).get(self.kind, "")
        if upload_prefix and name.startswith(upload_prefix + "/"):
            name = name[len(upload_prefix) + 1:]

        folder = getattr(settings, "M365_FOLDER_MAP", {}).get(self.kind, "")
        if not folder:
            return name
        folder = folder.strip("/")
        if name == folder or name.startswith(folder + "/"):
            return name
        return f"{folder}/{name}"

    @property
    def backend(self):
        if not m365_enabled():
            return FileSystemStorage()

        library_name = getattr(settings, "M365_SHAREPOINT_LIBRARY", "Documents")
        if not library_name:
            raise ValueError(
                "No SharePoint document library configured in "
                "settings.M365_SHAREPOINT_LIBRARY."
            )
        return SharePointStorage(library_name)

    def _open(self, name, mode="rb"):
        return self.backend._open(self._remote_name(name), mode)

    def _save(self, name, content):
        remote_name = self._remote_name(name)
        self.backend._save(remote_name, content)
        return remote_name

    def delete(self, name):
        return self.backend.delete(self._remote_name(name))

    def exists(self, name):
        return self.backend.exists(self._remote_name(name))

    def listdir(self, path):
        return self.backend.listdir(path)

    def size(self, name):
        return self.backend.size(self._remote_name(name))

    def url(self, name):
        return self.backend.url(self._remote_name(name))

    def path(self, name):
        return self.backend.path(name)

    def get_accessed_time(self, name):
        return self.backend.get_accessed_time(name)

    def get_created_time(self, name):
        return self.backend.get_created_time(name)

    def get_modified_time(self, name):
        return self.backend.get_modified_time(name)


# Keep this storage import stable for Django migrations. The backend remains
# selected dynamically (local media or SharePoint) when a file is accessed.
activity_reports_storage = get_storage("activity_reports")
