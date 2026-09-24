from django.db import models

from apps.common.models import BaseAuditModel
from apps.common.uploads import upload_to_company_media, validate_media_upload
from apps.m365.storage import get_storage


class CompanyMedia(BaseAuditModel):
    """Thư viện ảnh / video chung của công ty (sự kiện, đào tạo, quảng bá...).

    Tệp thật lưu trên SharePoint/OneDrive qua SharePointStorage; bảng này chỉ
    giữ metadata trong SQL Server, đúng kiến trúc mục 13 của
    docs/02_Solution_Architecture.md.
    """

    MEDIA_TYPE_CHOICES = [
        ("Image", "Hình ảnh"),
        ("Video", "Video"),
    ]

    title = models.CharField("Tiêu đề", max_length=300, db_column="Title")
    description = models.CharField(
        "Mô tả", max_length=1000, null=True, blank=True, db_column="Description"
    )
    media_type = models.CharField(
        "Loại tệp", max_length=10, choices=MEDIA_TYPE_CHOICES, db_column="MediaType"
    )
    category = models.CharField(
        "Chủ đề / Sự kiện", max_length=200, null=True, blank=True, db_column="Category",
        help_text="Ví dụ: Sự kiện công ty, Đào tạo, Team building, Quảng bá...",
    )
    file = models.FileField(
        "Tệp ảnh/video", upload_to=upload_to_company_media,
        validators=[validate_media_upload],
        storage=get_storage("assets"),
    )
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban liên quan", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="DepartmentID", related_name="company_media",
    )

    class Meta:
        db_table = "tblCompanyMedia"
        verbose_name = "Ảnh / Video công ty"
        verbose_name_plural = "Thư viện Ảnh / Video công ty"
        ordering = ["-created_date"]

    def __str__(self):
        return f"[{self.get_media_type_display()}] {self.title}"