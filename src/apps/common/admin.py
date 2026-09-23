from django.contrib import admin


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
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
        if self.edit_roles is None:
            return True
        return self._role_code(request) in self.edit_roles

    def has_change_permission(self, request, obj=None):
        return self.has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_add_permission(request)

    # ---- Giới hạn dữ liệu nhìn thấy (vd: Trưởng phòng chỉ thấy phòng mình) ----
    def get_queryset(self, request):
        can_manage = request.user.is_superuser or (
            request.user.is_staff and (
                self.edit_roles is None or self._role_code(request) in self.edit_roles
            )
        )
        if request.GET.get("show_deleted") == "1" and can_manage:
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

    def get_actions(self, request):
        actions = super().get_actions(request)
        for name, description in (
            ("soft_delete_selected", "Xóa mềm các bản ghi đã chọn"),
            ("restore_selected", "Khôi phục các bản ghi đã chọn"),
        ):
            if name not in actions:
                actions[name] = (getattr(self, name), name, description)
        if request.GET.get("show_deleted") == "1":
            actions.pop("soft_delete_selected", None)
        else:
            actions.pop("restore_selected", None)
        actions.pop("delete_selected", None)
        return actions

    @admin.action(description="Xóa mềm các bản ghi đã chọn")
    def soft_delete_selected(self, request, queryset):
        count, _ = queryset.delete(user=request.user)
        self.message_user(request, f"Đã chuyển {count} bản ghi vào danh sách đã xóa mềm.")

    @admin.action(description="Khôi phục các bản ghi đã chọn")
    def restore_selected(self, request, queryset):
        count = queryset.restore(user=request.user)
        self.message_user(request, f"Đã khôi phục {count} bản ghi.")

    def delete_model(self, request, obj):
        obj.delete(user=request.user)

    def delete_queryset(self, request, queryset):
        queryset.delete(user=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_deleted:
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
