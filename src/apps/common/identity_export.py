"""Identity disclosure is explicit at spreadsheet export boundaries only."""
from apps.security.permissions import has_permission


def spreadsheet_national_id(value, user=None):
    text = str(value or '')
    if not text or (user is not None and has_permission(user, 'export_full_national_id')):
        return text
    return '********' + text[-4:] if len(text) >= 4 else '************'
