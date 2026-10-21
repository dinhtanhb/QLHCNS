from django.core.exceptions import ValidationError
from django.db import connection, transaction

from .admin import BaseAuditAdmin


class LockedWorkflowAdmin(BaseAuditAdmin):
    """Recheck workflow state under lock before writing a stale Admin form."""
    editable_statuses = ()

    def _locked_current(self, obj):
        return self.model.all_objects.select_for_update().get(pk=obj.pk)

    def _require_editable(self, current):
        if current.status not in self.editable_statuses:
            raise ValidationError("Bản ghi đã được xử lý. Tải lại trang; không thể ghi đè nội dung đã duyệt.")

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                current = self._locked_current(obj)
                if current.is_deleted:
                    raise ValidationError("Bản ghi đã bị xóa. Tải lại danh sách trước khi tiếp tục.")
                self._require_editable(current)
                if current.status != obj.status and "status" not in form.changed_data:
                    raise ValidationError("Trạng thái đã thay đổi. Tải lại trang trước khi lưu.")
            return super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj is None:
            return True
        qs = self.model.all_objects.filter(pk=obj.pk)
        if request.method == "POST" and connection.in_atomic_block:
            qs = qs.select_for_update()
        current = qs.first()
        return bool(current and current.status in self.editable_statuses)

    def delete_model(self, request, obj):
        with transaction.atomic():
            self._require_editable(self._locked_current(obj))
            return super().delete_model(request, obj)
