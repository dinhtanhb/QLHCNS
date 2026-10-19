from django.db import models
from apps.common.models import BaseAuditModel


class SearchQueryLog(BaseAuditModel):
    """Nhật ký truy vấn chatbot: không lưu nội dung/kết quả tài liệu."""

    user = models.ForeignKey(
        "security.User", on_delete=models.CASCADE,
        related_name="assistant_search_logs", db_column="UserID",
    )
    question = models.CharField("Câu hỏi", max_length=500, db_column="Question")
    parsed_filters = models.JSONField("Bộ lọc đã parse", default=dict, db_column="ParsedFilters")
    result_count = models.PositiveIntegerField("Số kết quả", default=0, db_column="ResultCount")
    sources = models.CharField("Nguồn", max_length=30, db_column="Sources")
    took_ms = models.PositiveIntegerField("Thời gian (ms)", default=0, db_column="TookMs")
    error_note = models.CharField("Ghi chú lỗi", max_length=100, null=True, blank=True, db_column="ErrorNote")

    class Meta:
        db_table = "tblAssistantSearchLog"
        # "-id" để thứ tự ổn định khi nhiều log cùng một nhịp đồng hồ.
        ordering = ["-created_date", "-id"]
        verbose_name = "Nhật ký truy vấn trợ lý"
        verbose_name_plural = "Nhật ký truy vấn trợ lý"
