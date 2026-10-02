from decimal import Decimal as _Decimal
from datetime import date as _date

from django.core.exceptions import ValidationError
from django.db import models
from apps.common.models import BaseAuditModel
from apps.common.uploads import upload_to_leave_requests, validate_upload
from apps.m365.storage import get_storage

# Mã loại nghỉ có kiểm soát hạn mức
ANNUAL_LEAVE_CODE = "AL"          # Phép năm
COMPENSATORY_LEAVE_CODE = "CO"    # Nghỉ bù (do làm Thứ 7/Chủ nhật/ngày lễ)


def leave_days_in_period(from_date, to_date, *, holidays=None):
    """Working days in an inclusive leave-date range, excluding weekends and holidays."""
    from apps.attendance.services import standard_working_days
    return standard_working_days(from_date, to_date, holidays=holidays)


def leave_days_in_year(leave_request, year, *, holidays=None):
    start = max(leave_request.from_date, _date(year, 1, 1))
    end = min(leave_request.to_date, _date(year, 12, 31))
    if end < start:
        return _Decimal("0")
    return leave_days_in_period(start, end, holidays=holidays)


def leave_days_in_month(leave_request, year, month):
    from calendar import monthrange
    start = max(leave_request.from_date, _date(year, month, 1))
    end = min(leave_request.to_date, _date(year, month, monthrange(year, month)[1]))
    if end < start:
        return _Decimal("0")
    return leave_days_in_period(start, end)


class LeaveType(BaseAuditModel):
    leave_type_code = models.CharField(max_length=50, unique=True, db_column="LeaveTypeCode")
    leave_type_name = models.CharField(max_length=100, db_column="LeaveTypeName")
    is_paid = models.BooleanField(default=True, db_column="IsPaid")

    class Meta:
        db_table = "tblLeaveType"
        verbose_name = "Loại nghỉ phép"
        verbose_name_plural = "Loại nghỉ phép"

    def __str__(self):
        return self.leave_type_name


class LeaveRequest(BaseAuditModel):
    STATUS_CHOICES = [
        ("Pending", "Chờ duyệt"),
        ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"),
        ("Cancelled", "Đã hủy"),
    ]

    employee = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT,
        db_column="EmployeeID", related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT,
        db_column="LeaveTypeID", related_name="leave_requests",
    )
    from_date = models.DateField(db_column="FromDate")
    to_date = models.DateField(db_column="ToDate")
    total_days = models.DecimalField(max_digits=4, decimal_places=1, default=0, db_column="TotalDays")
    reason = models.CharField(max_length=500, null=True, blank=True, db_column="Reason")
    attachment = models.FileField(
        "Tệp đính kèm (đơn xin nghỉ, giấy tờ liên quan)",
        upload_to=upload_to_leave_requests,
        validators=[validate_upload], null=True, blank=True,
        storage=get_storage("leave"),
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    class Meta:
        db_table = "tblLeaveRequest"
        verbose_name = "Đơn xin nghỉ phép"
        verbose_name_plural = "Đơn xin nghỉ phép"

    def compute_total_days(self):
        """Số ngày nghỉ thực tế = số ngày công chuẩn (T2–T6, đã trừ ngày lễ)."""
        from apps.attendance.services import standard_working_days

        return standard_working_days(self.from_date, self.to_date)

    def clean(self):
        if not (self.from_date and self.to_date):
            return

        if self.to_date < self.from_date:
            raise ValidationError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.")

        self.total_days = self.compute_total_days()
        if self.total_days <= 0:
            raise ValidationError(
                "Khoảng ngày đã chọn không có ngày công chuẩn nào "
                "(toàn Thứ 7, Chủ nhật hoặc ngày lễ) — không cần xin nghỉ phép."
            )

        self._validate_no_overlap()
        self._validate_quota()

    def _validate_no_overlap(self):
        """Không cho gửi hai đơn trùng ngày."""
        if not self.employee_id:
            return
        overlapping = LeaveRequest.objects.filter(
            employee_id=self.employee_id,
            status__in=["Pending", "Approved"],
            from_date__lte=self.to_date,
            to_date__gte=self.from_date,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        existing = overlapping.order_by("from_date").first()
        if existing:
            raise ValidationError(
                f"Anh/chị đã có đơn nghỉ trùng ngày: {existing.leave_type} "
                f"từ {existing.from_date:%d/%m/%Y} đến {existing.to_date:%d/%m/%Y} "
                f"({existing.get_status_display()})."
            )

    def _validate_quota(self):
        """Không cho nghỉ vượt quỹ phép năm hoặc quỹ nghỉ bù."""
        if not (self.employee_id and self.leave_type_id):
            return
        if self.status not in ("Pending", "Approved"):
            return

        code = (self.leave_type.leave_type_code or "").strip().upper()
        if code not in (ANNUAL_LEAVE_CODE, COMPENSATORY_LEAVE_CODE):
            return

        old = LeaveRequest.objects.filter(pk=self.pk).first() if self.pk else None
        for year in range(self.from_date.year, self.to_date.year + 1):
            requested_days = leave_days_in_year(self, year)
            if requested_days <= 0:
                continue
            balance = LeaveBalance.objects.filter(employee_id=self.employee_id, year=year).first()
            has_record = balance is not None
            if balance is None:
                balance = LeaveBalance(employee_id=self.employee_id, year=year)

            if code == ANNUAL_LEAVE_CODE:
                available = balance.available_annual_days
                label = "phép năm"
                if not has_record:
                    raise ValidationError(
                        f"Chưa khai báo hạn mức phép năm {year} cho anh/chị. "
                        "Vui lòng liên hệ bộ phận Nhân sự để được cấp số ngày phép."
                    )
            else:
                available = balance.compensatory_remaining
                label = "nghỉ bù"

            # Khi sửa đơn, trả lại phần ngày của từng năm trước khi kiểm tra lại.
            if old and old.status in ("Pending", "Approved") and old.leave_type_id:
                old_code = (old.leave_type.leave_type_code or "").strip().upper()
                if old_code == code:
                    available += leave_days_in_year(old, year)

            if requested_days > available:
                raise ValidationError(
                    f"Không đủ quỹ {label} năm {year}: cần {requested_days} ngày "
                    f"nhưng chỉ còn {available} ngày."
                )

    def save(self, *args, **kwargs):
        if self.from_date and self.to_date and not self.total_days:
            self.total_days = self.compute_total_days()
        super().save(*args, **kwargs)


class LeaveApproval(BaseAuditModel):
    DECISION_CHOICES = [("Approved", "Duyệt"), ("Rejected", "Từ chối")]

    leave_request = models.ForeignKey(
        LeaveRequest, on_delete=models.CASCADE,
        db_column="LeaveRequestID", related_name="approvals",
    )
    approver = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT,
        db_column="ApproverID", related_name="leave_approvals_made",
    )
    approval_level = models.SmallIntegerField(default=1, db_column="ApprovalLevel")
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, db_column="Decision")
    decision_date = models.DateTimeField(auto_now_add=True, db_column="DecisionDate")

    class Meta:
        db_table = "tblLeaveApproval"
        verbose_name = "Lịch sử duyệt nghỉ phép"
        verbose_name_plural = "Lịch sử duyệt nghỉ phép"

    def __str__(self):
        return f"{self.leave_request} - {self.get_decision_display()} bởi {self.approver}"

