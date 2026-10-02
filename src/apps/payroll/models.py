from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from dataclasses import dataclass
import hashlib
import copy
from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db import models
from apps.common.models import BaseAuditModel


# ============================================================
# 1. LƯƠNG CƠ BẢN CỦA NHÂN VIÊN
# ============================================================

@dataclass(frozen=True)
class PayrollConfiguration:
    period_date: object
    insurance: object
    deduction: object
    tax_brackets: tuple


def _decimal_amount(value):
    try:
        amount = Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount if amount.is_finite() else None


class EmployeeSalary(BaseAuditModel):
    STATUS_CHOICES = [("Active", "Đang áp dụng"), ("Ended", "Đã kết thúc")]

    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.PROTECT,
        db_column="EmployeeID", related_name="salaries",
    )
    current_basic_salary = models.DecimalField(
        "Lương cơ bản", max_digits=18, decimal_places=2, db_column="CurrentBasicSalary"
    )
    effective_date = models.DateField("Ngày hiệu lực", db_column="EffectiveDate")
    end_date = models.DateField("Ngày kết thúc", null=True, blank=True, db_column="EndDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Active", db_column="Status")

    class Meta:
        db_table = "tblEmployeeSalary"
        verbose_name = "Lương nhân viên"
        verbose_name_plural = "Lương nhân viên"

    def __str__(self):
        return f"{self.employee} - {self.current_basic_salary:,.0f}đ (từ {self.effective_date})"

    def clean(self):
        salary = _decimal_amount(self.current_basic_salary)
        if salary is not None and salary < 0:
            raise ValidationError({"current_basic_salary": "Lương cơ bản không được âm."})
        if self.end_date and self.effective_date and self.end_date < self.effective_date:
            raise ValidationError("Ngày kết thúc phải sau hoặc bằng ngày hiệu lực.")
        self._validate_no_overlap()

    def _validate_no_overlap(self):
        if not (self.employee_id and self.effective_date):
            return
        overlapping = EmployeeSalary.objects.filter(employee_id=self.employee_id).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=self.effective_date)
        )
        if self.end_date:
            overlapping = overlapping.filter(effective_date__lte=self.end_date)
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        existing = overlapping.order_by("effective_date").first()
        if existing:
            to_text = f"đến {existing.end_date:%d/%m/%Y}" if existing.end_date else "chưa kết thúc"
            raise ValidationError(
                f"Nhân viên đã có mức lương khác áp dụng trùng thời gian (từ "
                f"{existing.effective_date:%d/%m/%Y}, {to_text}) — không được khai 2 mức lương "
                f"chồng lấn hiệu lực cho cùng 1 nhân viên."
            )


# ============================================================
# 2. MASTER DATA: TỶ LỆ BẢO HIỂM / THUẾ (theo 06A_Payroll_Statutory_Rate_Master_Data)
#    Có hiệu lực theo thời gian — không hardcode trong code.
# ============================================================

