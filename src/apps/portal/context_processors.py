from apps.notification.models import Notification
from apps.activity.models import ActivityProposal
from apps.security.permissions import get_role_name, has_permission, permission_flags
from django.conf import settings


def ui_palette(request):
    """Dải màu giao diện do máy chủ chọn (UI_PALETTE) — gắn vào thẻ <html>.

    Không có nút chọn cho từng người dùng: giá trị chỉ đến từ cấu hình máy chủ.
    """
    return {"ui_palette": settings.UI_PALETTE}


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
    can_approve_proposals = has_permission(request.user, "approve_activity_proposals")
    pending_proposal_count = (
        ActivityProposal.objects.filter(approver=request.user, status="Submitted").count()
        if can_approve_proposals else 0
    )
    context.update({
        "synthetic_demo": getattr(settings, "SYNTHETIC_DEMO", False),
        # Các tên cũ đang dùng trong giao diện, giữ lại để không phải sửa template
        "can_approve": context["can_approve_leave"],
        "is_admin_user": context["can_view_admin_menu"],
        "user_role_name": get_role_name(request.user),
        "unread_notification_count": unread_count,
        "can_approve_activity_proposals": can_approve_proposals,
        "pending_activity_proposal_count": pending_proposal_count,
    })
    return context
