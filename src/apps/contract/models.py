from django.core.exceptions import ValidationError
from django.db import models
from apps.common.models import BaseAuditModel


class ContractType(BaseAuditModel):
    contract_type_code = models.CharField("Mã loại HĐ", max_length=50, unique=True, db_column="ContractTypeCode")
    contract_type_name = models.CharField("Tên loại hợp đồng", max_length=100, db_column="ContractTypeName")

    class Meta:
        db_table = "tblContractType"
        verbose_name = "Loại hợp đồng"
        verbose_name_plural = "Loại hợp đồng"

    def __str__(self):
        return self.contract_type_name


class Contract(BaseAuditModel):
    STATUS_CHOICES = [
        ("Draft", "Nháp"),
        ("Active", "Đang hiệu lực"),
        ("Expired", "Hết hạn"),
        ("Terminated", "Chấm dứt trước hạn"),
    ]

    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.PROTECT,
        db_column="EmployeeID", related_name="contracts",
    )
    contract_type = models.ForeignKey(
        ContractType, verbose_name="Loại hợp đồng", on_delete=models.PROTECT,
        db_column="ContractTypeID", related_name="contracts",
    )
    contract_no = models.CharField("Số hợp đồng", max_length=50, unique=True, db_column="ContractNo")
    start_date = models.DateField("Ngày bắt đầu", db_column="StartDate")
    end_date = models.DateField(
        "Ngày kết thúc", null=True, blank=True, db_column="EndDate",
        help_text="Để trống nếu là hợp đồng không xác định thời hạn",
    )
    basic_salary = models.DecimalField(
        "Lương cơ bản", max_digits=18, decimal_places=2, db_column="BasicSalary"
    )
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Draft", db_column="Status")

    class Meta:
        db_table = "tblContract"
        verbose_name = "Hợp đồng lao động"
        verbose_name_plural = "Hợp đồng lao động"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu.")

    def __str__(self):
        return f"{self.contract_no} - {self.employee}"


class ContractAppendix(BaseAuditModel):
    contract = models.ForeignKey(
        Contract, verbose_name="Hợp đồng", on_delete=models.CASCADE,
        db_column="ContractID", related_name="appendices",
    )
    appendix_no = models.CharField("Số phụ lục", max_length=50, db_column="AppendixNo")
    effective_date = models.DateField("Ngày hiệu lực", db_column="EffectiveDate")
    description = models.CharField(
        "Nội dung thay đổi", max_length=1000, null=True, blank=True, db_column="Description"
    )

    class Meta:
        db_table = "tblContractAppendix"
        verbose_name = "Phụ lục hợp đồng"
        verbose_name_plural = "Phụ lục hợp đồng"

    def __str__(self):
        return f"{self.appendix_no} - {self.contract}"