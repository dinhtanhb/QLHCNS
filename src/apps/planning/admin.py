from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import HeadcountPlan, TrainingCourse, TrainingEnrollment, AnnualBudget, Event, with_headcounts

PLANNING_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "DIRECTOR")


@admin.register(HeadcountPlan)
class HeadcountPlanAdmin(BaseAuditAdmin):
    list_display = ("department", "year", "planned_headcount", "actual_headcount", "gap")
    view_roles = PLANNING_ROLES + ("DEPT_MANAGER",)
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")

    def get_queryset(self, request):
        return with_headcounts(super().get_queryset(request))

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(department_id__in=dept_ids)
        return qs


class TrainingEnrollmentInline(admin.TabularInline):
    model = TrainingEnrollment
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(TrainingCourse)
class TrainingCourseAdmin(BaseAuditAdmin):
    list_display = ("course_code", "course_name", "provider", "start_date", "status", "cost")
    inlines = [TrainingEnrollmentInline]
    view_roles = PLANNING_ROLES + ("HR_OFFICER",)
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")


@admin.register(AnnualBudget)
class AnnualBudgetAdmin(BaseAuditAdmin):
    list_display = ("year", "department", "category", "allocated_amount")
    view_roles = PLANNING_ROLES + ("FINANCE_OFFICER",)
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "FINANCE_OFFICER")


@admin.register(Event)
class EventAdmin(BaseAuditAdmin):
    list_display = ("title", "event_type", "department", "start_time", "end_time")
    list_filter = ("event_type", "department")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "DEPT_MANAGER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            from django.db.models import Q
            return qs.filter(Q(department_id__in=dept_ids) | Q(department__isnull=True))
        return qs