class InsuranceRateConfig(BaseAuditModel):
    effective_from = models.DateField("Hiệu lực từ", db_column="EffectiveFrom")
    effective_to = models.DateField("Hiệu lực đến", null=True, blank=True, db_column="EffectiveTo")
    employee_social_insurance_rate = models.DecimalField(
        "NLĐ - BHXH (%)", max_digits=5, decimal_places=2, db_column="EmployeeSocialInsuranceRate"
    )
    employee_health_insurance_rate = models.DecimalField(
        "NLĐ - BHYT (%)", max_digits=5, decimal_places=2, db_column="EmployeeHealthInsuranceRate"
    )
    employee_unemployment_insurance_rate = models.DecimalField(
        "NLĐ - BHTN (%)", max_digits=5, decimal_places=2, db_column="EmployeeUnemploymentInsuranceRate"
    )
    employer_social_insurance_rate = models.DecimalField(
        "DN - BHXH (%)", max_digits=5, decimal_places=2, db_column="EmployerSocialInsuranceRate"
    )
    employer_health_insurance_rate = models.DecimalField(
        "DN - BHYT (%)", max_digits=5, decimal_places=2, db_column="EmployerHealthInsuranceRate"
    )
    employer_unemployment_insurance_rate = models.DecimalField(
        "DN - BHTN (%)", max_digits=5, decimal_places=2, db_column="EmployerUnemploymentInsuranceRate"
    )
    base_salary_reference = models.DecimalField(
        "Lương cơ sở (đ/tháng)", max_digits=18, decimal_places=2, default=Decimal("2340000"),
        db_column="BaseSalaryReference",
        help_text="Dùng để tính trần đóng BHXH/BHYT = 20 lần mức này.",
    )
    regional_minimum_wage = models.DecimalField(
        "Lương tối thiểu vùng (đ/tháng)", max_digits=18, decimal_places=2, default=Decimal("4960000"),
        db_column="RegionalMinimumWage",
        help_text="Dùng để tính trần đóng BHTN = 20 lần mức này.",
    )
    legal_reference = models.CharField(
        "Căn cứ pháp lý", max_length=300, null=True, blank=True, db_column="LegalReference"
    )

    class Meta:
        db_table = "tblInsuranceRateConfig"
        verbose_name = "Cấu hình tỷ lệ Bảo hiểm"
        verbose_name_plural = "Cấu hình tỷ lệ Bảo hiểm"

    def __str__(self):
        return f"Tỷ lệ BH từ {self.effective_from}"

    @property
    def total_employee_rate(self):
        return (
            self.employee_social_insurance_rate
            + self.employee_health_insurance_rate
            + self.employee_unemployment_insurance_rate
        )

    @property
    def social_health_cap(self):
        """Trần tiền lương đóng BHXH + BHYT = 20 x lương cơ sở."""
        return (self.base_salary_reference or Decimal("0")) * 20

    @property
    def unemployment_cap(self):
        """Trần tiền lương đóng BHTN = 20 x lương tối thiểu vùng."""
        return (self.regional_minimum_wage or Decimal("0")) * 20


class PersonalIncomeTaxBracket(BaseAuditModel):
    effective_from = models.DateField("Hiệu lực từ", db_column="EffectiveFrom")
    effective_to = models.DateField("Hiệu lực đến", null=True, blank=True, db_column="EffectiveTo")
    bracket_no = models.SmallIntegerField("Bậc thuế", db_column="BracketNo")
    income_from_monthly = models.DecimalField(
        "Thu nhập từ (đ/tháng)", max_digits=18, decimal_places=2, db_column="IncomeFromMonthly"
    )
    income_to_monthly = models.DecimalField(
        "Thu nhập đến (đ/tháng)", max_digits=18, decimal_places=2, null=True, blank=True, db_column="IncomeToMonthly"
    )
    tax_rate = models.DecimalField("Thuế suất (%)", max_digits=5, decimal_places=2, db_column="TaxRate")

    class Meta:
        db_table = "tblPersonalIncomeTaxBracket"
        verbose_name = "Bậc thuế TNCN"
        verbose_name_plural = "Bậc thuế TNCN"
        ordering = ["effective_from", "bracket_no"]

    def __str__(self):
        to_text = f"{self.income_to_monthly:,.0f}" if self.income_to_monthly else "trở lên"
        return f"Bậc {self.bracket_no}: {self.income_from_monthly:,.0f} - {to_text} ({self.tax_rate}%)"


class TaxDeductionConfig(BaseAuditModel):
    effective_from = models.DateField("Hiệu lực từ", db_column="EffectiveFrom")
    effective_to = models.DateField("Hiệu lực đến", null=True, blank=True, db_column="EffectiveTo")
    self_deduction_monthly = models.DecimalField(
        "Giảm trừ bản thân (đ/tháng)", max_digits=18, decimal_places=2, db_column="SelfDeductionMonthly"
    )
    dependent_deduction_monthly = models.DecimalField(
        "Giảm trừ mỗi người phụ thuộc (đ/tháng)", max_digits=18, decimal_places=2,
        db_column="DependentDeductionMonthly",
    )

    class Meta:
        db_table = "tblTaxDeductionConfig"
        verbose_name = "Cấu hình giảm trừ thuế TNCN"
        verbose_name_plural = "Cấu hình giảm trừ thuế TNCN"

    def __str__(self):
        return f"Giảm trừ từ {self.effective_from}"


