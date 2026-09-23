from .models import Notification


def notify(employee, notification_type, title, message, link=None, created_by=None):
    """Tạo 1 thông báo cho 1 nhân viên. Gọi hàm này ở bất kỳ đâu cần báo tin."""
    if not employee:
        return None
    return Notification.objects.create(
        employee=employee,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link or "",
        created_by=created_by,
    )