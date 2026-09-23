from django.db import models
from apps.common.models import BaseAuditModel


class Project(BaseAuditModel):
    project_code = models.CharField("Mã dự án", max_length=50, unique=True, db_column="ProjectCode")
    project_name = models.CharField("Tên dự án", max_length=300, db_column="ProjectName")
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban phụ trách", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="DepartmentID", related_name="projects",
    )
    start_date = models.DateField("Ngày bắt đầu", null=True, blank=True, db_column="StartDate")
    end_date = models.DateField("Ngày kết thúc", null=True, blank=True, db_column="EndDate")
    is_active = models.BooleanField("Đang hoạt động", default=True, db_column="IsActive")

    class Meta:
        db_table = "tblProject"
        verbose_name = "Dự án"
        verbose_name_plural = "Dự án"

    def __str__(self):
        return f"{self.project_code} - {self.project_name}"