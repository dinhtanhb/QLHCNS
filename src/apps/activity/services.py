"""Use cases for project activity tracking, reports and reminders."""
from __future__ import annotations

from datetime import timedelta
from pathlib import PurePosixPath

from django.conf import settings
from django.db import transaction
from django.utils import timezone


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

    existing = Task.objects.filter(activity=activity).first()
    if existing:
        return existing, False

    dispatch = activity.outgoing_document
    if dispatch.dispatch_type != "Outgoing":
        raise ValueError("Chỉ có thể tạo Task từ Công văn đi.")
    issued_date = dispatch.received_or_sent_date
    due_date = add_company_workdays(issued_date, ACTIVITY_REPORT_DEADLINE_WORKING_DAYS)
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
            "start_date": issued_date,
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


def send_activity_proposal_for_approval(package, approver, sender, approval_url=""):
    """Email the paired PDF files; report success only after Graph accepts the request."""
    from apps.m365.graph_client import GraphNotConfigured, get_graph_client

    mailbox = getattr(settings, "M365_MAIL_SENDER", "").strip()
    recipient = _user_email(approver)
    if not mailbox:
        raise GraphNotConfigured("Thiếu M365_MAIL_SENDER trong .env; chưa gửi email.")
    if not recipient:
        raise ValueError("Tài khoản Giám đốc chưa có email công ty để nhận hồ sơ.")
    if not package.has_required_files():
        raise ValueError("Cần tải đủ 2 tệp Excel và 2 tệp PDF trước khi gửi.")

    attachments = []
    total_bytes = 0
    for file_field in (package.proposal_pdf, package.budget_pdf):
        with file_field.open("rb") as uploaded:
            content = uploaded.read()
        total_bytes += len(content)
        attachments.append({
            "name": PurePosixPath(file_field.name).name,
            "content_type": "application/pdf",
            "content": content,
        })
    # Graph's simple JSON attachment endpoint is intended for small attachments.
    if total_bytes > 2_500_000:
        raise ValueError("Tổng dung lượng hai PDF vượt 2,5 MB; hãy nén PDF trước khi gửi.")

    activity = package.activity
    subject = f"Xin phê duyệt đề xuất hoạt động: {activity.activity_code} - {activity.activity_name}"
    body = (
        f"Kính gửi Giám đốc dự án,\n\n"
        f"Điều phối viên {sender.get_full_name() or sender.username} gửi hồ sơ đề xuất hoạt động "
        f"{activity.activity_code} - {activity.activity_name}, dự án {activity.project.project_name}, "
        f"phiên bản {package.version}.\n"
        "Hồ sơ gồm Đề xuất hoạt động và Dự trù kinh phí (PDF); các tệp Excel gốc được lưu trong IHRMS/SharePoint.\n"
        f"Mở hồ sơ và ghi nhận quyết định tại: {approval_url}\n\n"
        "Vui lòng phản hồi quyết định trên IHRMS."
    )
    get_graph_client().send_mail(mailbox, recipient, subject, body, attachments)
    return recipient