class EmployeeDependent(BaseAuditModel):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.CASCADE,
        db_column="EmployeeID", related_name="dependents",
    )
    full_name = models.CharField("Họ tên người phụ thuộc", max_length=200, db_column="FullName")
    relationship = models.CharField("Quan hệ", max_length=50, db_column="Relationship")
    registered_from = models.DateField("Đăng ký giảm trừ từ", db_column="RegisteredFrom")
    registered_to = models.DateField("Đến ngày", null=True, blank=True, db_column="RegisteredTo")
    is_active = models.BooleanField("Còn hiệu lực", default=True, db_column="IsActive")

    class Meta:
        db_table = "tblEmployeeDependent"
        verbose_name = "Người phụ thuộc"
        verbose_name_plural = "Người phụ thuộc"

    def __str__(self):
        return f"{self.full_name} ({self.relationship}) - {self.employee}"

    def clean(self):
        if self.registered_to and self.registered_from and self.registered_to < self.registered_from:
            raise ValidationError("Ngày kết thúc phải sau hoặc bằng ngày đăng ký giảm trừ.")
        self._validate_no_overlap()

    def _validate_no_overlap(self):
        """Không cho đăng ký trùng (cùng họ tên) cho cùng 1 nhân viên trong khoảng thời gian
        chồng lấn — kể cả khi 2 dòng ghi 'quan hệ' khác nhau, vì căn cứ giảm trừ thuế là theo
        người phụ thuộc (họ tên/CCCD), không phải theo quan hệ."""
        if not (self.employee_id and self.full_name and self.registered_from):
            return
        overlapping = EmployeeDependent.objects.filter(
            employee_id=self.employee_id,
            full_name__iexact=self.full_name.strip(),
            is_active=True,
        ).filter(
            models.Q(registered_to__isnull=True) | models.Q(registered_to__gte=self.registered_from)
        )
        if self.registered_to:
            overlapping = overlapping.filter(registered_from__lte=self.registered_to)
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        existing = overlapping.order_by("registered_from").first()
        if existing:
            to_text = f"đến {existing.registered_to:%d/%m/%Y}" if existing.registered_to else "chưa kết thúc"
            raise ValidationError(
                f"Người phụ thuộc \"{self.full_name}\" đã được đăng ký giảm trừ cho nhân viên này "
                f"trùng thời gian (từ {existing.registered_from:%d/%m/%Y}, {to_text}) — không được "
                f"đăng ký trùng, sẽ làm giảm trừ thuế bị tính nhân đôi."
            )


# ============================================================
# 3. KỲ LƯƠNG VÀ BẢNG LƯƠNG
# ============================================================

class PayrollPeriod(BaseAuditModel):
    STATUS_CHOICES = [("Open", "Đang mở"), ("Locked", "Đã khóa")]

    payroll_month = models.SmallIntegerField("Tháng", db_column="PayrollMonth")
    payroll_year = models.SmallIntegerField("Năm", db_column="PayrollYear")
    start_date = models.DateField("Ngày bắt đầu", db_column="StartDate")
    end_date = models.DateField("Ngày kết thúc", db_column="EndDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Open", db_column="Status")

    class Meta:
        db_table = "tblPayrollPeriod"
        verbose_name = "Kỳ lương"
        verbose_name_plural = "Kỳ lương"
        constraints = [
            models.UniqueConstraint(fields=["payroll_month", "payroll_year"], name="UX_PayrollPeriod_Month_Year")
        ]

    def __str__(self):
        return f"Kỳ lương {self.payroll_month:02d}/{self.payroll_year} ({self.get_status_display()})"


