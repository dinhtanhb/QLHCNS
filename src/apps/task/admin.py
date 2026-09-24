from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import Task, TaskComment


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(Task)
class TaskAdmin(BaseAuditAdmin):
    list_display = ("task_code", "task_name", "assigned_to_employee", "department", "priority", "due_date", "status")
    list_filter = ("status", "priority", "department")
    search_fields = ("task_code", "task_name", "assigned_to_employee__full_name")
    inlines = [TaskCommentInline]

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