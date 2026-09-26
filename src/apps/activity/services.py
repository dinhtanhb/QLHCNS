"""Use cases for project activity tracking, reports and reminders."""
from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from apps.common.email_draft import build_mailto_url


ACTIVITY_REPORT_DEADLINE_WORKING_DAYS = 10
DEFAULT_REMINDER_OFFSETS = (3, 1, 0)


def _holiday_dates(start_date, end_date):
    from apps.attendance.models import Holiday

    return set(
        Holiday.objects.filter(
            is_active=True,
            holiday_date__gt=start_date,
            holiday_date__lte=end_date,
        ).values_list("holiday_date", flat=True)
    )


def is_company_workday(day, holidays=None):
    """Use the existing company convention: Monday–Friday, excluding holidays."""
    if holidays is None:
        holidays = _holiday_dates(day - timedelta(days=1), day)
    return day.weekday() < 5 and day not in holidays


def add_company_workdays(start_date, number_of_days):
    """Return the date after N company workdays; the start date is day zero."""
    if number_of_days < 0:
        raise ValueError("number_of_days must be non-negative")
    if number_of_days == 0:
        return start_date

    # Ten business days normally span two weeks. The extra margin covers
    # consecutive public holidays without repeated database queries.
    end_date = start_date + timedelta(days=number_of_days * 4 + 31)
    holidays = _holiday_dates(start_date, end_date)
    current = start_date
    counted = 0
    while counted < number_of_days:
        current += timedelta(days=1)
        if is_company_workday(current, holidays):
            counted += 1
    return current


def company_workdays_between(start_date, end_date):
    """Count company workdays strictly after start_date and through end_date."""
    if end_date <= start_date:
        return 0
    holidays = _holiday_dates(start_date, end_date)
    day = start_date + timedelta(days=1)
    count = 0
    while day <= end_date:
        if is_company_workday(day, holidays):
            count += 1
        day += timedelta(days=1)
    return count


def find_schedule_conflicts(employee_id, start_date, end_date, exclude_activity_id=None):
    """Find overlapping activity date ranges for one CBDA."""
    from apps.activity.models import Activity

    qs = Activity.objects.filter(
        lead_cbda_id=employee_id,
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).exclude(status="Cancelled")
    if exclude_activity_id:
        qs = qs.exclude(pk=exclude_activity_id)
    return list(qs)


@transaction.atomic
def create_task_for_activity(activity):
    """Create exactly one report task after an issued dispatch is linked.

    An OfficialDispatch of type Outgoing is the issued record in the current system. The
    activity's coordinator (or the dispatch signer) is the task assigner.
    """
    from apps.notification.services import notify
    from apps.task.models import Task

    if not activity.outgoing_document_id:
        raise ValueError("Cần gắn công văn đi đã phát hành trước khi tạo Task báo cáo.")
    if activity.status == "Cancelled":
        return None, False

    dispatch = activity.outgoing_document
    if dispatch.dispatch_type != "Outgoing":
        raise ValueError("Chỉ có thể tạo Task từ Công văn đi.")
    due_date = add_company_workdays(activity.end_date, ACTIVITY_REPORT_DEADLINE_WORKING_DAYS)
    existing = Task.objects.filter(activity=activity).first()
    if existing:
        if existing.status == "Cancelled":
            return existing, False
        schedule_changed = (
            existing.start_date != activity.start_date or existing.due_date != due_date
        )
        if not schedule_changed:
            return existing, False

        update_fields = []
        if existing.start_date != activity.start_date:
            existing.start_date = activity.start_date
            update_fields.append("start_date")
        if existing.due_date != due_date:
            existing.due_date = due_date
            update_fields.append("due_date")

        reopened = (
            existing.status == "Done"
            and (existing.completed_date is None or existing.completed_date < activity.end_date)
        )
        if reopened:
            # A report marked complete before the rescheduled activity ends cannot
            # satisfy the new schedule. Detach the old report without deleting it
            # from SharePoint so the assignee can upload the current report later.
            existing.status = "Todo"
            existing.completed_date = None
            existing.report_file = None
            update_fields.extend(("status", "completed_date", "report_file"))

        update_fields.append("modified_date")
        existing.save(update_fields=update_fields)
        _notify_task_schedule_changed(existing, activity, due_date, reopened=reopened)
        return existing, False

    start_date = activity.start_date
    task_code = f"ACT-{activity.pk}-REPORT"
    task, created = Task.objects.get_or_create(
        task_code=task_code,
        defaults={
            "task_name": f"Báo cáo hoạt động: {activity.activity_name}",
            "description": (
                f"Triển khai và nộp báo cáo cho hoạt động '{activity.activity_name}' "
                f"(mã {activity.activity_code}), dự án {activity.project.project_name}. "
                f"Địa điểm: {activity.location or '(chưa ghi)'}."
            ),
            "assigned_by_employee": activity.coordinator or dispatch.signer,
            "assigned_to_employee": activity.lead_cbda,
            "department": activity.project.department,
            "priority": "High",
            "start_date": start_date,
            "due_date": due_date,
            "status": "Todo",
            "activity": activity,
            "created_by": activity.created_by,
        },
    )
    if task.activity_id != activity.pk:
        raise ValueError(f"Mã công việc {task_code} đang được dùng bởi hoạt động khác.")

    if created:
        _notify_task_assigned(task, activity, due_date)
    return task, created


