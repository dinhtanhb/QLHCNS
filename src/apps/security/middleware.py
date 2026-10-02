import time
from django.conf import settings
from django.contrib.auth import logout
from django.utils.cache import patch_cache_control


class SensitiveResponseMiddleware:
    """Expire idle sessions and keep authenticated content out of shared caches."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        authenticated = request.user.is_authenticated
        if authenticated:
            now = int(time.time())
            last = request.session.get('security_last_activity', now)
            if not isinstance(last, (int, float)) or now - last > settings.SESSION_IDLE_TIMEOUT:
                logout(request)
            else:
                request.session['security_last_activity'] = now
        response = self.get_response(request)
        if authenticated or request.user.is_authenticated or request.path in ('/portal/login/', '/admin/login/'):
            patch_cache_control(response, private=True, no_store=True, no_cache=True, must_revalidate=True)
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response
