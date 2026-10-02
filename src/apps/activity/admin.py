from django.contrib import admin, messages

from apps.common.admin import BaseAuditAdmin
from apps.activity.models import Activity
from apps.activity.services import create_task_for_activity, find_schedule_conflicts

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
    autocomplete_fields = ("project", "outgoing_document")
    actions = ["action_create_tracking_task"]

    def save_model(self, request, obj, form, change):
        conflicts = []
        if obj.status != "Cancelled" and obj.lead_cbda_id and obj.start_date and obj.end_date:
            conflicts = find_schedule_conflicts(
                employee_id=obj.lead_cbda_id,
                start_date=obj.start_date,
                end_date=obj.end_date,
                exclude_activity_id=obj.pk,
            )
        super().save_model(request, obj, form, change)
        if conflicts:
            names = ", ".join(
                f"{activity.activity_code} ({activity.start_date}–{activity.end_date})"
                for activity in conflicts
            )
            self.message_user(
                request,
                f"Lưu ý: CBDA {obj.lead_cbda} đang có lịch trùng với {names}. "
                "Đã lưu hoạt động; vui lòng kiểm tra và điều phối.",
                level=messages.WARNING,
            )

    @admin.action(description="Kiểm tra/tạo lại Task báo cáo cho các hoạt động đã có công văn", permissions=["change"])
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

