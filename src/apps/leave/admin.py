from django.contrib import admin
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

    @admin.action(description="✅ Duyệt các đơn đã chọn")
    def approve_selected(self, request, queryset):
        role_code = self._role_code(request)
        if not request.user.is_superuser and role_code not in ("HR_MANAGER", "DEPT_MANAGER", "DIRECTOR"):
            self.message_user(request, "Vai trò của anh/chị không có quyền duyệt đơn.", level="ERROR")
            return
        count = 0
        for leave_request in queryset.filter(status="Pending"):
            leave_request.status = "Approved"
            leave_request.save()
            LeaveApproval.objects.create(
                leave_request=leave_request,
                approver=request.user.employee,
                decision="Approved",
                created_by=request.user,
            )
            count += 1
        self.message_user(request, f"Đã duyệt {count} đơn.")

    @admin.action(description="❌ Từ chối các đơn đã chọn")
    def reject_selected(self, request, queryset):
        role_code = self._role_code(request)
        if not request.user.is_superuser and role_code not in ("HR_MANAGER", "DEPT_MANAGER", "DIRECTOR"):
            self.message_user(request, "Vai trò của anh/chị không có quyền duyệt đơn.", level="ERROR")
            return
        count = 0
        for leave_request in queryset.filter(status="Pending"):
            leave_request.status = "Rejected"
            leave_request.save()
            LeaveApproval.objects.create(
                leave_request=leave_request,
                approver=request.user.employee,
                decision="Rejected",
                created_by=request.user,
            )
            count += 1
        self.message_user(request, f"Đã từ chối {count} đơn.")


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