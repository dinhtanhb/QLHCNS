"""Separate, revocable bearer sessions; web cookies never authenticate this API."""
from importlib import import_module
import logging
import re

from django.conf import settings
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from django.db import DatabaseError, transaction
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.utils import timezone
from django.utils.crypto import constant_time_compare

PREFIX = '/api/mobile/v1/'
logger = logging.getLogger(__name__)


@transaction.atomic
def save_native_session(native):
    # Session data is cached for the duration of a request. A different request
    # may meanwhile move a push address to another account. Preserve the DB's
    # latest registration under its row lock instead of resurrecting cached data.
    row = Session.objects.select_for_update().filter(session_key=native.session_key).first()
    if row is None:
        return False  # Concurrent logout must never recreate a revoked session.
    current = row.get_decoded()
    native.pop('expo_push_token', None)
    if current.get('expo_push_token'):
        native['expo_push_token'] = current['expo_push_token']
    native.save()
    return True


def _activity_only(before, native):
    def without_activity(data):
        return {key: value for key, value in data.items() if key != 'security_last_activity'}
    return bool(before.get('mobile_session')) and without_activity(before) == without_activity(dict(native))


def _still_valid(native, user):
    """Read only after a failed savepoint, never insert/recreate a session."""
    row = Session.objects.filter(session_key=native.session_key, expire_date__gt=timezone.now()).first()
    if row is None:
        return False
    data = row.get_decoded()
    return (data.get('mobile_session') is True and user.is_authenticated and user.is_active
            and data.get(SESSION_KEY) == str(user.pk)
            and data.get(BACKEND_SESSION_KEY) in settings.AUTHENTICATION_BACKENDS
            and constant_time_compare(data.get(HASH_SESSION_KEY, ''), user.get_session_auth_hash()))


class MobileSessionMiddleware:
    """Runs between SessionMiddleware and AuthenticationMiddleware.

    Reuse Django's backend/hash/expiry checks and existing idle middleware, but
    keep native sessions distinct from portal sessions and never emit cookies.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(PREFIX):
            return self.get_response(request)
        if not settings.MOBILE_API_ENABLED:
            return JsonResponse({'error': 'API mobile chưa được bật.'}, status=404)
        original = request.session
        store = import_module(settings.SESSION_ENGINE).SessionStore
        match = re.fullmatch(r'Bearer ([a-z0-9]{32})', request.headers.get('Authorization', ''))
        native = store(session_key=match[1] if match else None)
        if match and native.get('mobile_session') is not True:
            native = store()
        before = dict(native)
        request.session = native
        try:
            response = self.get_response(request)
            # auth.login rotates CSRF state, but native login must not rotate the
            # browser's CSRF cookie if a portal session shares the same host.
            request.META.pop('CSRF_COOKIE_NEEDS_UPDATE', None)
            response.cookies.clear()
            if native.modified and not native.is_empty() and response.status_code < 500:
                try:
                    saved = save_native_session(native)
                except (DatabaseError, UpdateError) as error:
                    # Django wraps force-update DatabaseError in UpdateError.
                    # The atomic savepoint has exited before this read/recheck.
                    database_error = isinstance(error, DatabaseError) or isinstance(error.__context__, DatabaseError)
                    try:
                        valid = _still_valid(native, request.user)
                    except DatabaseError:
                        valid = None  # Authentication cannot be rechecked: do not claim expiry.
                    if valid is False:
                        saved = False
                    elif valid and database_error and _activity_only(before, native):
                        logger.warning('Mobile activity timestamp was not saved; valid session retained.')
                        saved = True  # Best-effort activity only; never discard business session changes.
                    else:
                        logger.warning('Mobile session write unavailable; retry without revoking session.')
                        response = JsonResponse({'error': 'Dịch vụ phiên tạm bận. Vui lòng thử lại.'}, status=503)
                        saved = True
                if not saved:
                    response = JsonResponse({'error': 'Phiên đã hết hạn. Vui lòng đăng nhập lại.'}, status=401)
            response['Cache-Control'] = 'private, no-store, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Vary'] = 'Authorization'
            return response
        finally:
            request.session = original
