from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import Employee, EmployeeTransfer, EmployeePromotion, EmployeeReward, EmployeeDiscipline


@admin.register(Employee)
class EmployeeAdmin(BaseAuditAdmin):
    view_roles = ("SUPER_ADMIN", "SYS_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")

    def get_exclude(self, request, obj=None):
        excluded = tuple(super().get_exclude(request, obj) or ())
        if not request.user.is_superuser and self._role_code(request) in ("SYS_ADMIN", "DEPT_MANAGER"):
            excluded += ("national_id", "tax_code", "social_insurance_no")
        return excluded

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(department_id__in=dept_ids)
        return qs


class HistoryBaseAdmin(BaseAuditAdmin):
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")
    search_fields = ("employee__full_name", "employee__employee_code")


@admin.register(EmployeeTransfer)
class EmployeeTransferAdmin(HistoryBaseAdmin):
    list_display = ("employee", "from_department", "to_department", "effective_date")


@admin.register(EmployeePromotion)
class EmployeePromotionAdmin(HistoryBaseAdmin):
    list_display = ("employee", "old_position", "new_position", "effective_date")


@admin.register(EmployeeReward)
class EmployeeRewardAdmin(HistoryBaseAdmin):
    list_display = ("employee", "reward_type", "reward_date", "amount")


@admin.register(EmployeeDiscipline)
class EmployeeDisciplineAdmin(HistoryBaseAdmin):
    list_display = ("employee", "discipline_type", "discipline_date")
