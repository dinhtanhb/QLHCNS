"""Native transport for the portal's existing, permission-checked workflows.

Only local registered application routes are callable. No network proxy, template
execution from the device, cookie authentication, or role impersonation occurs.
"""
from copy import copy
from io import BytesIO
import json
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import Http404, HttpResponse, JsonResponse, QueryDict
from django.middleware.csrf import get_token
from django.urls import Resolver404, resolve
from django.utils.datastructures import MultiValueDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables

from .workspace_schema import NativeSchema


def complete_navigation(result, user):
    from apps.security.permissions import has_permission
    supplements = [
        ('/portal/search/', 'Tìm kiếm', 'Tra cứu và báo cáo', True),
        ('/assistant/', 'Trợ lý tài liệu', 'Tra cứu và báo cáo', True),
        ('/portal/procurement/', 'Mua sắm', 'Hành chính', has_permission(user, 'request_procurement') or has_permission(user, 'approve_procurement')),
        ('/portal/rooms/approvals/', 'Duyệt phòng họp', 'Hành chính', has_permission(user, 'approve_office_request')),
        ('/portal/vehicles/approvals/', 'Duyệt đặt xe', 'Hành chính', has_permission(user, 'approve_office_request')),
        ('/portal/supplies/approvals/', 'Duyệt và cấp văn phòng phẩm', 'Hành chính', has_permission(user, 'approve_office_request')),
        ('/portal/kpi/score/', 'Chấm điểm KPI', 'Cá nhân', has_permission(user, 'score_kpi')),
        ('/reports/', 'Trung tâm Báo cáo (Excel)', 'Tra cứu và báo cáo', has_permission(user, 'view_report_center')),
    ]
    known = {row['path'] for row in result['navigation']}
    for path, label, group, permitted in supplements:
        if permitted and path not in known:
            result['navigation'].append({'kind': 'link', 'path': path, 'label': label, 'group': group, 'external': False})


EXCLUDED = {'login', 'logout', 'service_worker', 'password_change', 'password_change_done', 'jsi18n'}
NAMESPACES = {'portal', 'reporting', 'admin', 'assistant'}
MAX_PAYLOAD = 1024 * 1024
MAX_FIELDS = 2000


def close_internal(response):
    # Only the outer response may emit request_finished. Closing an internally
    # rendered response would close SQL Server's connection mid-transaction.
    for closer in response._resource_closers:
        try:
            closer()
        except Exception:
            pass
    response._resource_closers.clear()


class ExpiredWorkspaceSession(Exception):
    pass


def local_route(value):
    if not isinstance(value, str) or not value.startswith('/') or value.startswith('//') or len(value) > 8192:
        raise PermissionDenied('Địa chỉ nghiệp vụ không hợp lệ.')
    decoded = unquote(unquote(value))
    if '\\' in decoded or any(ord(char) < 32 for char in decoded) or any(part in {'.', '..'} for part in urlsplit(decoded).path.split('/')):
        raise PermissionDenied('Địa chỉ nghiệp vụ không hợp lệ.')
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise PermissionDenied('Chỉ truy cập nghiệp vụ nội bộ.')
    parsed = parsed._replace(path=unquote(parsed.path))
    if parsed.path.startswith('//'):
        raise PermissionDenied('Địa chỉ nghiệp vụ không hợp lệ.')
    try:
        match = resolve(parsed.path)
    except Resolver404:
        raise Http404
    if match.url_name in EXCLUDED:
        raise PermissionDenied('Dùng chức năng tài khoản trong Cài đặt.')
    if match.namespace not in NAMESPACES and match.view_name != 'private_file':
        raise PermissionDenied('Nghiệp vụ không thuộc phạm vi mobile.')
    return parsed, match


def allowed_route(value):
    try:
        local_route(value)
        return True
    except (PermissionDenied, Http404, ValueError):
        return False


@sensitive_variables()
def payload_from(request):
    if request.method == 'GET':
        return {'path': request.GET.get('path', '/portal/'), 'method': 'GET', 'fields': []}, MultiValueDict()
    if request.content_type == 'application/json':
        if len(request.body) > MAX_PAYLOAD:
            raise ValidationError('Biểu mẫu quá lớn.')
        payload = json.loads(request.body or b'{}')
        files = MultiValueDict()
    elif request.content_type == 'multipart/form-data':
        raw = request.POST.get('payload', '')
        if len(raw.encode('utf-8')) > MAX_PAYLOAD:
            raise ValidationError('Biểu mẫu quá lớn.')
        payload = json.loads(raw)
        files = request.FILES
    else:
        raise ValidationError('Định dạng biểu mẫu không được hỗ trợ.')
    if not isinstance(payload, dict):
        raise ValidationError('Biểu mẫu không hợp lệ.')
    if len(files) > 20:
        raise ValidationError('Tối đa 20 tệp trong một lần gửi.')
    return payload, files


