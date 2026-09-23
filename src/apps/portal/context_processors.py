from apps.notification.models import Notification
from apps.security.permissions import get_role_name, permission_flags


def user_permissions(request):
    """Đưa quyền của người đang đăng nhập ra template (dùng để ẩn/hiện menu).

    Danh sách quyền lấy từ apps/security/permissions.py — không khai báo lại ở đây.
    """
    if not request.user.is_authenticated:
        return {}

    employee = getattr(request.user, "employee", None)
    unread_count = (
        Notification.objects.filter(employee=employee, is_read=False).count() if employee else 0
    )

    context = permission_flags(request.user)
    context.update({
        # Các tên cũ đang dùng trong giao diện, giữ lại để không phải sửa template
        "can_approve": context["can_approve_leave"],
        "is_admin_user": context["can_view_admin_menu"],
        "user_role_name": get_role_name(request.user),
        "unread_notification_count": unread_count,
    })
    return context
