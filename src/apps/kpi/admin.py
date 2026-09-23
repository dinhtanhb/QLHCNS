from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import KPIPeriod, KPITemplate, CompanyKPI, DepartmentKPI, EmployeeKPI

SETUP_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "DIRECTOR")


class SetupAdmin(BaseAuditAdmin):
    view_roles = SETUP_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")


admin.site.register(KPIPeriod, SetupAdmin)
admin.site.register(KPITemplate, SetupAdmin)


@admin.register(CompanyKPI)
class CompanyKPIAdmin(BaseAuditAdmin):
    list_display = ("kpi_template", "kpi_period", "target", "actual", "achievement", "score")
    readonly_fields = ("achievement", "score")
    view_roles = SETUP_ROLES
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "DIRECTOR")


@admin.register(DepartmentKPI)
class DepartmentKPIAdmin(BaseAuditAdmin):
    list_display = ("department", "kpi_template", "kpi_period", "target", "actual", "achievement")
    readonly_fields = ("achievement",)
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "DEPT_MANAGER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(department_id__in=dept_ids)
        return qs


@admin.register(EmployeeKPI)
class EmployeeKPIAdmin(BaseAuditAdmin):
    list_display = ("employee", "kpi_template", "kpi_period", "target", "actual", "achievement", "score")
    readonly_fields = ("achievement", "score")
    search_fields = ("employee__full_name", "employee__employee_code")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "DEPT_MANAGER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(employee__department_id__in=dept_ids)
        return qs