@sensitive_variables()
def build_fields(payload, incoming):
    fields = payload.get('fields', [])
    uploads = payload.get('uploads', [])
    if not isinstance(fields, list) or len(fields) > MAX_FIELDS or not isinstance(uploads, list) or len(uploads) > 20:
        raise ValidationError('Biểu mẫu không hợp lệ.')
    post = QueryDict('', mutable=True)
    for pair in fields:
        if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(v, str) for v in pair):
            raise ValidationError('Trường biểu mẫu không hợp lệ.')
        name, value = pair
        if not name or len(name) > 300 or len(value) > 262144 or any(ord(c) < 32 for c in name):
            raise ValidationError('Trường biểu mẫu quá dài hoặc không hợp lệ.')
        if name != 'csrfmiddlewaretoken':
            post.appendlist(name, value)
    files = MultiValueDict()
    from apps.common.uploads import validate_upload
    for entry in uploads:
        if not isinstance(entry, dict) or not isinstance(entry.get('name'), str) or not isinstance(entry.get('key'), str):
            raise ValidationError('Tệp đính kèm không hợp lệ.')
        name = entry['name']
        if not name or len(name) > 300 or name == 'csrfmiddlewaretoken':
            raise ValidationError('Tên trường tệp không hợp lệ.')
        for uploaded in incoming.getlist(entry['key']):
            validate_upload(uploaded)
            files.appendlist(name, uploaded)
    if sum(len(files.getlist(key)) for key in files) > 20:
        raise ValidationError('Tối đa 20 tệp trong một lần gửi.')
    return post, files


