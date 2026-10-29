"""Separate, revocable bearer sessions; web cookies never authenticate this API."""
from importlib import import_module
import re

from django.conf import settings
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from django.db import transaction
from django.contrib.sessions.backends.base import UpdateError

PREFIX = '/api/mobile/v1/'


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
    try:
        native.save()
    except UpdateError:
        return False
    return True


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
        request.session = native
        try:
            response = self.get_response(request)
            # auth.login rotates CSRF state, but native login must not rotate the
            # browser's CSRF cookie if a portal session shares the same host.
            request.META.pop('CSRF_COOKIE_NEEDS_UPDATE', None)
            response.cookies.clear()
            if native.modified and not native.is_empty() and response.status_code < 500:
                if not save_native_session(native):
                    response = JsonResponse({'error': 'Phiên đã hết hạn. Vui lòng đăng nhập lại.'}, status=401)
            response['Cache-Control'] = 'private, no-store, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Vary'] = 'Authorization'
            return response
        finally:
            request.session = original
