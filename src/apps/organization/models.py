from django.db import models
from apps.common.models import BaseAuditModel


class Organization(BaseAuditModel):
    organization_code = models.CharField(max_length=50, unique=True, db_column="OrganizationCode")
    organization_name = models.CharField(max_length=200, db_column="OrganizationName")
    description = models.CharField(max_length=1000, null=True, blank=True, db_column="Description")
    is_active = models.BooleanField(default=True, db_column="IsActive")

    class Meta:
        db_table = "tblOrganization"
        verbose_name = "Tổ chức"
        verbose_name_plural = "Tổ chức"

    def __str__(self):
        return self.organization_name


class Department(BaseAuditModel):
    department_code = models.CharField(max_length=50, unique=True, db_column="DepartmentCode")
    department_name = models.CharField(max_length=200, db_column="DepartmentName")
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT,
        db_column="OrganizationID", related_name="departments",
    )
    # Dùng string reference vì Employee nằm ở app "hrm" tạo sau — Django tự xử lý thứ tự migration.
    manager = models.ForeignKey(
        "hrm.Employee", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="ManagerEmployeeID", related_name="managed_departments",
    )
    description = models.CharField(max_length=1000, null=True, blank=True, db_column="Description")
    is_active = models.BooleanField(default=True, db_column="IsActive")

    class Meta:
        db_table = "tblDepartment"
        verbose_name = "Phòng ban"
        verbose_name_plural = "Phòng ban"

    def __str__(self):
        return self.department_name


class Position(BaseAuditModel):
    position_code = models.CharField(max_length=50, unique=True, db_column="PositionCode")
    position_name = models.CharField(max_length=200, db_column="PositionName")
    description = models.CharField(max_length=1000, null=True, blank=True, db_column="Description")
    is_active = models.BooleanField(default=True, db_column="IsActive")

    class Meta:
        db_table = "tblPosition"
        verbose_name = "Vị trí"
        verbose_name_plural = "Vị trí"

    def __str__(self):
        return self.position_name


class JobTitle(BaseAuditModel):
    job_title_code = models.CharField(max_length=50, unique=True, db_column="JobTitleCode")
    job_title_name = models.CharField(max_length=200, db_column="JobTitleName")
    description = models.CharField(max_length=1000, null=True, blank=True, db_column="Description")
    is_active = models.BooleanField(default=True, db_column="IsActive")

    class Meta:
        db_table = "tblJobTitle"
        verbose_name = "Chức danh"
        verbose_name_plural = "Chức danh"

    def __str__(self):
        return self.job_title_name