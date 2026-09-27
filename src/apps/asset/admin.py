from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import (
    AssetType, Asset, AssetAllocation, AssetMaintenance,
    InventorySession, InventoryMember, InventoryLine,
    AssetDisposalRequest, AssetDisposalRequestMember, AssetDisposalItem, AssetDisposalMinutes,
)

VIEW_ROLES = (
    "SUPER_ADMIN", "SYS_ADMIN", "DIRECTOR", "HR_MANAGER", "HR_OFFICER",
    "FINANCE_OFFICER", "PROJECT_COORDINATOR",
)
EDIT_ROLES = ("SUPER_ADMIN", "SYS_ADMIN", "HR_MANAGER", "HR_OFFICER")


class AssetTypeAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES


admin.site.register(AssetType, AssetTypeAdmin)


class AssetMaintenanceInline(admin.TabularInline):
    model = AssetMaintenance
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(Asset)
class AssetAdmin(BaseAuditAdmin):
    list_display = ("asset_code", "asset_name", "asset_type", "location", "status")
    list_filter = ("status", "asset_type", "condition")
    search_fields = ("asset_code", "asset_name", "serial_number")
    inlines = [AssetMaintenanceInline]
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES


@admin.register(AssetAllocation)
class AssetAllocationAdmin(BaseAuditAdmin):
    list_display = ("asset", "employee", "assigned_date", "return_date")
    search_fields = ("asset__asset_code", "employee__full_name")
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES


class InventoryMemberInline(admin.TabularInline):
    model = InventoryMember
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(InventorySession)
class InventorySessionAdmin(BaseAuditAdmin):
    list_display = ("session_name", "office_name", "inventory_datetime", "status")
    inlines = [InventoryMemberInline]
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES


@admin.register(AssetDisposalRequest)
class AssetDisposalRequestAdmin(BaseAuditAdmin):
    list_display = ("request_no", "request_date", "location_name", "status")
    view_roles = VIEW_ROLES + ("DIRECTOR",)
    edit_roles = EDIT_ROLES
