from django.contrib import admin

from apps.common.admin import BaseAuditAdmin
from apps.assistant.models import SearchQueryLog


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(BaseAuditAdmin):
    """
    Nhật ký truy vấn trợ lý: chỉ đọc, không tạo/sửa/xóa từ Admin.

    RBAC là bắt buộc cho mọi trang Admin trong hệ thống (xem docstring của
    `RoleBasedAdminMixin` trong `apps/common/admin.py`), nên kế thừa
    `BaseAuditAdmin` thay vì `admin.ModelAdmin` trơn. `BaseAuditAdmin` cũng
    cung cấp sẵn `exclude` các cột audit (created_by/modified_by/deleted_by/
    deleted_date/is_deleted) và gỡ action `delete_selected`.

    `question` là văn bản tự do của người dùng nên chỉ SUPER_ADMIN được xem;
    không cấp `view_roles` rộng để tránh lộ nội dung truy vấn toàn công ty.
    """

    view_roles = ("SUPER_ADMIN",)

    list_display = ("user", "question", "result_count", "sources", "took_ms", "created_date")
    search_fields = ("question",)
    list_filter = ("sources",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
