"""Presentation helpers; no DB queries or business calculations."""
from datetime import date, datetime
from django import template
from django.utils import timezone
from django.template.defaultfilters import floatformat
from django.utils.translation import override
from apps.common.ui_status import STATUS_BADGES, status_badge
register = template.Library()

@register.filter
def ui_status_groups(rows, family):
    """Group only the supplied page rows; no query, sorting or workflow changes."""
    groups = {code: {"code": code, "label": value["label"], "rows": []}
              for code, value in STATUS_BADGES.get(family, {}).items()}
    for row in rows:
        code = str(row.status)
        if code not in groups:
            groups[code] = {"code": code, "label": code, "rows": []}
        groups[code]["rows"].append(row)
    return list(groups.values())

@register.inclusion_tag("ui/badge.html")
def ui_badge(family, code, fallback=""):
    return status_badge(family, code, fallback)

@register.filter
def ui_vnd(value):
    if value is None or value == "":
        return "—"
    with override("vi"):
        return str(floatformat(value, "0g")) + " đ"

@register.filter
def ui_date(value):
    if isinstance(value, datetime) and timezone.is_aware(value):
        value = timezone.localtime(value)
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return value if value else "—"

@register.filter
def ui_bound_field(field):
    attrs = {}
    identifiers = []
    if field.help_text:
        identifiers.append(field.auto_id + "-help")
    if field.errors:
        identifiers.append(field.auto_id + "-error")
        attrs["aria-invalid"] = "true"
    if identifiers:
        attrs["aria-describedby"] = " ".join(identifiers)
    return field.as_widget(attrs=attrs)
