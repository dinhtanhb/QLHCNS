from django.db import models
from apps.common.models import BaseAuditModel


class Notification(BaseAuditModel):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Người nhận", on_delete=models.CASCADE,
        db_column="EmployeeID", related_name="notifications",
    )
    notification_type = models.CharField("Loại thông báo", max_length=50, db_column="NotificationType")
    title = models.CharField("Tiêu đề", max_length=300, db_column="Title")
    message = models.CharField("Nội dung", max_length=1000, db_column="Message")
    link = models.CharField("Đường dẫn liên quan", max_length=300, null=True, blank=True)
    is_read = models.BooleanField("Đã đọc", default=False, db_column="IsRead")

    class Meta:
        db_table = "tblNotification"
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"
        ordering = ["-created_date"]

    def __str__(self):
        return f"{self.employee} - {self.title}"