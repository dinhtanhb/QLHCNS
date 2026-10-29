"""Versioned JSON transport over existing IHRMS permissions and leave commands."""
from datetime import timedelta
from functools import wraps
import json
import time

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.password_validation import validate_password, password_changed
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from apps.attendance.models import Attendance
from apps.hrm.models import Employee, EmployeeProfileChangeRequest
from apps.leave.models import LeaveBalance, LeaveType
from apps.leave.services import decide_leave, employee_for, submit_leave
from apps.notification.models import Notification
from apps.portal.selectors import approvable_leave_requests
from apps.security.data_access import visible_leave_requests_for
from apps.security.permissions import get_role_code, has_permission

def reply(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def endpoint(*methods, anonymous=False):
    def decorate(view):
        @csrf_exempt  # Cookie authentication is rejected in MobileSessionMiddleware.
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method not in methods:
                response = reply({'error': 'Phương thức không được hỗ trợ.'}, 405)
                response['Allow'] = ', '.join(methods)
                return response
            if not anonymous and not request.user.is_authenticated:
                return reply({'error': 'Phiên đã hết hạn. Vui lòng đăng nhập lại.'}, 401)
            try:
                if request.method == 'POST':
                    if request.content_type != 'application/json':
                        return reply({'error': 'Yêu cầu phải dùng JSON.'}, 415)
                    if len(request.body) > 16_384:
                        return reply({'error': 'Yêu cầu quá lớn.'}, 413)
                    request.mobile_data = json.loads(request.body or b'{}')
                    if not isinstance(request.mobile_data, dict):
                        raise ValueError
                return view(request, *args, **kwargs)
            except (ValueError, TypeError, UnicodeError, OverflowError):
                return reply({'error': 'Dữ liệu không hợp lệ.'}, 400)
            except ValidationError as exc:
                return reply({'error': '; '.join(exc.messages)}, 400)
            except PermissionDenied as exc:
                return reply({'error': str(exc) or 'Không có quyền truy cập.'}, 403)
            except Http404:
                return reply({'error': 'Không tìm thấy dữ liệu trong phạm vi được phép.'}, 404)
        return wrapped
    return decorate


def text(data, key, *, limit, required=False):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValidationError(f'Trường {key} không hợp lệ.')
    return value


def page(request, queryset, serialize):
    number = int(request.GET.get('page', '1'))
    if number < 1 or number > 100_000:
        raise ValueError
    result = Paginator(queryset, 30).get_page(number)
    return reply({'items': [serialize(obj) for obj in result],
                  'page': result.number, 'has_next': result.has_next(),
                  'count': result.paginator.count})


def leave_row(leave):
    return {'id': leave.pk, 'employee_name': leave.employee.full_name,
        'leave_type': leave.leave_type.leave_type_name, 'from_date': leave.from_date,
        'to_date': leave.to_date, 'total_days': leave.total_days, 'reason': leave.reason or '',
        'status': leave.status, 'status_label': leave.get_status_display()}


@sensitive_post_parameters('password')
@endpoint('POST', anonymous=True)
def login(request):
    username = text(request.mobile_data, 'username', limit=150, required=True)
    password = text(request.mobile_data, 'password', limit=1024, required=True)
    # Authenticate through Axes + ModelBackend, exactly as portal/admin do.
    user = auth.authenticate(request, username=username, password=password)
    if user is None:
        locked = getattr(request, 'axes_locked_out', False)
        return reply({'error': 'Đăng nhập tạm bị khóa. Vui lòng thử lại sau.' if locked
                      else 'Tên đăng nhập hoặc mật khẩu không đúng.'}, 429 if locked else 401)
    # A login always creates a distinct session, even if a bearer was supplied.
    request.session.flush()
    auth.login(request, user)
    expires = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
    request.session['mobile_session'] = True
    request.session['security_last_activity'] = int(time.time())
    request.session.set_expiry(expires)
    request.session.save()
    return reply({'token': request.session.session_key, 'expires_at': expires,
                  'idle_timeout': settings.SESSION_IDLE_TIMEOUT})


@endpoint('POST')
def logout(request):
    auth.logout(request)
    return reply({'ok': True})


@sensitive_post_parameters('old_password', 'new_password', 'confirm_password')
@endpoint('POST')
def change_password(request):
    data = request.mobile_data
    old = text(data, 'old_password', limit=1024, required=True)
    new = text(data, 'new_password', limit=1024, required=True)
    confirm = text(data, 'confirm_password', limit=1024, required=True)
    user = auth.authenticate(request, username=request.user.username, password=old)
    if user is None:
        return reply({'error': 'Mật khẩu hiện tại không đúng hoặc tài khoản tạm bị khóa.'}, 400)
    if new != confirm:
        raise ValidationError('Hai mật khẩu mới chưa khớp.')
    if old == new:
        raise ValidationError('Mật khẩu mới phải khác mật khẩu hiện tại.')
    validate_password(new, user)
    user.set_password(new)
    user.save(update_fields=['password'])
    password_changed(new, user)
    auth.logout(request)
    return reply({'ok': True})


@endpoint('GET', 'POST')
def profile_requests(request):
    employee = employee_for(request.user)
    if not employee or not has_permission(request.user, 'submit_profile_change_request'):
        raise PermissionDenied('Tài khoản không có quyền gửi yêu cầu cập nhật hồ sơ.')
    if request.method == 'POST':
        field = text(request.mobile_data, 'field_name', limit=50, required=True)
        if field not in EmployeeProfileChangeRequest.ALLOWED_FIELDS:
            raise PermissionDenied('Trường hồ sơ không được phép cập nhật.')
        value = text(request.mobile_data, 'new_value', limit=500).strip()
        if field == 'mobile_phone' and not value:
            raise ValidationError('Số điện thoại không được để trống.')
        employee._meta.get_field(field).clean(value, employee)
        with transaction.atomic():
            employee = Employee.objects.select_for_update().get(pk=employee.pk)
            if EmployeeProfileChangeRequest.objects.filter(employee=employee, field_name=field,
                    new_value=value, status='Pending').exists():
                raise ValidationError('Yêu cầu này đang chờ Nhân sự duyệt.')
            item = EmployeeProfileChangeRequest(employee=employee, field_name=field,
                old_value=str(getattr(employee, field) or ''), submitted_snapshot=str(getattr(employee, field) or ''),
                new_value=value, reason=text(request.mobile_data, 'reason', limit=500).strip(), created_by=request.user)
            item.full_clean()
            item.save()
        return reply({'ok': True}, 201)
    return page(request, EmployeeProfileChangeRequest.objects.filter(employee=employee).order_by('-created_date', '-pk'),
        lambda row: {'id': row.pk, 'field_label': row.get_field_name_display(), 'new_value': row.new_value,
                     'status_label': row.get_status_display(), 'decision_note': row.decision_note or ''})


@endpoint('GET')
def me(request):
    user = request.user
    employee = employee_for(user)
    profile = None
    if employee:
        profile = {'employee_code': employee.employee_code, 'full_name': employee.full_name,
            'department': str(employee.department), 'position': str(employee.position),
            'company_email': employee.company_email or '', 'join_date': employee.join_date}
        profile.update({field: getattr(employee, field) or '' for field in EmployeeProfileChangeRequest.ALLOWED_FIELDS})
    return reply({'username': user.username, 'role': get_role_code(user), 'profile': profile,
        'can_approve': has_permission(user, 'approve_leave') and employee is not None,
        'can_manage_hr': has_permission(user, 'manage_hr'),
        'can_request_profile_change': employee is not None and has_permission(user, 'submit_profile_change_request'),
        'can_approve_profile_change': has_permission(user, 'approve_profile_change_request'),
        'palette': settings.UI_PALETTE})


@endpoint('GET')
def my_profile(request):
    employee = employee_for(request.user)
    if not employee:
        return reply({'profile': None, 'salary': None, 'contract': None})
    salary = employee.salaries.filter(status='Active').order_by('-effective_date').first()
    contract = employee.contracts.select_related('contract_type').order_by('-start_date').first()
    return reply({'profile': {
        'full_name': employee.full_name, 'employee_code': employee.employee_code,
        'date_of_birth': employee.date_of_birth, 'gender': employee.get_gender_display(),
        'department': str(employee.department), 'position': str(employee.position),
        'manager': employee.manager.full_name if employee.manager else '',
        'company_email': employee.company_email, 'personal_email': employee.personal_email or '',
        'mobile_phone': employee.mobile_phone, 'address': employee.address or '',
        'join_date': employee.join_date, 'employment_status': employee.get_employment_status_display()},
        'salary': {'basic': str(salary.current_basic_salary), 'effective_date': salary.effective_date} if salary else None,
        'contract': {'number': contract.contract_no, 'type': str(contract.contract_type),
                     'start_date': contract.start_date, 'end_date': contract.end_date} if contract else None})


@endpoint('GET')
def profile_history(request):
    employee = employee_for(request.user)
    if not employee:
        raise PermissionDenied('Tài khoản chưa có hồ sơ nhân viên.')
    kind = request.GET.get('kind', 'transfers')
    sources = {
        'transfers': (employee.transfers.select_related('from_department', 'to_department'), 'effective_date',
                      lambda row: f'{row.from_department} → {row.to_department}'),
        'promotions': (employee.promotions.select_related('old_position', 'new_position'), 'effective_date',
                       lambda row: f'{row.old_position} → {row.new_position}'),
        'rewards': (employee.rewards.all(), 'reward_date', lambda row: str(row.reward_type)),
        'disciplines': (employee.disciplines.all(), 'discipline_date', lambda row: str(row.discipline_type)),
    }
    if kind not in sources:
        raise ValidationError('Loại lịch sử không hợp lệ.')
    qs, date_field, describe = sources[kind]
    return page(request, qs.order_by('-'+date_field, '-pk'), lambda row: {
        'id': row.pk, 'date': getattr(row, date_field), 'description': describe(row),
        'amount': str(row.amount) if kind == 'rewards' and row.amount is not None else None})


@endpoint('GET')
def organization(request):
    # Same directory fields and Active scope as the portal organization chart.
    return page(request, Employee.objects.filter(employment_status='Active').select_related(
        'department', 'position', 'manager').order_by('full_name', 'pk'), lambda row: {
            'id': row.pk, 'name': row.full_name, 'employee_code': row.employee_code,
            'department': str(row.department), 'position': str(row.position),
            'manager_id': row.manager_id if row.manager and row.manager.employment_status == 'Active' and not row.manager.is_deleted else None,
            'manager': row.manager.full_name if row.manager and row.manager.employment_status == 'Active' and not row.manager.is_deleted else ''})


@endpoint('GET')
def profile_approvals(request):
    if not has_permission(request.user, 'approve_profile_change_request'):
        raise PermissionDenied('Không có quyền duyệt cập nhật hồ sơ.')
    return page(request, EmployeeProfileChangeRequest.objects.filter(status='Pending').select_related('employee').order_by('created_date', 'pk'),
        lambda row: {'id': row.pk, 'employee_name': row.employee.full_name, 'field_label': row.get_field_name_display(),
                     'old_value': row.old_value, 'new_value': row.new_value, 'reason': row.reason or '',
                     'has_attachment': bool(row.attachment)})


@endpoint('POST')
def profile_decision(request, pk):
    from apps.hrm.services import decide_profile_change
    decide_profile_change(request.user, pk,
        text(request.mobile_data, 'decision', limit=20, required=True), text(request.mobile_data, 'note', limit=500))
    return reply({'ok': True})


@endpoint('GET')
def attendance(request):
    employee = employee_for(request.user)
    records = Attendance.objects.filter(employee=employee) if employee else Attendance.objects.none()
    return page(request, records.order_by('-attendance_date', '-pk'), lambda row: {
        'id': row.pk, 'date': row.attendance_date, 'check_in': row.check_in_time,
        'check_out': row.check_out_time, 'hours': row.working_hours,
        'status_label': row.get_status_display()})


@endpoint('GET')
def leave_options(request):
    employee = employee_for(request.user)
    year = timezone.localdate().year
    balance = LeaveBalance.objects.filter(employee=employee, year=year).first() if employee else None
    return reply({'types': list(LeaveType.objects.order_by('leave_type_name').values(
        'id', 'leave_type_name')), 'year': year,
        'annual_available': balance.available_annual_days if balance else None,
        'can_submit': employee is not None})


@endpoint('GET', 'POST')
def leaves(request):
    if request.method == 'POST':
        data = request.mobile_data
        # Never accept employee/status/days/created_by from the device.
        kind = data.get('leave_type')
        if isinstance(kind, bool) or not isinstance(kind, int) or kind < 1:
            raise ValidationError('Vui lòng chọn loại nghỉ.')
        leave = submit_leave(request.user, leave_type=kind,
            from_date=text(data, 'from_date', limit=10, required=True),
            to_date=text(data, 'to_date', limit=10, required=True),
            reason=text(data, 'reason', limit=500))
        return reply({'item': leave_row(leave), 'message': 'Đã gửi đơn xin nghỉ phép, chờ phê duyệt.'}, 201)
    qs = visible_leave_requests_for(request.user).select_related('employee', 'leave_type')
    return page(request, qs.order_by('-from_date', '-pk'), leave_row)


@endpoint('GET')
def approvals(request):
    if not has_permission(request.user, 'approve_leave') or not employee_for(request.user):
        raise PermissionDenied('Anh/chị không có quyền duyệt đơn nghỉ phép.')
    return page(request, approvable_leave_requests(request.user).order_by('from_date', 'pk'), leave_row)


@endpoint('POST')
def decision(request, pk):
    leave = decide_leave(request.user, pk, request.mobile_data.get('decision'))
    return reply({'item': leave_row(leave), 'message': 'Đã xử lý đơn nghỉ phép.'})


@endpoint('GET')
def notifications(request):
    employee = employee_for(request.user)
    qs = Notification.objects.filter(employee=employee) if employee else Notification.objects.none()
    return page(request, qs.order_by('-created_date', '-pk'), lambda row: {
        'id': row.pk, 'title': row.title, 'message': row.message,
        'is_read': row.is_read, 'created_at': row.created_date,
        'destination': 'approvals' if row.link == '/portal/leave/approvals/' else
                       'leaves' if row.link == '/portal/leave/' else
                       'profile-requests' if row.link == '/portal/profile/requests/' else None})


@endpoint('POST')
def notification_read(request, pk):
    employee = employee_for(request.user)
    if not employee:
        raise Http404
    notification = get_object_or_404(Notification.objects.filter(employee=employee), pk=pk)
    notification.is_read = True
    notification.modified_by = request.user
    notification.save(update_fields=['is_read', 'modified_by', 'modified_date'])
    return reply({'ok': True})


@endpoint('POST')
def push_token(request):
    if not settings.MOBILE_PUSH_ENABLED:
        return reply({'error': 'Thông báo điện thoại chưa được cấu hình. Thông báo trong ứng dụng vẫn hoạt động.'}, 503)
    from .push import register_token
    register_token(request, request.mobile_data.get('token'))
    return reply({'ok': True})
