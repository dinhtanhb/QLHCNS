from django.conf import settings
from django.db import models
from apps.common.models import BaseAuditModel


class ChecklistTemplate(BaseAuditModel):
    TEMPLATE_TYPE_CHOICES = [("Onboarding", "Tiếp nhận"), ("Offboarding", "Nghỉ việc")]

    template_code = models.CharField(max_length=50, unique=True, db_column="TemplateCode")
    template_name = models.CharField(max_length=200, db_column="TemplateName")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, db_column="TemplateType")
    is_active = models.BooleanField(default=True, db_column="IsActive")

    class Meta:
        db_table = "tblChecklistTemplate"
        ordering = ["template_type", "template_name"]

    def __str__(self):
        return f"{self.template_name} ({self.get_template_type_display()})"


class ChecklistTemplateItem(BaseAuditModel):
    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name="items", db_column="TemplateID"
    )
    sequence = models.PositiveSmallIntegerField(db_column="Sequence")
    item_name = models.CharField(max_length=300, db_column="ItemName")
    responsible_role_code = models.CharField(max_length=30, db_column="ResponsibleRoleCode")
    due_offset_days = models.SmallIntegerField(default=0, db_column="DueOffsetDays")
    requires_asset_return = models.BooleanField(default=False, db_column="RequiresAssetReturn")

    class Meta:
        db_table = "tblChecklistTemplateItem"
        ordering = ["sequence", "id"]
        constraints = [models.UniqueConstraint(fields=["template", "sequence"], name="uq_check_tpl_item_seq")]

    def __str__(self):
        return self.item_name


class EmployeeLifecycleCase(BaseAuditModel):
    CASE_TYPE_CHOICES = [("Onboarding", "Tiếp nhận"), ("Offboarding", "Nghỉ việc")]
    STATUS_CHOICES = [("Open", "Đang xử lý"), ("Completed", "Hoàn tất"), ("Cancelled", "Đã hủy")]

    employee = models.ForeignKey(
        "hrm.Employee", on_delete=models.CASCADE, related_name="lifecycle_cases", db_column="EmployeeID"
    )
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT, db_column="TemplateID")
    case_type = models.CharField(max_length=20, choices=CASE_TYPE_CHOICES, db_column="CaseType")
    effective_date = models.DateField(db_column="EffectiveDate")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open", db_column="Status")
    triggering_event_ref = models.CharField(max_length=150, unique=True, db_column="TriggeringEventRef")

    class Meta:
        db_table = "tblEmployeeLifecycleCase"
        ordering = ["-effective_date", "-created_date"]

    def __str__(self):
        return f"{self.employee} — {self.get_case_type_display()} {self.effective_date}"


class LifecycleChecklistItem(BaseAuditModel):
    STATUS_CHOICES = [("Pending", "Chưa làm"), ("Done", "Hoàn tất"), ("Skipped", "Bỏ qua")]

    case = models.ForeignKey(EmployeeLifecycleCase, on_delete=models.CASCADE, related_name="items", db_column="CaseID")
    template_item = models.ForeignKey(ChecklistTemplateItem, on_delete=models.PROTECT, db_column="TemplateItemID")
    item_name = models.CharField(max_length=300, db_column="ItemName")
    responsible_role_code = models.CharField(max_length=30, db_column="ResponsibleRoleCode")
    requires_asset_return = models.BooleanField(default=False, db_column="RequiresAssetReturn")
    assigned_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lifecycle_checklist_items", db_column="AssignedToUserID",
    )
    due_date = models.DateField(null=True, blank=True, db_column="DueDate")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending", db_column="Status")
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="completed_lifecycle_items", db_column="CompletedByUserID",
    )
    completed_at = models.DateTimeField(null=True, blank=True, db_column="CompletedAt")
    skip_reason = models.CharField(max_length=500, blank=True, db_column="SkipReason")
    last_reminded_on = models.DateField(null=True, blank=True, db_column="LastRemindedOn")
    asset_allocation = models.ForeignKey(
        "asset.AssetAllocation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="lifecycle_checklist_items", db_column="AssetAllocationID",
    )

    class Meta:
        db_table = "tblLifecycleChecklistItem"
        ordering = ["template_item__sequence", "id"]
        indexes = [models.Index(fields=["status", "due_date"], name="ix_lifecycle_due_status")]

    def __str__(self):
        return self.item_name
