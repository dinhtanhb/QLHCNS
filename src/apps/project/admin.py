from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import Project


@admin.register(Project)
class ProjectAdmin(BaseAuditAdmin):
    list_display = ("project_code", "project_name", "department", "start_date", "end_date", "is_active")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "DEPT_MANAGER", "DIRECTOR", "FINANCE_OFFICER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")