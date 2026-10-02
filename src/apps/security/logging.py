"""Avoid persisting exception payloads that may contain SQL/Graph secrets."""
import logging
from django.conf import settings


class SafeExceptionFilter(logging.Filter):
    def filter(self, record):
        if not settings.DEBUG and record.exc_info:
            record.msg = "Unhandled error: type=%s (exception payload omitted)"
            record.args = (record.exc_info[0].__name__,)
            record.exc_info = None
            record.exc_text = None
        return True
