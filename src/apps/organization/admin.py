from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import Organization, Department, Position, JobTitle

VIEW_ROLES = ("SUPER_ADMIN", "SYS_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
EDIT_ROLES = ("SUPER_ADMIN", "HR_MANAGER")


class OrgBaseAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES


admin.site.register(Organization, OrgBaseAdmin)
admin.site.register(Department, OrgBaseAdmin)
admin.site.register(Position, OrgBaseAdmin)
admin.site.register(JobTitle, OrgBaseAdmin)