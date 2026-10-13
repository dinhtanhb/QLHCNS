"""Bounded read-only phase-two blocks; authorization precedes query construction."""
from datetime import datetime, time, timedelta

from django.db.models import BooleanField, Case, Count, Exists, F, OuterRef, Q, Value, When, Window
from django.db.models.functions import RowNumber
from django.urls import reverse
from django.utils import timezone

from apps.document.models import PersonnelDecision, PersonnelDecisionHistory
from apps.leave.models import LeaveRequest
from apps.recruitment.models import Candidate, JobPosting, RecruitmentRequest
from apps.security.data_access import managed_departments_for
from apps.security.permissions import HR_MANAGER, get_role_code, has_permission


def created_window(today):
    zone = timezone.get_current_timezone()
    return (timezone.make_aware(datetime.combine(today - timedelta(days=29), time.min), zone),
            timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min), zone))


def recent_leave(user, today, employee=None):
    start, end = created_window(today)
    qs = LeaveRequest.objects.filter(employee__is_deleted=False, leave_type__is_deleted=False,
        employee__department__is_deleted=False, created_date__gte=start, created_date__lt=end)
    if employee is not None:
        qs = qs.filter(employee_id=employee.pk)
    fields = ['pk', 'from_date', 'to_date', 'total_days', 'status']
    detailed = has_permission(user, 'manage_hr')
    if detailed: fields.append('leave_type__leave_type_name')
    if employee is None: fields.extend(('employee__full_name', 'employee__employee_code'))
    rows = list(qs.order_by('-created_date', '-pk').values(*fields)[:6])
    for row in rows:
        row['type_label'] = row.pop('leave_type__leave_type_name') if detailed else 'Nghỉ phép'
    return dict(state='ready', rows=rows, title='Đơn nghỉ gần đây của tôi' if employee else 'Đơn nghỉ gần đây toàn Trung tâm',
        href=reverse('portal:leave_list') if employee else None, global_scope=employee is None)


def status_counts(queryset, choices):
    counts = {row['status']: row['value'] for row in queryset.values('status').annotate(value=Count('pk')).order_by('status')}
    return [dict(code=code, label=label, value=counts.get(code, 0)) for code, label in choices]


def recent_leave_pair(user, employee, today):
    """Two independently bounded lists in one SELECT, even for a superuser.

    Global rank selects the six newest; partitioned rank independently selects
    the employee's six newest, including those outside the global first six.
    Django's window-filter wrapper works on both supported database backends.
    """
    start, end = created_window(today)
    order = [F('created_date').desc(), F('pk').desc()]
    qs = LeaveRequest.objects.filter(employee__is_deleted=False, leave_type__is_deleted=False,
        employee__department__is_deleted=False, created_date__gte=start, created_date__lt=end).annotate(
            global_rank=Window(RowNumber(), order_by=order),
            own_rank=Window(RowNumber(), partition_by=[F('employee_id')], order_by=order))
    qs = qs.filter(Q(global_rank__lte=6) | Q(employee_id=employee.pk, own_rank__lte=6))
    detailed = has_permission(user, 'manage_hr')
    fields = ['pk','employee_id','employee__full_name','employee__employee_code',
              'from_date','to_date','total_days','status','global_rank','own_rank']
    if detailed: fields.append('leave_type__leave_type_name')
    records = list(qs.order_by('-created_date','-pk').values(*fields))
    own, global_rows = [], []
    for record in records:
        row = dict(record)
        own_employee = row.pop('employee_id') == employee.pk
        global_rank = row.pop('global_rank')
        own_rank = row.pop('own_rank')
        row['type_label'] = row.pop('leave_type__leave_type_name') if detailed else 'Nghỉ phép'
        if global_rank <= 6: global_rows.append(row)
        if own_employee and own_rank <= 6:
            own_row = dict(row)
            own_row.pop('employee__full_name'); own_row.pop('employee__employee_code')
            own.append(own_row)
    return dict(state='ready', own=dict(state='ready', rows=own, global_scope=False, href=reverse('portal:leave_list')),
        global_leave=dict(state='ready', rows=global_rows, global_scope=True, href=None))


def postings():
    value = JobPosting.objects.filter(status='Open', recruitment_request__is_deleted=False,
        recruitment_request__department__is_deleted=False, recruitment_request__position__is_deleted=False).count()
    return dict(state='ready', label='Tin có trạng thái đang tuyển', value=value, icon='document',
        note='Theo trạng thái Open, chưa xét ngày đóng', rows=[], href=None)


