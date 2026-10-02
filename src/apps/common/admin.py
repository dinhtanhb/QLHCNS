from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from django.http import HttpResponseRedirect


class RoleBasedAdminMixin:
    """
    Cơ chế phân quyền theo vai trò (RBAC), dùng cho mọi trang Admin trong hệ thống.
    Đối chiếu 10_RBAC_Permission_Matrix.md.

    Cách dùng ở từng ModelAdmin con:
        view_roles = ("SUPER_ADMIN", "HR_MANAGER", ...)   # None = ai đăng nhập Admin cũng xem được
        edit_roles = ("SUPER_ADMIN", "HR_MANAGER")         # None = ai đăng nhập Admin cũng sửa được
        Ghi đè scope_queryset() nếu cần giới hạn theo phòng ban / theo cá nhân.
    """
    view_roles = None
    edit_roles = None

    def _role_code(self, request):
        role = getattr(request.user, "role", None)
        return role.role_code if role else None

    # ---- Có thấy module này trong menu Admin không ----
    def has_module_permission(self, request):
        if not request.user.is_active or not request.user.is_staff:
            return False
        if request.user.is_superuser:
            return True
        if self.view_roles is None:
            return True
        return self._role_code(request) in self.view_roles

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        if not request.user.is_active or not request.user.is_staff:
            return False
        if request.user.is_superuser:
            return True
        if self.edit_roles is None:
            return True
        return self._role_code(request) in self.edit_roles

    def _object_in_scope(self, request, obj):
        if obj is None or request.user.is_superuser:
            return True
        manager = getattr(self.model, "all_objects", self.model._default_manager)
        return self.scope_queryset(request, manager.filter(pk=obj.pk)).exists()

    def has_change_permission(self, request, obj=None):
        return self.has_add_permission(request) and self._object_in_scope(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_add_permission(request) and self._object_in_scope(request, obj)

    # ---- Giới hạn dữ liệu nhìn thấy (vd: Trưởng phòng chỉ thấy phòng mình) ----
    def get_queryset(self, request):
        can_manage = request.user.is_superuser or (
            request.user.is_staff and (
                self.edit_roles is None or self._role_code(request) in self.edit_roles
            )
        )
        if request.GET.get("show_deleted") == "1" and can_manage and hasattr(self.model, "all_objects"):
            qs = self.model.all_objects.filter(is_deleted=True)
        else:
            qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return self.scope_queryset(request, qs)

    def scope_queryset(self, request, qs):
        """Mặc định: không giới hạn thêm. Từng ModelAdmin con tự ghi đè nếu cần."""
        return qs


class BaseAuditAdmin(RoleBasedAdminMixin, admin.ModelAdmin):
    """Khuôn dùng chung: ẩn field Audit + tự điền người tạo/sửa + có RBAC."""
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")
    change_list_template = "admin/common/audit_change_list.html"
    actions = ("soft_delete_selected", "restore_selected")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except ValidationError as error:
            self.message_user(request, "; ".join(error.messages), level="ERROR")
        except IntegrityError:
            self.message_user(request, "Dữ liệu đã thay đổi hoặc vi phạm ràng buộc. Tải lại và kiểm tra trước khi lưu.", level="ERROR")
        return HttpResponseRedirect(request.path)

    def get_actions(self, request):
        actions = super().get_actions(request)
        for name, description in (
            ("soft_delete_selected", "Xóa mềm các bản ghi đã chọn"),
            ("restore_selected", "Khôi phục các bản ghi đã chọn"),
        ):
            if self.has_delete_permission(request) and name not in actions:
                actions[name] = (getattr(type(self), name), name, description)
        if request.GET.get("show_deleted") == "1":
            actions.pop("soft_delete_selected", None)
        else:
            actions.pop("restore_selected", None)
        actions.pop("delete_selected", None)
        return actions

    @admin.action(description="Xóa mềm các bản ghi đã chọn", permissions=['delete'])
    def soft_delete_selected(self, request, queryset):
        try:
            with transaction.atomic():
                objects = list(queryset)
                if not self.has_delete_permission(request) or any(not self.has_delete_permission(request, obj) for obj in objects):
                    raise PermissionDenied
                count, _ = queryset.delete(user=request.user)
        except ValidationError as error:
            self.message_user(request, "; ".join(error.messages), level="ERROR")
            return
        self.message_user(request, f"Đã chuyển {count} bản ghi vào danh sách đã xóa mềm.")

    @admin.action(description="Khôi phục các bản ghi đã chọn", permissions=['delete'])
    def restore_selected(self, request, queryset):
        try:
            with transaction.atomic():
                objects = list(queryset)
                if not self.has_delete_permission(request) or any(not self.has_delete_permission(request, obj) for obj in objects):
                    raise PermissionDenied
                count = queryset.restore(user=request.user)
        except ValidationError as error:
            self.message_user(request, "; ".join(error.messages), level="ERROR")
            return
        self.message_user(request, f"Đã khôi phục {count} bản ghi.")

    def delete_model(self, request, obj):
        obj.delete(user=request.user)

    def delete_queryset(self, request, queryset):
        queryset.delete(user=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_deleted:
            return False
        return super().has_change_permission(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if self._role_code(request) == "DEPT_MANAGER" and not request.user.is_superuser:
            employee = getattr(request.user, "employee", None)
            departments = employee.managed_departments.values_list("pk", flat=True) if employee else []
            related = db_field.remote_field.model
            qs = kwargs.get("queryset", related._default_manager.all())
            if related._meta.label_lower == "organization.department":
                kwargs["queryset"] = qs.filter(pk__in=departments)
                kwargs["required"] = True
            elif related._meta.label_lower == "hrm.employee":
                kwargs["queryset"] = qs.filter(department_id__in=departments)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
