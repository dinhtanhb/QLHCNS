from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """Theo 10_RBAC_Permission_Matrix.md mục 2 — 8 vai trò chuẩn."""
    role_code = models.CharField(max_length=30, unique=True, db_column="RoleCode")
    role_name = models.CharField(max_length=100, db_column="RoleName")

    class Meta:
        db_table = "tblRole"

    def __str__(self):
        return self.role_name


class User(AbstractUser):
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.PROTECT,
        db_column="RoleID", related_name="users",
    )
    employee = models.OneToOneField(
        "hrm.Employee", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="EmployeeID", related_name="user_account",
    )
    external_object_id = models.CharField(
        max_length=100, null=True, blank=True, unique=True,
        db_column="ExternalObjectId",
    )

    class Meta:
        db_table = "tblUser"