def candidates():
    # Hired is a model status, not proof of employment or a date of recruitment.
    choices = [(code, 'Trạng thái Hired' if code == 'Hired' else label) for code, label in Candidate.STATUS_CHOICES]
    rows = status_counts(Candidate.objects.all(), choices)
    return dict(state='ready', label='Ứng viên đang xử lý', value=sum(row['value'] for row in rows[:4]),
        icon='people', rows=rows, note='Bốn nhóm đang xử lý; trạng thái hiện tại', href=None,
        cta=reverse('portal:hr_candidate_list'), cta_label='Mở danh sách ứng viên')


def requests(user):
    qs = RecruitmentRequest.objects.filter(department__in=managed_departments_for(user, global_roles=(HR_MANAGER,)))
    choices = [(code, 'Trạng thái Closed' if code == 'Closed' else label) for code, label in RecruitmentRequest.STATUS_CHOICES]
    rows = status_counts(qs, choices)
    label = 'Đề xuất tuyển dụng của phòng tôi' if get_role_code(user) == 'DEPT_MANAGER' and not user.is_superuser else 'Đề xuất tuyển dụng'
    return dict(state='ready', label=label, value=sum(row['value'] for row in rows), rows=rows,
        icon='briefcase', note='Trạng thái hiện tại', href=None,
        cta=reverse('portal:recruitment_list'), cta_label='Mở danh sách đề xuất')


def history(user, today):
    decisions = PersonnelDecision.objects.filter(employee__is_deleted=False, employee__department__is_deleted=False)
    can_manage = has_permission(user, 'manage_hr')
    if not can_manage:
        # The destination uses the reverse relation, including legacy soft-deleted
        # actor events. Mirror that exact visibility rule without loading actors.
        own_history = PersonnelDecisionHistory.all_objects.filter(decision_id=OuterRef('pk'), created_by_id=user.pk)
        decisions = decisions.alias(own_history=Exists(own_history)).filter(Q(status='PendingApproval') | Q(own_history=True))
    start, end = created_window(today)
    qs = PersonnelDecisionHistory.objects.filter(decision__in=decisions, created_date__gte=start, created_date__lt=end)
    fields = ['pk', 'decision_id', 'decision__decision_no', 'created_date', 'action', 'status_to']
    if not can_manage:
        # List visibility joins all actor history; detail uses live related
        # history. Evaluate the stricter detail guard inside this same SELECT.
        own_live = PersonnelDecisionHistory.objects.filter(decision_id=OuterRef('decision_id'), created_by_id=user.pk)
        qs = qs.alias(own_live=Exists(own_live)).annotate(can_open_detail=Case(When(
            Q(decision__status='PendingApproval') | Q(own_live=True) |
            Q(decision__status='Issued', decision__employee_id=user.employee_id), then=Value(True)),
            default=Value(False), output_field=BooleanField()))
        fields.append('can_open_detail')
    rows = list(qs.order_by('-created_date', '-pk').values(*fields)[:8])
    labels = dict(PersonnelDecisionHistory.ACTION_CHOICES)
    for row in rows:
        row['action_label'] = labels.get(row['action'], row['action'])
        can_open = row.pop('can_open_detail', can_manage)
        row['href'] = reverse('portal:personnel_decision_detail', args=[row['decision_id']]) if can_open else None
    return dict(state='ready', rows=rows)


def phase2_sections(user, employee, today, read_block):
    result = {}
    linked = employee is not None and not employee.is_deleted
    global_leave = has_permission(user, 'approve_leave_all_departments')
    if linked and global_leave:
        pair = read_block(lambda: recent_leave_pair(user, employee, today))
        result['own_leave'] = pair.get('own', pair)
        result['global_leave'] = pair.get('global_leave', pair)
    elif linked:
        result['own_leave'] = read_block(lambda: recent_leave(user, today, employee))
    elif global_leave:
        result['global_leave'] = read_block(lambda: recent_leave(user, today))
    if has_permission(user, 'view_reports'):
        result['postings'] = read_block(postings)
    if has_permission(user, 'manage_hr'):
        result['candidates'] = read_block(candidates)
    if has_permission(user, 'manage_hr') or has_permission(user, 'approve_personnel_decision'):
        result['history'] = read_block(lambda: history(user, today))
    if (has_permission(user, 'request_recruitment') or has_permission(user, 'approve_recruitment')) and (
        user.is_superuser or get_role_code(user) == HR_MANAGER or linked
    ):
        result['requests'] = read_block(lambda: requests(user))
    if any(has_permission(user, permission) for permission in ('manage_hr', 'request_recruitment', 'approve_recruitment')):
        if 'postings' in result:
            result['postings'].update(cta=reverse('portal:recruitment_hub'), cta_label='Mở tuyển dụng')
    return result