from decimal import Decimal
from django.db.models import Sum


class LeaveBalance(BaseAuditModel):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.CASCADE,
        db_column="EmployeeID", related_name="leave_balances",
    )
    year = models.SmallIntegerField("Năm", db_column="Year")
    allocated_days = models.DecimalField(
        "Số ngày phép được cấp năm nay", max_digits=4, decimal_places=1, default=0, db_column="AllocatedDays"
    )
    carried_over_days = models.DecimalField(
        "Ngày phép năm trước chuyển qua", max_digits=4, decimal_places=1, default=0, db_column="CarriedOverDays"
    )

    class Meta:
        db_table = "tblLeaveBalance"
        verbose_name = "Hạn mức phép năm"
        verbose_name_plural = "Hạn mức phép năm"
        constraints = [models.UniqueConstraint(fields=["employee", "year"], name="UX_LeaveBalance_Emp_Year")]

    # ---------- Phép năm ----------
    def _days_by_status(self, leave_type_code, statuses):
        requests = LeaveRequest.objects.filter(
            employee=self.employee,
            status__in=statuses,
            leave_type__leave_type_code__iexact=leave_type_code,
            from_date__lte=_date(self.year, 12, 31),
            to_date__gte=_date(self.year, 1, 1),
        )
        return sum(
            (leave_days_in_year(request, self.year) for request in requests),
            Decimal("0"),
        )

    @property
    def used_days(self):
        """Số ngày phép năm đã được duyệt."""
        return self._days_by_status(ANNUAL_LEAVE_CODE, ["Approved"])

    @property
    def pending_days(self):
        """Số ngày phép năm đang chờ duyệt (đã giữ chỗ trong quỹ)."""
        return self._days_by_status(ANNUAL_LEAVE_CODE, ["Pending"])

    @property
    def remaining_days(self):
        return self.allocated_days + self.carried_over_days - self.used_days

    @property
    def available_annual_days(self):
        """Số ngày phép năm còn có thể xin, đã trừ cả đơn đang chờ duyệt."""
        return self.remaining_days - self.pending_days

    # ---------- Nghỉ bù ----------
    @property
    def compensatory_earned(self):
        """Ngày nghỉ bù tích lũy được do làm Thứ 7/Chủ nhật/ngày lễ."""
        from apps.attendance.services import compensatory_days_earned

        return compensatory_days_earned(self.employee, self.year)

    @property
    def compensatory_used(self):
        return self._days_by_status(COMPENSATORY_LEAVE_CODE, ["Approved"])

    @property
    def compensatory_pending(self):
        return self._days_by_status(COMPENSATORY_LEAVE_CODE, ["Pending"])

    @property
    def compensatory_remaining(self):
        return self.compensatory_earned - self.compensatory_used - self.compensatory_pending

    def __str__(self):
        return f"{self.employee} - Phép {self.year}"
