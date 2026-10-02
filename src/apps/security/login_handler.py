"""Separate username and shared-IP thresholds over the persistent Axes counters."""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Sum
from axes.handlers.database import AxesDatabaseHandler
from axes.helpers import get_failure_limit


class SharedIPAxesHandler(AxesDatabaseHandler):
    def get_failures(self, request, credentials=None):
        attempts = self.get_user_attempts(request, credentials)
        if settings.AXES_LOCKOUT_PARAMETERS != ["username", "ip_address"] or len(attempts) != 2:
            raise ImproperlyConfigured("SharedIPAxesHandler requires username and ip_address lockout parameters.")
        username_count, ip_count = [qs.aggregate(total=Sum("failures_since_start"))["total"] or 0 for qs in attempts]
        username_limit = get_failure_limit(request, credentials)
        ip_limit = settings.AXES_IP_FAILURE_LIMIT
        # Axes compares this score to the username limit. Scale only the IP
        # score so its configured threshold is reached at ip_limit, not at 5.
        return max(username_count, (ip_count * username_limit) // ip_limit)

    def reset_user_attempts(self, request, credentials=None):
        # A valid coworker's login must not erase failed attempts on other
        # accounts sharing that IP. Reset only the successful username.
        return self.filter_user_attempts(request, credentials)[0].delete()[0]
