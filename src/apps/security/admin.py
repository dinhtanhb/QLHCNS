from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.common.admin import RoleBasedAdminMixin
from .models import User, Role

ADMIN_ROLES = ("SUPER_ADMIN", "SYS_ADMIN")


class RoleAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    view_roles = ADMIN_ROLES
    edit_roles = ("SUPER_ADMIN",)  # chỉ Super Admin được thêm/sửa vai trò


admin.site.register(Role, RoleAdmin)


@admin.register(User)
class CustomUserAdmin(RoleBasedAdminMixin, UserAdmin):
    view_roles = ADMIN_ROLES
    edit_roles = ADMIN_ROLES

    fieldsets = UserAdmin.fieldsets + (  # type: ignore
        ("Thông tin hệ thống IHRMS", {"fields": ("role", "employee", "external_object_id")}),
    )