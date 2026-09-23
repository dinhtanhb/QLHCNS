from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from apps.common.models import BaseAuditModel


class KPIPeriod(BaseAuditModel):
    year = models.SmallIntegerField("Năm", db_column="Year")
    quarter = models.SmallIntegerField("Quý", null=True, blank=True, db_column="Quarter")
    month = models.SmallIntegerField("Tháng", null=True, blank=True, db_column="Month")

    class Meta:
        db_table = "tblKPIPeriod"
        verbose_name = "Kỳ đánh giá KPI"
        verbose_name_plural = "Kỳ đánh giá KPI"

    def __str__(self):
        if self.month:
            return f"Tháng {self.month}/{self.year}"
        if self.quarter:
            return f"Quý {self.quarter}/{self.year}"
        return f"Năm {self.year}"


class KPITemplate(BaseAuditModel):
    kpi_name = models.CharField("Tên KPI", max_length=300, db_column="KPIName")
    description = models.CharField("Mô tả", max_length=1000, null=True, blank=True, db_column="Description")
    weight = models.DecimalField("Trọng số (%)", max_digits=5, decimal_places=2, default=0, db_column="Weight")
    target_value = models.DecimalField(
        "Chỉ tiêu mặc định", max_digits=18, decimal_places=2, null=True, blank=True, db_column="TargetValue"
    )

    class Meta:
        db_table = "tblKPITemplate"
        verbose_name = "Mẫu KPI"
        verbose_name_plural = "Mẫu KPI"

    def __str__(self):
        return self.kpi_name


class BaseKPIResult(BaseAuditModel):
    kpi_template = models.ForeignKey(KPITemplate, on_delete=models.PROTECT, db_column="KPITemplateID")
    kpi_period = models.ForeignKey(KPIPeriod, on_delete=models.PROTECT, db_column="KPIPeriodID")
    target = models.DecimalField("Chỉ tiêu", max_digits=18, decimal_places=2, default=0, db_column="Target")
    actual = models.DecimalField("Thực tế", max_digits=18, decimal_places=2, null=True, blank=True, db_column="Actual")
    achievement = models.DecimalField(
        "Tỷ lệ đạt (%)", max_digits=9, decimal_places=2, default=0, db_column="Achievement"
    )

    class Meta:
        abstract = True

    def calculate_achievement(self):
        if self.target and self.actual is not None:
            self.achievement = (self.actual / self.target * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            self.achievement = Decimal("0")


class CompanyKPI(BaseKPIResult):
    score = models.DecimalField("Điểm", max_digits=9, decimal_places=2, default=0, db_column="Score")

    class Meta:
        db_table = "tblCompanyKPI"
        verbose_name = "KPI Công ty"
        verbose_name_plural = "KPI Công ty"

    def save(self, *args, **kwargs):
        self.calculate_achievement()
        self.score = (self.achievement * self.kpi_template.weight / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.kpi_template} - {self.kpi_period}"


class DepartmentKPI(BaseKPIResult):
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", on_delete=models.PROTECT,
        db_column="DepartmentID", related_name="kpi_results",
    )

    class Meta:
        db_table = "tblDepartmentKPI"
        verbose_name = "KPI Phòng ban"
        verbose_name_plural = "KPI Phòng ban"

    def save(self, *args, **kwargs):
        self.calculate_achievement()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.department} - {self.kpi_template} - {self.kpi_period}"


class EmployeeKPI(BaseKPIResult):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.PROTECT,
        db_column="EmployeeID", related_name="kpi_results",
    )
    score = models.DecimalField("Điểm", max_digits=9, decimal_places=2, default=0, db_column="Score")

    class Meta:
        db_table = "tblEmployeeKPI"
        verbose_name = "KPI Nhân viên"
        verbose_name_plural = "KPI Nhân viên"

    def save(self, *args, **kwargs):
        self.calculate_achievement()
        self.score = (self.achievement * self.kpi_template.weight / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.kpi_template} - {self.kpi_period}"