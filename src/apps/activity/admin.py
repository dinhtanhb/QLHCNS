from django.contrib import admin, messages

from apps.common.admin import BaseAuditAdmin
from apps.activity.models import Activity
from apps.activity.services import create_task_for_activity

VIEW_ROLES = (
    "SUPER_ADMIN", "DIRECTOR", "PROJECT_MANAGER", "PROJECT_COORDINATOR", "CBDA",
)
EDIT_ROLES = ("SUPER_ADMIN", "PROJECT_MANAGER", "PROJECT_COORDINATOR")


@admin.register(Activity)
class ActivityAdmin(BaseAuditAdmin):
    view_roles = VIEW_ROLES
    edit_roles = EDIT_ROLES
    list_display = (
        "activity_code", "activity_name", "project", "lead_cbda",
        "start_date", "end_date", "status", "outgoing_document",
    )
    list_filter = ("status", "project")
    search_fields = ("activity_code", "activity_name", "location")
    autocomplete_fields = ("project",)
    actions = ["action_create_tracking_task"]

    @admin.action(description="Kiểm tra/tạo lại Task báo cáo cho các hoạt động đã có công văn")
    def action_create_tracking_task(self, request, queryset):
        created, skipped = 0, 0
        for activity in queryset:
            if not activity.outgoing_document_id:
                skipped += 1
                continue
            _, was_created = create_task_for_activity(activity)
            created += int(was_created)
            skipped += int(not was_created)

        if created:
            self.message_user(
                request, f"Đã tạo/kiểm tra Công việc theo dõi cho {created} hoạt động.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Bỏ qua {skipped} hoạt động chưa tạo mới (đã có Task hoặc chưa có Công văn đi).",
                level=messages.WARNING,
            )
