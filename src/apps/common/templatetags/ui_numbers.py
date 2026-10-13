from decimal import Decimal
from django import template
from apps.common.number_format import vi_number
register = template.Library()

@register.filter
def ui_year(value):
    """Calendar years are identifiers, not quantities needing grouping."""
    if value is None or value == "":
        return "—"
    if isinstance(value, (int, Decimal)) and not isinstance(value, bool):
        return str(value)
    return value

@register.filter
def ui_number(value):
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return vi_number(value)
    return value