def cloned_request(original, path, method, fields, files):
    parsed, match = local_route(path)
    request = copy(original)
    request.META = original.META.copy()
    request.COOKIES = {}
    request.path = request.path_info = parsed.path
    request.method = method
    request.resolver_match = match
    request.GET = QueryDict(parsed.query, encoding='utf-8')
    request._post = fields
    request._files = files
    request.session = original.session
    request.user = original.user
    request._messages = FallbackStorage(request)
    request.META['PATH_INFO'] = parsed.path
    request.META['QUERY_STRING'] = parsed.query
    request.META['REQUEST_METHOD'] = method
    request.META['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    request.META.pop('HTTP_COOKIE', None)
    # This internal request is authorized by the native bearer, never a browser
    # cookie. Produce a valid internal CSRF pair for decorated admin views too.
    token = get_token(request)
    request._post = fields.copy()
    request._post['csrfmiddlewaretoken'] = token
    request.COOKIES[settings.CSRF_COOKIE_NAME] = request.META['CSRF_COOKIE']
    request.META['HTTP_ORIGIN'] = original.build_absolute_uri('/').rstrip('/')
    request.META['HTTP_REFERER'] = original.build_absolute_uri(path)
    request._body = request._post.urlencode().encode('utf-8')
    request._stream = BytesIO(request._body)
    request._read_started = False
    request.META['CONTENT_LENGTH'] = str(len(request._body))
    return request, match


def refresh_actor(request):
    try:
        request.user.refresh_from_db()
    except ObjectDoesNotExist:
        auth.logout(request)
        raise ExpiredWorkspaceSession
    for attribute in ('_perm_cache', '_user_perm_cache', '_group_perm_cache'):
        request.user.__dict__.pop(attribute, None)
    if not request.user.is_active:
        auth.logout(request)
        raise ExpiredWorkspaceSession


@sensitive_variables()
def dispatch(request):
    payload, incoming = payload_from(request)
    path = payload.get('path', '/portal/')
    method = payload.get('method', 'GET')
    if method not in {'GET', 'POST'}:
        raise ValidationError('Phương thức không được hỗ trợ.')
    fields, files = build_fields(payload, incoming)
    if method == 'GET' and fields:
        parsed, _ = local_route(path)
        query = QueryDict(parsed.query, mutable=True)
        for key in fields:
            query.setlist(key, fields.getlist(key))
        path = parsed.path + ('?'+query.urlencode() if query else '')
        fields = QueryDict('', mutable=True)
    notices = []
    for _ in range(8):
        internal, match = cloned_request(request, path, method, fields, files)
        if payload.get('json') is not None:
            if method != 'POST' or match.view_name != 'assistant:api_search' or not isinstance(payload['json'], dict):
                raise ValidationError('Nghiệp vụ này không nhận dữ liệu JSON trực tiếp.')
            internal.META['CONTENT_TYPE'] = 'application/json'
            internal.META['HTTP_X_CSRFTOKEN'] = get_token(internal)
            internal._body = json.dumps(payload['json']).encode('utf-8')
            internal._stream = BytesIO(internal._body)
            internal.META['CONTENT_LENGTH'] = str(len(internal._body))
        if match.namespace == 'admin' and not request.user.is_staff:
            raise PermissionDenied('Không có quyền quản trị.')
        if match.namespace == 'admin' and match.url_name.endswith('_password_change') and str(match.kwargs.get('id') or match.kwargs.get('object_id')) == str(request.user.pk):
            raise PermissionDenied('Đổi mật khẩu của bạn trong Cài đặt tài khoản.')
        response = match.func(internal, *match.args, **match.kwargs)
        if hasattr(response, 'render'):
            response.render()
        notices.extend({'text': str(message), 'level': message.level} for message in messages.get_messages(internal))
        internal._messages.update(response)
        if method == 'POST':
            refresh_actor(request)
        if response.status_code in {301, 302, 303, 307, 308}:
            destination = response.headers.get('Location', '')
            # Never repeat a POST, including for a 307/308 response.
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc:
                if parsed.netloc != request.get_host():
                    raise PermissionDenied('Không chuyển tiếp ra máy chủ khác.')
                destination = parsed.path + ('?'+parsed.query if parsed.query else '')
            local_route(destination)
            close_internal(response)
            path, method, fields, files = destination, 'GET', QueryDict('', mutable=True), MultiValueDict()
            payload.pop('json', None)
            continue
        kind = response.headers.get('Content-Type', '').split(';', 1)[0].lower()
        invalid_form = response.status_code == 422 and kind in {'text/html', 'application/xhtml+xml'}
        if response.status_code >= 400 and not invalid_form:
            error = 'Không có quyền hoặc dữ liệu không hợp lệ.' if response.status_code in {400, 403, 404} else 'Chưa xử lý được nghiệp vụ. Vui lòng thử lại.'
            if not getattr(response, 'streaming', False) and response.status_code in {400, 403}:
                body = response.content.decode(response.charset or 'utf-8', errors='replace').strip()
                if len(body) <= 1000 and '<' not in body and not body.startswith('{'):
                    error = body or error
                if response.headers.get('Content-Type', '').startswith('application/json'):
                    try:
                        code = json.loads(body).get('error')
                        error = {'question_too_short': 'Nhập ít nhất 2 ký tự để tìm tài liệu.', 'rate_limited': 'Bạn tìm quá nhanh. Vui lòng chờ một phút.',
                                 'session_expired': 'Phiên đã kết thúc. Vui lòng đăng nhập lại.'}.get(code, error)
                    except (ValueError, AttributeError):
                        pass
            close_internal(response)
            return JsonResponse({'error': error, 'messages': notices}, status=response.status_code)
        if kind == 'application/json':
            data = json.loads(response.content)
            close_internal(response)
            return JsonResponse({'kind': 'json', 'path': path, 'data': data, 'messages': notices})
        if getattr(response, 'streaming', False) or kind not in {'text/html', 'application/xhtml+xml'}:
            response['X-IHRMS-Document'] = '1'
            return response
        html = response.content.decode(response.charset or 'utf-8')
        if payload.get('print') is True and not invalid_form:
            from .workspace_print import printable_html
            close_internal(response)
            result = HttpResponse(printable_html(html), content_type='text/html; charset=utf-8')
            result['X-IHRMS-Document'] = '1'
            result['Content-Disposition'] = 'attachment; filename="IHRMS-print.html"'
            return result
        result = NativeSchema(html, path, allowed_route, request.build_absolute_uri('/')).result()
        if match.view_name == 'assistant:assistant_page':
            for block in result['blocks']:
                if block['kind'] == 'form' and any(f['name'] == 'question' for f in block['fields']):
                    block['format'] = 'json'
                    for action in block['actions']:
                        action.update(path='/assistant/api/search/', method='POST')
            result['blocks'].insert(0, {'kind': 'link', 'label': 'Lịch sử tìm kiếm', 'path': '/assistant/api/history/', 'external': False})
        result['messages'] = notices
        complete_navigation(result, request.user)
        if payload.get('menu_only') is True:
            result['blocks'] = []
        close_internal(response)
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
    raise ValidationError('Luồng chuyển trang quá dài. Vui lòng mở lại nghiệp vụ.')


@csrf_exempt
@sensitive_post_parameters('payload')
def workspace(request):
    from .views import endpoint
    # Keep the ordinary endpoints' JSON limit unchanged; only this transport
    # accepts the explicitly bounded form/file contract above.
    try:
        return endpoint('GET', 'POST', parse_json=False)(dispatch)(request)
    except ExpiredWorkspaceSession:
        return JsonResponse({'error': 'Phiên đã kết thúc. Vui lòng đăng nhập lại.'}, status=401)
