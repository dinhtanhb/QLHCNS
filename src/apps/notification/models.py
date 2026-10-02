from django.db import models
from apps.common.models import BaseAuditModel
from apps.common.email_draft import build_mailto_url


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


class NotificationEmailOutbox(BaseAuditModel):
    """Audit/outbox row for email drafts manually reviewed and sent in Outlook."""
    STATUS_CHOICES = [
        ("Draft", "Nháp — chưa gửi"),
        ("Pending", "Đang chờ gửi"),
        ("Sent", "Đã gửi"),
        ("Failed", "Gửi lỗi"),
    ]

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="email_outbox_entries",
        db_column="NotificationID",
    )
    recipient_email = models.EmailField("Email người nhận", max_length=254, db_column="RecipientEmail")
    subject = models.CharField("Tiêu đề thư", max_length=300, db_column="Subject")
    body_text = models.TextField("Nội dung thư", db_column="BodyText")
    status = models.CharField("Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Draft", db_column="Status")
    attempt_count = models.PositiveSmallIntegerField("Số lần thử", default=0, db_column="AttemptCount")
    last_attempt_at = models.DateTimeField("Lần thử gần nhất", null=True, blank=True, db_column="LastAttemptAt")
    error_message = models.CharField(
        "Lỗi đã làm sạch", max_length=500, null=True, blank=True, db_column="ErrorMessage"
    )
    idempotency_key = models.CharField("Khóa chống lặp", max_length=200, unique=True, db_column="IdempotencyKey")
    sent_by = models.ForeignKey(
        "security.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_column="SentByUserID",
    )
    sent_at = models.DateTimeField("Thời điểm xác nhận đã gửi", null=True, blank=True, db_column="SentAt")

    class Meta:
        db_table = "tblNotificationEmailOutbox"
        verbose_name = "Hàng chờ email Outlook"
        verbose_name_plural = "Hàng chờ email Outlook"
        indexes = [models.Index(fields=["status"], name="ix_notif_email_status")]

    @property
    def mailto_url(self):
        return build_mailto_url(self.recipient_email, self.subject, self.body_text)

    def __str__(self):
        return f"{self.recipient_email} — {self.subject}"
