from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import BaseAuditModel


class ProcurementRequest(BaseAuditModel):
    STATUS_CHOICES = [
        ("Pending", "Chờ duyệt"),
        ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"),
        ("Purchased", "Đã mua"),
    ]

    request_no = models.CharField("Số đề nghị", max_length=50, unique=True, db_column="RequestNo")
    requested_by = models.ForeignKey(
        "hrm.Employee", verbose_name="Người đề nghị", on_delete=models.PROTECT,
        db_column="RequestedBy", related_name="procurement_requests",
    )
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", on_delete=models.PROTECT,
        db_column="DepartmentID", related_name="procurement_requests",
    )
    request_date = models.DateField("Ngày đề nghị", db_column="RequestDate")
    reason = models.CharField("Lý do", max_length=1000, null=True, blank=True, db_column="Reason")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    class Meta:
        db_table = "tblProcurementRequest"
        verbose_name = "Đề nghị mua sắm"
        verbose_name_plural = "Đề nghị mua sắm"

    @property
    def total_estimated_cost(self):
        return sum((item.estimated_cost or 0) * item.quantity for item in self.items.all())

    def __str__(self):
        return f"{self.request_no} - {self.department}"


class ProcurementItem(BaseAuditModel):
    procurement_request = models.ForeignKey(
        ProcurementRequest, on_delete=models.CASCADE, db_column="ProcurementRequestID", related_name="items"
    )
    item_name = models.CharField("Tên hàng hóa/dịch vụ", max_length=300, db_column="ItemName")
    quantity = models.SmallIntegerField("Số lượng", default=1, db_column="Quantity", validators=[MinValueValidator(1)])
    estimated_cost = models.DecimalField(
        "Đơn giá dự kiến", max_digits=18, decimal_places=2, null=True, blank=True,
        db_column="EstimatedCost", validators=[MinValueValidator(0)],
    )

    class Meta:
        db_table = "tblProcurementItem"
        verbose_name = "Hạng mục mua sắm"
        verbose_name_plural = "Hạng mục mua sắm"
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name="procurement_item_quantity_positive"),
            models.CheckConstraint(
                condition=models.Q(estimated_cost__gte=0) | models.Q(estimated_cost__isnull=True),
                name="procurement_item_cost_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"


class ProcurementApproval(BaseAuditModel):
    DECISION_CHOICES = [("Approved", "Duyệt"), ("Rejected", "Từ chối")]

    procurement_request = models.ForeignKey(
        ProcurementRequest, on_delete=models.CASCADE, db_column="ProcurementRequestID", related_name="approvals"
    )
    approver = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT, db_column="ApproverID", related_name="procurement_approvals"
    )
    approval_level = models.SmallIntegerField("Cấp duyệt", default=1, db_column="ApprovalLevel")
    decision = models.CharField("Quyết định", max_length=20, choices=DECISION_CHOICES, db_column="Decision")
    decision_date = models.DateTimeField("Thời gian", auto_now_add=True, db_column="DecisionDate")

    class Meta:
        db_table = "tblProcurementApproval"
        verbose_name = "Lịch sử duyệt mua sắm"
        verbose_name_plural = "Lịch sử duyệt mua sắm"

    def __str__(self):
        return f"{self.procurement_request} - {self.get_decision_display()}"
