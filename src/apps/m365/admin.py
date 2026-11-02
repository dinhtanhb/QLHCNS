from django.contrib import admin

from apps.common.admin import BaseAuditAdmin
from apps.m365.models import CompanyMedia

VIEW_ROLES = ("SUPER_ADMIN", "SYS_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
EDIT_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")


@admin.register(CompanyMedia)
class CompanyMediaAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES
    list_display = ("title", "status", "media_type", "category", "department", "created_date", "created_by")
    list_filter = ("status", "media_type", "category", "department")
    search_fields = ("title", "description", "category")

    def scope_queryset(self, request, qs):
        from apps.security.data_access import visible_company_media_for
        return visible_company_media_for(request.user, qs)
