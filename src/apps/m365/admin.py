from django.contrib import admin

from apps.common.admin import BaseAuditAdmin
from apps.m365.models import CompanyMedia

VIEW_ROLES = ("SUPER_ADMIN", "SYS_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
EDIT_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")


@admin.register(CompanyMedia)
class CompanyMediaAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES
    list_display = ("title", "media_type", "category", "department", "created_date", "created_by")
    list_filter = ("media_type", "category", "department")
    search_fields = ("title", "description", "category")