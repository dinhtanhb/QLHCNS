"""Chuẩn hóa tên tệp tải lên và kiểm tra tệp hợp lệ.

Vấn đề trước đây: tên tệp tiếng Việt được lưu nguyên xuống đĩa nên bị hỏng dấu,
sinh ra những tên như "I3b_C⌠ng_van_h?_tr?...pdf". Ngoài ra hệ thống nhận mọi
loại tệp, kể cả .exe và .html.

Cách xử lý: bỏ dấu tiếng Việt, chuyển về chữ thường không dấu, thêm một mã ngẫu
nhiên ngắn để không ghi đè tệp trùng tên, đồng thời chỉ cho phép các định dạng
tài liệu thông dụng và giới hạn dung lượng.
"""
import os
import re
import unicodedata
import uuid
from datetime import date

from django.core.exceptions import ValidationError

# Định dạng tệp được phép tải lên
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".txt", ".csv", ".zip", ".rar", ".7z",
}

# Dung lượng tối đa cho một tệp (MB)
MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Định dạng riêng cho thư viện ảnh/video công ty (rộng hơn ALLOWED_EXTENSIONS
# vì cần nhận thêm định dạng video). Dùng cho apps.m365.models.CompanyMedia.
ALLOWED_MEDIA_EXTENSIONS = ALLOWED_EXTENSIONS | {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_MEDIA_UPLOAD_SIZE_MB = 500
MAX_MEDIA_UPLOAD_SIZE = MAX_MEDIA_UPLOAD_SIZE_MB * 1024 * 1024


def slugify_filename(filename, max_length=80):
    """Bỏ dấu tiếng Việt và ký tự đặc biệt, giữ lại phần mở rộng."""
    base, ext = os.path.splitext(filename or "")
    ext = ext.lower()

    # đ/Đ không tự bỏ dấu được nên phải thay trước
    base = base.replace("đ", "d").replace("Đ", "D")
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^\w\s-]", "", base).strip().lower()
    base = re.sub(r"[\s_-]+", "-", base).strip("-")

    if not base:
        base = "tep-dinh-kem"
    return base[:max_length], ext


def build_upload_path(folder, filename):
    """Đường dẫn lưu tệp: <folder>/<năm>/<tháng>/<ten-da-chuan-hoa>-<mã>.<ext>"""
    base, ext = slugify_filename(filename)
    today = date.today()
    unique = uuid.uuid4().hex[:8]
    return f"{folder}/{today:%Y}/{today:%m}/{base}-{unique}{ext}"


# Django yêu cầu upload_to phải là hàm đặt ở cấp module thì mới ghi được vào
# migration, nên mỗi thư mục có một hàm riêng thay vì dùng hàm sinh hàm.
def upload_to_documents(instance, filename):
    return build_upload_path("documents", filename)


def upload_to_dispatches(instance, filename):
    return build_upload_path("dispatches", filename)


def upload_to_incoming_docs(instance, filename):
    return build_upload_path("incoming_docs", filename)


def upload_to_outgoing_docs(instance, filename):
    return build_upload_path("outgoing_docs", filename)


def upload_to_candidate_cv(instance, filename):
    return build_upload_path("candidates/cv", filename)


def upload_to_leave_requests(instance, filename):
    return build_upload_path("leave-requests", filename)


def upload_to_company_media(instance, filename):
    return build_upload_path("company-media", filename)

def upload_to_activity_reports(instance, filename):
    return build_upload_path("activity-reports", filename)

def validate_upload(uploaded_file):
    """Kiểm tra định dạng và dung lượng tệp. Dùng làm validator cho FileField."""
    if not uploaded_file:
        return

    name = getattr(uploaded_file, "name", "") or ""
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS))
        raise ValidationError(
            f'Định dạng tệp "{ext or "không xác định"}" không được phép. '
            f"Chỉ nhận các định dạng: {allowed}."
        )

    size = getattr(uploaded_file, "size", None)
    if size and size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            f"Tệp nặng {size / 1024 / 1024:.1f} MB, vượt quá giới hạn {MAX_UPLOAD_SIZE_MB} MB."
        )


def validate_media_upload(uploaded_file):
    """Giống validate_upload nhưng cho phép thêm định dạng video và dung
    lượng lớn hơn — dùng cho thư viện ảnh/video công ty (CompanyMedia)."""
    if not uploaded_file:
        return

    name = getattr(uploaded_file, "name", "") or ""
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        allowed = ", ".join(sorted(e.lstrip(".") for e in ALLOWED_MEDIA_EXTENSIONS))
        raise ValidationError(
            f'Định dạng tệp "{ext or "không xác định"}" không được phép. '
            f"Chỉ nhận các định dạng: {allowed}."
        )

    size = getattr(uploaded_file, "size", None)
    if size and size > MAX_MEDIA_UPLOAD_SIZE:
        raise ValidationError(
            f"Tệp nặng {size / 1024 / 1024:.1f} MB, vượt quá giới hạn "
            f"{MAX_MEDIA_UPLOAD_SIZE_MB} MB."
        )
