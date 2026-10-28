from hashlib import sha256

from django.db import transaction

from .models import Notification, NotificationEmailOutbox


def notify_many(employees, notification_type, title, message, link=None, created_by=None):
    """Create notices in batches without inserting once per employee."""
    employee_ids = dict.fromkeys(employee.pk for employee in employees if employee)
    notifications = Notification.objects.bulk_create([
        Notification(employee_id=pk, notification_type=notification_type, title=title,
                     message=message, link=link or '', created_by=created_by)
        for pk in employee_ids
    ], batch_size=100)
    from apps.mobile.push import after_notification
    after_notification(tuple(employee_ids))
    return notifications


def notify(employee, notification_type, title, message, link=None, created_by=None):
    """Tạo 1 thông báo cho 1 nhân viên. Gọi hàm này ở bất kỳ đâu cần báo tin."""
    if not employee:
        return None
    notification = Notification.objects.create(
        employee=employee,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link or "",
        created_by=created_by,
    )
    from apps.mobile.push import after_notification
    after_notification((employee.pk,))
    return notification


@transaction.atomic
def notify_with_email_draft(
    employee, notification_type, title, message, link, email_subject, email_body,
    created_by=None, idempotency_key=None,
):
    """Create an in-app notice and, if an address exists, an Outlook mail draft.

    Mail is never sent by the server. Locking the employee row serializes duplicate
    event handling for this recipient; the unique key remains the final DB guard.
    """
    if not employee:
        return None, None

    from apps.hrm.models import Employee

    recipient = Employee.objects.select_for_update().get(pk=employee.pk)
    raw_key = idempotency_key or f"{notification_type}:{link or ''}:{recipient.pk}"
    if len(raw_key) > 200:
        raw_key = f"{notification_type[:40]}:{sha256(raw_key.encode('utf-8')).hexdigest()}"

    email = (recipient.company_email or recipient.personal_email or "").strip()
    existing = NotificationEmailOutbox.objects.filter(idempotency_key=raw_key).select_related(
        "notification"
    ).first() if email else None
    if existing:
        return existing.notification, existing

    notification = notify(recipient, notification_type, title, message, link, created_by)
    if not email:
        return notification, None

    outbox, _ = NotificationEmailOutbox.objects.get_or_create(
        idempotency_key=raw_key,
        defaults={
            "notification": notification,
            "recipient_email": email,
            "subject": email_subject,
            "body_text": email_body,
            "status": "Draft",
            "created_by": created_by,
        },
    )
    if outbox.notification_id != notification.pk:
        notification.delete()
        notification = outbox.notification
    return notification, outbox