class Payroll(BaseAuditModel):
    payroll_period = models.ForeignKey(
        PayrollPeriod, verbose_name="Kỳ lương", on_delete=models.PROTECT,
        db_column="PayrollPeriodID", related_name="payrolls",
    )
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.PROTECT,
        db_column="EmployeeID", related_name="payrolls",
    )
    basic_salary = models.DecimalField("Lương cơ bản", max_digits=18, decimal_places=2, default=0, db_column="BasicSalary")
    allowance = models.DecimalField("Phụ cấp", max_digits=18, decimal_places=2, default=0, db_column="Allowance")
    standard_working_days = models.DecimalField(
        "Ngày công chuẩn của kỳ", max_digits=4, decimal_places=1, default=0,
        db_column="StandardWorkingDays",
        help_text="Số ngày công chuẩn (T2–T6, đã trừ ngày lễ) của cả kỳ lương — do calculate() tự tính.",
    )
    actual_working_days = models.DecimalField(
        "Ngày công thực tế được tính lương", max_digits=4, decimal_places=1, default=0,
        db_column="ActualWorkingDays",
        help_text="Ngày công chuẩn đã giới hạn theo ngày vào làm/nghỉ việc, trừ tiếp số ngày "
                  "nghỉ không lương trong tháng — do calculate() tự tính, dùng để quy đổi "
                  "Lương cơ bản/Phụ cấp theo tỷ lệ ngày công thực tế / ngày công chuẩn.",
    )
    overtime_amount = models.DecimalField(
        "Tiền tăng ca", max_digits=18, decimal_places=2, default=0, db_column="OvertimeAmount"
    )
    overtime_tax_exempt_amount = models.DecimalField(
        "Tiền tăng ca được miễn thuế", max_digits=18, decimal_places=2, default=0,
        db_column="OvertimeTaxExemptAmount",
        help_text="Phần tiền làm thêm giờ TRẢ CAO HƠN mức lương giờ làm việc bình thường "
                  "(phần chênh lệch) được miễn thuế TNCN. Ví dụ: làm thêm ngày thường trả 150%, "
                  "thì 50% chênh lệch nhập vào đây. Để 0 nếu không có.",
    )
    insurance_salary = models.DecimalField(
        "Lương đóng bảo hiểm", max_digits=18, decimal_places=2, default=0,
        db_column="InsuranceSalary",
        help_text="Tiền lương ghi trong hợp đồng dùng làm căn cứ đóng BHXH/BHYT/BHTN. "
                  "Để trống (0) thì hệ thống tự lấy bằng Lương cơ bản.",
    )
    gross_income = models.DecimalField(
        "Tổng thu nhập (Gross)", max_digits=18, decimal_places=2, default=0, db_column="GrossIncome"
    )
    insurance_amount = models.DecimalField(
        "Bảo hiểm (NLĐ đóng)", max_digits=18, decimal_places=2, default=0, db_column="InsuranceAmount"
    )
    tax_amount = models.DecimalField("Thuế TNCN", max_digits=18, decimal_places=2, default=0, db_column="TaxAmount")
    deduction_amount = models.DecimalField(
        "Khấu trừ khác", max_digits=18, decimal_places=2, default=0, db_column="DeductionAmount"
    )
    net_income = models.DecimalField(
        "Thực lãnh (Net)", max_digits=18, decimal_places=2, default=0, db_column="NetIncome"
    )

    calculated_at = models.DateTimeField(null=True, blank=True, editable=False)
    calculation_signature = models.CharField(max_length=64, blank=True, editable=False)

    INPUT_FIELDS = ("basic_salary", "allowance", "overtime_amount", "overtime_tax_exempt_amount",
                    "insurance_salary", "deduction_amount")
    RESULT_FIELDS = ("standard_working_days", "actual_working_days", "gross_income",
                     "insurance_amount", "tax_amount", "net_income")

    def input_signature(self):
        values = [str(Decimal(str(getattr(self, name) or 0)).normalize()) for name in self.INPUT_FIELDS]
        values.extend([str(self.employee_id), str(self.payroll_period_id)])
        return hashlib.sha256("|".join(values).encode()).hexdigest()

    def validate_calculated(self, *, configuration=None):
        if not self.calculated_at or self.calculation_signature != self.input_signature():
            raise ValidationError("Có dòng lương chưa tính hoặc đã đổi đầu vào; hãy tính lương lại trước khi khóa.")
        fresh = copy.copy(self)
        fresh.calculate(configuration=configuration)
        if any(getattr(fresh, name) != getattr(self, name) for name in self.RESULT_FIELDS):
            raise ValidationError("Dữ liệu công/nhân sự/cấu hình lương đã thay đổi; hãy tính lương lại trước khi khóa.")

    class Meta:
        db_table = "tblPayroll"
        verbose_name = "Bảng lương"
        verbose_name_plural = "Bảng lương"
        constraints = [
            models.UniqueConstraint(fields=["payroll_period", "employee"], name="UX_Payroll_Period_Employee")
        ]

    def clean(self):
        self.validate_input_amounts()
        # C2 (đã sửa): trước đây có `and self.pk` — chỉ chặn SỬA dòng đã tồn tại, còn TẠO MỚI
        # (self.pk chưa có trước khi save) một dòng Payroll cho kỳ đã Locked lại lọt qua hoàn
        # toàn. Bỏ điều kiện `self.pk` để chặn cả 2 trường hợp.
        if self.payroll_period_id and self.payroll_period.status == "Locked":
            raise ValidationError("Kỳ lương đã khóa — không được thêm/sửa bảng lương.")

    def validate_input_amounts(self):
        amounts = {name: _decimal_amount(getattr(self, name)) for name in self.INPUT_FIELDS}
        errors = {
            name: "Số tiền không được âm."
            for name, amount in amounts.items() if amount is not None and amount < 0
        }
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.employee} - {self.payroll_period}"

    # -------- Công thức tính lương, theo 06A_Payroll_Statutory_Rate_Master_Data mục 2 --------
    @staticmethod
    def load_calculation_configuration(period_date):
        insurance_cfg = (
            InsuranceRateConfig.objects.filter(effective_from__lte=period_date)
            .filter(models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=period_date))
            .order_by("-effective_from")
            .first()
        )
        deduction_cfg = (
            TaxDeductionConfig.objects.filter(effective_from__lte=period_date)
            .filter(models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=period_date))
            .order_by("-effective_from")
            .first()
        )
        # BUG C1 (đã sửa): trước đây filter bậc thuế chỉ theo effective_from__lte + (effective_to
        # isnull HOẶC >= period) — nếu thế hệ cũ chưa bị đóng effective_to (quên đóng khi thêm
        # thế hệ mới), CẢ 2 thế hệ đều khớp filter cùng lúc → bracket_no trùng, thuế bị cộng đôi
        # từng bậc một cách âm thầm (không có lỗi hiển thị). Bậc thuế có NHIỀU dòng (1 dòng/bậc)
        # cùng chung 1 effective_from cho mỗi lần khai báo (khác Insurance/TaxDeduction chỉ có
        # 1 dòng/thế hệ nên .first() vốn đã đúng). Phải xác định ĐÚNG 1 thế hệ trước, rồi mới lấy
        # toàn bộ bậc của thế hệ đó — không lọc lẫn thế hệ theo effective_to nữa.
        latest_bracket_generation = (
            PersonalIncomeTaxBracket.objects.filter(effective_from__lte=period_date)
            .order_by("-effective_from")
            .values_list("effective_from", flat=True)
            .first()
        )
        tax_brackets = list(
            PersonalIncomeTaxBracket.objects.filter(effective_from=latest_bracket_generation).order_by("bracket_no")
        ) if latest_bracket_generation else []

        return PayrollConfiguration(period_date, insurance_cfg, deduction_cfg, tuple(tax_brackets))

    def calculate(self, *, configuration=None):
        """Tính Gross, Bảo hiểm, Thuế TNCN, Net theo tỷ lệ hiệu lực tại thời điểm StartDate của kỳ lương."""
        self.validate_input_amounts()
        from apps.attendance.models import MonthlyAttendanceSummary
        from apps.attendance.services import standard_working_days as _standard_working_days

        period = self.payroll_period
        period_date = period.start_date

        configuration = configuration or self.load_calculation_configuration(period_date)
        if configuration.period_date != period_date:
            raise ValidationError("Payroll configuration does not match the period start date.")
        insurance_cfg = configuration.insurance
        deduction_cfg = configuration.deduction
        tax_brackets = configuration.tax_brackets

        if not insurance_cfg or not deduction_cfg or not tax_brackets:
            raise ValidationError(
                "Chưa có cấu hình Tỷ lệ Bảo hiểm / Giảm trừ thuế / Bậc thuế cho kỳ lương này. "
                "Vào mục Payroll → khai báo các cấu hình trước."
            )
        self.standard_working_days = _standard_working_days(period.start_date, period.end_date)

        # Khoảng ngày nhân viên thực sự có mặt trong kỳ, giới hạn bởi ngày vào làm / ngày nghỉ việc.
        present_from = period.start_date
        if self.employee.join_date and self.employee.join_date > present_from:
            present_from = self.employee.join_date
        present_to = period.end_date
        if self.employee.leave_date and self.employee.leave_date < present_to:
            present_to = self.employee.leave_date
        present_standard_days = _standard_working_days(present_from, present_to)

        # I3 (đã sửa): chỉ dùng số liệu đã được quản lý duyệt (status="Approved") — trước đây
        # dùng thẳng số nhân viên tự khai (status="Pending" mặc định) để trừ lương, không ai
        # xác nhận lại. Nếu chưa duyệt, coi như chưa có số liệu (unpaid_days=0) cho tới khi duyệt.
        summary = MonthlyAttendanceSummary.objects.filter(
            employee=self.employee, year=period.payroll_year, month=period.payroll_month,
            status=MonthlyAttendanceSummary.STATUS_APPROVED,
        ).first()
        unpaid_days = summary.unpaid_leave_days if summary else Decimal("0")

        self.actual_working_days = max(present_standard_days - unpaid_days, Decimal("0"))

        if self.standard_working_days > 0:
            work_ratio = min(self.actual_working_days / self.standard_working_days, Decimal("1"))
        else:
            work_ratio = Decimal("1")

        prorated_basic_salary = (self.basic_salary * work_ratio).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        prorated_allowance = (self.allowance * work_ratio).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        self.gross_income = prorated_basic_salary + prorated_allowance + self.overtime_amount

        # ---- Bảo hiểm NLĐ đóng ----

        # ---- Bảo hiểm NLĐ đóng ----
        # Căn cứ đóng là TIỀN LƯƠNG THEO HỢP ĐỒNG, không phải tổng thu nhập:
        # không tính tiền tăng ca. Nếu chưa khai báo riêng thì lấy bằng lương cơ bản.
        insurance_base = self.insurance_salary or self.basic_salary

        # Trần đóng theo luật: BHXH/BHYT tối đa 20 lần lương cơ sở,
        # BHTN tối đa 20 lần lương tối thiểu vùng.
        sh_base = min(insurance_base, insurance_cfg.social_health_cap) \
            if insurance_cfg.social_health_cap else insurance_base
        ui_base = min(insurance_base, insurance_cfg.unemployment_cap) \
            if insurance_cfg.unemployment_cap else insurance_base

        social = sh_base * insurance_cfg.employee_social_insurance_rate / Decimal("100")
        health = sh_base * insurance_cfg.employee_health_insurance_rate / Decimal("100")
        unemployment = ui_base * insurance_cfg.employee_unemployment_insurance_rate / Decimal("100")

        self.insurance_amount = (social + health + unemployment).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )

        # Số người phụ thuộc còn hiệu lực tại thời điểm tính lương
        dependent_count = EmployeeDependent.objects.filter(
            employee=self.employee, is_active=True, registered_from__lte=period_date
        ).filter(
            models.Q(registered_to__isnull=True) | models.Q(registered_to__gte=period_date)
        ).count()

        # Phần tiền làm thêm giờ trả cao hơn giờ làm việc bình thường được miễn thuế TNCN
        exempt = min(self.overtime_tax_exempt_amount or Decimal("0"), self.overtime_amount or Decimal("0"))

        taxable_income = (
            self.gross_income
            - exempt
            - self.insurance_amount
            - deduction_cfg.self_deduction_monthly
            - (dependent_count * deduction_cfg.dependent_deduction_monthly)
        )
        taxable_income = max(taxable_income, Decimal("0"))

        # Tính thuế lũy tiến từng phần
        tax = Decimal("0")
        for bracket in tax_brackets:
            lower = bracket.income_from_monthly
            upper = bracket.income_to_monthly
            if taxable_income <= lower:
                break
            portion_top = min(taxable_income, upper) if upper else taxable_income
            portion = portion_top - lower
            if portion > 0:
                tax += portion * bracket.tax_rate / Decimal("100")

        self.tax_amount = tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        self.net_income = self.gross_income - self.insurance_amount - self.tax_amount - self.deduction_amount
        self.calculated_at = timezone.now()
        self.calculation_signature = self.input_signature()


class Payslip(BaseAuditModel):
    payroll = models.OneToOneField(
        Payroll, verbose_name="Bảng lương", on_delete=models.CASCADE,
        db_column="PayrollID", related_name="payslip",
    )
    generated_date = models.DateTimeField("Ngày xuất phiếu", auto_now_add=True, db_column="GeneratedDate")
    file_url = models.CharField("Đường dẫn file", max_length=500, null=True, blank=True, db_column="FileUrl")

    class Meta:
        db_table = "tblPayslip"
        verbose_name = "Phiếu lương"
        verbose_name_plural = "Phiếu lương"

    def __str__(self):
        return f"Phiếu lương - {self.payroll}"
