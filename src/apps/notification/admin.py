from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(BaseAuditAdmin):
    list_display = ("employee", "title", "notification_type", "is_read", "created_date")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER")
    edit_roles = ("SUPER_ADMIN",)