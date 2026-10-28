"""Optional generic Expo push, bound to existing revocable mobile sessions.

No personnel fields, leave status, identifiers or URLs leave IHRMS. Disabled
until the organization configures its Expo/FCM/APNs credentials.
"""
import json
import logging
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from apps.security.models import User

logger = logging.getLogger(__name__)
TOKEN = re.compile(r'(?:ExponentPushToken|ExpoPushToken)\[[A-Za-z0-9_-]{10,200}\]')


@transaction.atomic
def register_token(request, token):
    if not isinstance(token, str) or not TOKEN.fullmatch(token):
        from django.core.exceptions import ValidationError
        raise ValidationError('Mã thiết bị không hợp lệ.')
    # There are only 30–50 users. Serialize registration over live session rows
    # so one physical push address cannot remain bound to a previous account.
    for row in Session.objects.select_for_update().filter(expire_date__gt=timezone.now()).order_by('session_key'):
        data = row.get_decoded()
        if row.session_key != request.session.session_key and data.get('expo_push_token') == token:
            data.pop('expo_push_token')
            Session.objects.filter(pk=row.pk).update(session_data=SessionStore().encode(data))
    request.session['expo_push_token'] = token
    # Publish registration while all affected rows are locked. Middleware merges
    # this committed field before subsequent idle-time saves on other requests.
    request.session.save()


def send_generic_push(employee_ids):
    if not settings.MOBILE_PUSH_ENABLED:
        return
    users = {str(u.pk): u for u in User.objects.filter(employee_id__in=employee_ids,
        employee__is_deleted=False, is_active=True)}
    tokens = set()
    for row in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        data = row.get_decoded()
        user = users.get(data.get(SESSION_KEY))
        last = data.get('security_last_activity', 0)
        token = data.get('expo_push_token', '')
        if (not user or data.get('mobile_session') is not True or not isinstance(last, (int, float))
                or time.time()-last > settings.SESSION_IDLE_TIMEOUT or not isinstance(token, str)
                or not TOKEN.fullmatch(token) or data.get(BACKEND_SESSION_KEY) not in settings.AUTHENTICATION_BACKENDS
                or not constant_time_compare(data.get(HASH_SESSION_KEY, ''), user.get_session_auth_hash())):
            continue
        tokens.add(token)
    messages = [{'to': token, 'title': 'IHRMS',
        'body': 'Bạn có cập nhật mới. Mở IHRMS để xem chi tiết.',
        'data': {'screen': 'notifications'}, 'sound': 'default', 'channelId': 'ihrms-updates'} for token in sorted(tokens)]
    for start in range(0, len(messages), 100):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if settings.MOBILE_EXPO_ACCESS_TOKEN:
            headers['Authorization'] = 'Bearer '+settings.MOBILE_EXPO_ACCESS_TOKEN
        request = Request('https://exp.host/--/api/v2/push/send',
            data=json.dumps(messages[start:start+100]).encode('utf-8'), headers=headers, method='POST')
        try:
            with urlopen(request, timeout=3) as response:
                payload = json.loads(response.read(128_000))
                if payload.get('errors') or any(item.get('status') != 'ok' for item in payload.get('data', [])):
                    logger.warning('Mobile push provider rejected a generic delivery; no device/content logged')
        except (URLError, ValueError, TimeoutError, OSError):
            logger.warning('Mobile push unavailable; in-app notifications remain authoritative')


def after_notification(employee_ids):
    if settings.MOBILE_PUSH_ENABLED:
        transaction.on_commit(lambda: send_generic_push(employee_ids), robust=True)
