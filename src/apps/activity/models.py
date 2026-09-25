from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseAuditModel


class Activity(BaseAuditModel):
    """Một Hoạt động dự án cụ thể (ví dụ: 'Tập huấn kỹ năng X tại xã Y').

    Thuộc về 1 Project (dự án/nhà tài trợ — dùng model Project có sẵn), và có
    thể liên kết tới 1 Công văn đi (apps.office.OutgoingDocument) khi kế
    hoạch tháng được phát hành — thời điểm này dùng để tự tính hạn báo cáo
    cho Task theo dõi hoạt động (xem apps.activity.services).

    Phạm vi module này CHỈ theo dõi tiến độ công việc + nhắc hạn, KHÔNG bao
    gồm ngân sách/quyết toán (theo đúng yêu cầu phạm vi ban đầu).
    """

    STATUS_CHOICES = [
        ("Planned", "Đã lên kế hoạch"),
        ("DispatchIssued", "Đã có Công văn"),
        ("InProgress", "Đang triển khai"),
        ("Completed", "Đã hoàn thành"),
        ("Cancelled", "Đã hủy"),
    ]

    activity_code = models.CharField("Mã hoạt động", max_length=50, unique=True, db_column="ActivityCode")
    activity_name = models.CharField("Tên hoạt động", max_length=300, db_column="ActivityName")

    project = models.ForeignKey(
        "project.Project", verbose_name="Dự án", on_delete=models.PROTECT,
        db_column="ProjectID", related_name="activities",
    )

    location = models.CharField("Địa điểm thực hiện", max_length=300, null=True, blank=True, db_column="Location")
    participants = models.CharField(
        "Thành phần tham gia", max_length=500, null=True, blank=True, db_column="Participants"
    )
    purpose = models.TextField("Mục đích", null=True, blank=True, db_column="Purpose")
    expected_output = models.TextField("Kết quả mong đợi", null=True, blank=True, db_column="ExpectedOutput")

    start_date = models.DateField("Ngày bắt đầu", db_column="StartDate")
    end_date = models.DateField("Ngày kết thúc", db_column="EndDate")

    lead_cbda = models.ForeignKey(
        "hrm.Employee", verbose_name="CBDA phụ trách chính", on_delete=models.PROTECT,
        db_column="LeadCbdaID", related_name="activities_as_lead_cbda",
    )
    coordinator = models.ForeignKey(
        "hrm.Employee", verbose_name="Điều phối viên (ĐPV)", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="CoordinatorID", related_name="activities_as_coordinator",
    )

    outgoing_document = models.ForeignKey(
        "document.OfficialDispatch", verbose_name="Công văn đi liên quan", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="OutgoingDocumentID", related_name="activities",
    )

    status = models.CharField("Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Planned", db_column="Status")

    class Meta:
        db_table = "tblActivity"
        verbose_name = "Hoạt động dự án"
        verbose_name_plural = "Hoạt động dự án"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.activity_code} - {self.activity_name}"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu."})
        if self.outgoing_document_id and self.outgoing_document.dispatch_type != "Outgoing":
            raise ValidationError({"outgoing_document": "Chỉ liên kết Công văn đi đã phát hành."})
        if (
            self.outgoing_document_id
            and not self.coordinator_id
            and not self.outgoing_document.signer_id
        ):
            raise ValidationError({
                "coordinator": "Chọn điều phối viên hoặc liên kết công văn có người ký để ghi nhận người giao Task."
            })
