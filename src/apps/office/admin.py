from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import (
    IncomingDocument, OutgoingDocument, MeetingRoom, Vehicle,
    RoomBooking, VehicleBooking, SupplyItem, SupplyRequest, SupplyRequestItem, SealUsageLog,
)

OFFICE_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")


@admin.register(IncomingDocument)
class IncomingDocumentAdmin(BaseAuditAdmin):
    list_display = ("incoming_no", "incoming_date", "sender", "subject", "status")
    list_filter = ("status",)
    search_fields = ("incoming_no", "subject", "sender")
    view_roles = OFFICE_ROLES + ("DIRECTOR",)
    edit_roles = OFFICE_ROLES


@admin.register(OutgoingDocument)
class OutgoingDocumentAdmin(BaseAuditAdmin):
    list_display = ("outgoing_no", "outgoing_date", "recipient", "subject", "drafted_by", "signed_by")
    search_fields = ("outgoing_no", "subject", "recipient")
    view_roles = OFFICE_ROLES + ("DIRECTOR",)
    edit_roles = OFFICE_ROLES


class ResourceAdmin(BaseAuditAdmin):
    view_roles = OFFICE_ROLES
    edit_roles = OFFICE_ROLES


admin.site.register(MeetingRoom, ResourceAdmin)
admin.site.register(Vehicle, ResourceAdmin)


@admin.register(RoomBooking)
class RoomBookingAdmin(BaseAuditAdmin):
    list_display = ("room", "employee", "start_time", "end_time", "status")
    view_roles = OFFICE_ROLES
    edit_roles = OFFICE_ROLES  # nhân viên tự đặt qua Portal, Admin chỉ để HR sửa khi cần


@admin.register(VehicleBooking)
class VehicleBookingAdmin(BaseAuditAdmin):
    list_display = ("vehicle", "employee", "start_time", "end_time", "status")
    view_roles = OFFICE_ROLES
    edit_roles = OFFICE_ROLES


@admin.register(SupplyItem)
class SupplyItemAdmin(BaseAuditAdmin):
    list_display = ("item_code", "item_name", "unit", "quantity_in_stock", "min_stock_alert")
    view_roles = OFFICE_ROLES
    edit_roles = OFFICE_ROLES


class SupplyRequestItemInline(admin.TabularInline):
    model = SupplyRequestItem
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(SupplyRequest)
class SupplyRequestAdmin(BaseAuditAdmin):
    list_display = ("request_no", "employee", "request_date", "status")
    list_filter = ("status",)
    inlines = [SupplyRequestItemInline]
    view_roles = OFFICE_ROLES
    edit_roles = OFFICE_ROLES
    actions = ["approve_and_issue"]

    @admin.action(description="✅ Duyệt & cấp phát (trừ kho)")
    def approve_and_issue(self, request, queryset):
        count = 0
        for supply_request in queryset.filter(status="Pending"):
            for line in supply_request.items.all():
                line.item.quantity_in_stock -= line.quantity_requested
                line.item.save(update_fields=["quantity_in_stock"])
                line.quantity_issued = line.quantity_requested
                line.save(update_fields=["quantity_issued"])
            supply_request.status = "Issued"
            supply_request.save()
            count += 1
        self.message_user(request, f"Đã duyệt & cấp phát {count} đề nghị.")


@admin.register(SealUsageLog)
class SealUsageLogAdmin(BaseAuditAdmin):
    list_display = ("seal_type", "used_by", "used_date", "document_reference")
    list_filter = ("seal_type",)
    search_fields = ("document_reference", "used_by__full_name")
    view_roles = OFFICE_ROLES + ("DIRECTOR",)
    edit_roles = OFFICE_ROLES