from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.common.admin import RoleBasedAdminMixin
from .models import User, Role
from .models import SecurityEvent
from django.db.models import Q

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

    def get_readonly_fields(self, request, obj=None):
        fields = tuple(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            fields += ('is_superuser', 'is_staff', 'groups', 'user_permissions', 'role', 'employee', 'external_object_id')
        return fields

    def scope_queryset(self, request, qs):
        # Resetting a privileged user's password is also privilege escalation.
        ordinary = Q(is_staff=False, groups__isnull=True, user_permissions__isnull=True) & (Q(role__role_code='EMPLOYEE') | Q(role__isnull=True))
        return qs.filter(is_superuser=False).filter(Q(pk=request.user.pk) | ordinary).distinct()

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if obj is None or request.user.is_superuser:
            return True
        if obj.is_superuser:
            return False
        return obj.pk == request.user.pk or (not obj.is_staff and not obj.groups.exists() and not obj.user_permissions.exists() and (obj.role is None or obj.role.role_code == 'EMPLOYEE'))

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj) and (obj is None or obj.pk != request.user.pk)


@admin.register(SecurityEvent)
class SecurityEventAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    view_roles = ('SUPER_ADMIN', 'SYS_ADMIN')
    edit_roles = ()
    list_display = ('occurred_at', 'user', 'action', 'resource', 'record_id')
    list_filter = ('action', 'resource')
    readonly_fields = ('occurred_at', 'user', 'action', 'resource', 'record_id')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