def _notify_task_schedule_changed(task, activity, due_date, *, reopened=False):
    from apps.notification.services import notify

    message = (
        f"{activity.activity_name}: thời gian hoạt động {activity.start_date:%d/%m/%Y}–"
        f"{activity.end_date:%d/%m/%Y}; hạn báo cáo {due_date:%d/%m/%Y}."
    )
    if reopened:
        message += " Task được mở lại vì lịch mới kết thúc sau ngày hoàn thành trước đó. Vui lòng nộp báo cáo theo lịch mới."

    recipients = [task.assigned_to_employee]
    if task.assigned_by_employee_id != task.assigned_to_employee_id:
        recipients.append(task.assigned_by_employee)
    for employee in recipients:
        notify(
            employee=employee,
            notification_type="ActivityTaskScheduleChanged",
            title="Lịch Task báo cáo hoạt động đã thay đổi",
            message=message,
            link=f"/portal/tasks/{task.pk}/",
            created_by=activity.modified_by,
        )


def _notify_task_assigned(task, activity, due_date):
    from apps.notification.services import notify

    notify(
        employee=activity.lead_cbda,
        notification_type="ActivityTaskAssigned",
        title="Công việc hoạt động mới được giao",
        message=(
            f"Bạn được giao báo cáo hoạt động '{activity.activity_name}'. "
            f"Hạn hoàn thành: {due_date.strftime('%d/%m/%Y')}."
        ),
        link=f"/portal/tasks/{task.pk}/",
        created_by=activity.created_by,
    )
    coordinator = activity.coordinator
    if coordinator and coordinator.pk != activity.lead_cbda_id:
        notify(
            employee=coordinator,
            notification_type="ActivityTaskAssigned",
            title="Đã giao việc báo cáo hoạt động",
            message=(
                f"Công việc '{activity.activity_name}' đã được giao cho "
                f"{activity.lead_cbda}. Hạn: {due_date.strftime('%d/%m/%Y')}."
            ),
            link=f"/portal/tasks/{task.pk}/",
            created_by=activity.created_by,
        )


def send_activity_report_reminders(today=None):
    """Create idempotent in-app reminders for activity report tasks."""
    from apps.notification.models import Notification
    from apps.task.models import Task
    from apps.notification.services import notify

    today = today or timezone.localdate()
    if not is_company_workday(today):
        return 0

    offsets = set(getattr(settings, "ACTIVITY_TASK_REMINDER_OFFSETS", DEFAULT_REMINDER_OFFSETS))
    tasks = Task.objects.filter(
        activity__isnull=False,
        due_date__isnull=False,
    ).exclude(status__in=("Done", "Cancelled")).select_related(
        "assigned_to_employee", "activity", "assigned_by_employee"
    )
    sent = 0
    for task in tasks:
        if task.due_date < today:
            reminder_key = "overdue"
        else:
            remaining = company_workdays_between(today, task.due_date)
            if remaining not in offsets:
                continue
            reminder_key = f"due-{remaining}"

        link = f"/portal/tasks/{task.pk}/"
        already_sent = Notification.objects.filter(
            employee=task.assigned_to_employee,
            notification_type="ActivityReportReminder",
            link=link,
            created_date__date=today,
        ).exists()
        if already_sent:
            continue

        if reminder_key == "overdue":
            title = "Báo cáo hoạt động đã quá hạn"
            message = f"{task.task_name} đã quá hạn từ {task.due_date:%d/%m/%Y}; vui lòng cập nhật tiến độ."
        elif reminder_key == "due-0":
            title = "Hạn báo cáo hoạt động là hôm nay"
            message = f"{task.task_name} đến hạn hôm nay; vui lòng hoàn thành và tải báo cáo lên SharePoint."
        else:
            title = "Sắp đến hạn báo cáo hoạt động"
            message = f"{task.task_name} còn {reminder_key[4:]} ngày làm việc; vui lòng cập nhật tiến độ."

        notify(
            employee=task.assigned_to_employee,
            notification_type="ActivityReportReminder",
            title=title,
            message=message,
            link=link,
        )
        sent += 1
    return sent


def _user_email(user):
    employee = getattr(user, "employee", None)
    return (getattr(employee, "company_email", "") or getattr(user, "email", "") or "").strip()


def build_activity_proposal_email_draft(package, approver, sender, approval_url=""):
    """Build a mailto draft for the coordinator to review and send in Outlook."""
    recipient = _user_email(approver)
    if not recipient:
        raise ValueError("Tài khoản Giám đốc chưa có email công ty để nhận hồ sơ.")
    if not package.has_required_files():
        raise ValueError("Cần tải đủ 2 tệp PDF: đề xuất hoạt động và dự trù kinh phí.")

    activity = package.activity
    subject = f"Xin phê duyệt đề xuất hoạt động: {activity.activity_code} - {activity.activity_name}"
    body = (
        f"Kính gửi Giám đốc dự án,\n\n"
        f"Điều phối viên {sender.get_full_name() or sender.username} gửi hồ sơ đề xuất hoạt động "
        f"{activity.activity_code} - {activity.activity_name}, dự án {activity.project.project_name}, "
        f"phiên bản {package.version}.\n"
        "Hồ sơ gồm 2 tệp PDF: Đề xuất hoạt động và Dự trù kinh phí.\n"
        f"Mở hồ sơ và ghi nhận quyết định tại: {approval_url}\n\n"
        "Vui lòng xem xét và phản hồi quyết định trên IHRMS."
    )
    return {
        "recipient": recipient,
        "sender_email": _user_email(sender),
        "subject": subject,
        "body": body,
        "mailto_url": build_mailto_url(recipient, subject, body),
    }
