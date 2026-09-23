from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import ProcurementRequest, ProcurementItem, ProcurementApproval


class ProcurementItemInline(admin.TabularInline):
    model = ProcurementItem
    extra = 1
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(ProcurementRequest)
class ProcurementRequestAdmin(BaseAuditAdmin):
    list_display = ("request_no", "department", "requested_by", "request_date", "status")
    list_filter = ("status", "department")
    inlines = [ProcurementItemInline]
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "FINANCE_OFFICER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "FINANCE_OFFICER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(department_id__in=dept_ids)
        return qs


@admin.register(ProcurementApproval)
class ProcurementApprovalAdmin(BaseAuditAdmin):
    list_display = ("procurement_request", "approver", "decision", "decision_date")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "FINANCE_OFFICER", "DIRECTOR")
    edit_roles = ()