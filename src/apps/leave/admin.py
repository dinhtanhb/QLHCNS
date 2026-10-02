from django.contrib import admin
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.common.admin import BaseAuditAdmin
from .models import LeaveType, LeaveRequest, LeaveApproval
from .models import LeaveBalance


class LeaveTypeAdmin(BaseAuditAdmin):
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")


admin.site.register(LeaveType, LeaveTypeAdmin)


class LeaveScopeMixin:
    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(employee__department_id__in=dept_ids)
        return qs


@admin.register(LeaveRequest)
class LeaveRequestAdmin(LeaveScopeMixin, BaseAuditAdmin):
    list_display = ("employee", "leave_type", "from_date", "to_date", "total_days", "status")
    list_filter = ("status", "leave_type")
    search_fields = ("employee__full_name", "employee__employee_code")
    actions = ["approve_selected", "reject_selected"]

    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER")

    readonly_fields = ("status", "total_days")

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.status != "Pending":
            return False
        return super().has_change_permission(request, obj)

    def has_approve_permission(self, request):
        return self.has_view_permission(request) and bool(getattr(request.user, "employee_id", None)) and (
            request.user.is_superuser or self._role_code(request) in ("HR_MANAGER", "DEPT_MANAGER", "DIRECTOR"))

    def _decide(self, request, queryset, decision):
        if not self.has_approve_permission(request):
            self.message_user(request, "Anh/chị không có quyền duyệt đơn.", level="ERROR")
            return
        count = 0
        for pk in self.scope_queryset(request, queryset).values_list("pk", flat=True):
            try:
                with transaction.atomic():
                    leave_request = self.scope_queryset(request, LeaveRequest.objects.select_for_update()).filter(pk=pk, status="Pending").first()
                    if leave_request is None:
                        continue
                    if self._role_code(request) == "DEPT_MANAGER" and leave_request.employee_id == request.user.employee_id:
                        raise ValidationError("Không thể tự duyệt đơn nghỉ phép của chính mình.")
                    leave_request.status = decision
                    leave_request.modified_by = request.user
                    leave_request.full_clean()
                    leave_request.save()
                    LeaveApproval.objects.create(leave_request=leave_request, approver=request.user.employee,
                        decision=decision, created_by=request.user)
                count += 1
            except ValidationError as error:
                self.message_user(request, "; ".join(error.messages), level="ERROR")
        self.message_user(request, f"Đã xử lý {count} đơn.")

    @admin.action(description="Duyệt các đơn đã chọn", permissions=["approve"])
    def approve_selected(self, request, queryset):
        self._decide(request, queryset, "Approved")

    @admin.action(description="Từ chối các đơn đã chọn", permissions=["approve"])
    def reject_selected(self, request, queryset):
        self._decide(request, queryset, "Rejected")


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(LeaveScopeMixin, BaseAuditAdmin):
    list_display = ("leave_request", "approver", "decision", "decision_date")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ()  # không ai được sửa tay lịch sử duyệt — chỉ sinh ra qua action ở trên

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(leave_request__employee__department_id__in=dept_ids)
        return qs


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(BaseAuditAdmin):
    list_display = ("employee", "year", "allocated_days", "carried_over_days", "used_days", "remaining_days")
    search_fields = ("employee__full_name", "employee__employee_code")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")
