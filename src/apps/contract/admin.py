from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import ContractType, Contract, ContractAppendix

VIEW_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DIRECTOR")
EDIT_ROLES = ("SUPER_ADMIN", "HR_MANAGER")


class ContractTypeAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES


admin.site.register(ContractType, ContractTypeAdmin)


class ContractAppendixInline(admin.TabularInline):
    model = ContractAppendix
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(Contract)
class ContractAdmin(BaseAuditAdmin):
    list_display = ("contract_no", "employee", "contract_type", "start_date", "end_date", "status")
    list_filter = ("status", "contract_type")
    search_fields = ("contract_no", "employee__full_name", "employee__employee_code")
    inlines = [ContractAppendixInline]

    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES