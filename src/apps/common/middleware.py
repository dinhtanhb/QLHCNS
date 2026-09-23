import threading

from django.db import DatabaseError
from django.utils import timezone


class ApplyDueEmployeeChangesMiddleware:
    """Apply scheduled HR changes once per process per local day on authenticated traffic."""
    _last_run = None
    _lock = threading.Lock()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = timezone.localdate()
        if getattr(request, "user", None) and request.user.is_authenticated and self._last_run != today:
            with self._lock:
                if self._last_run != today:
                    try:
                        from apps.hrm.services import apply_due_employee_changes
                        apply_due_employee_changes(today)
                    except DatabaseError:
                        # A transient DB problem should not take down unrelated portal pages.
                        pass
                    else:
                        self._last_run = today
        return self.get_response(request)
