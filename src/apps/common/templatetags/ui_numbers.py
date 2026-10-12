from decimal import Decimal
from django import template
from apps.common.number_format import vi_number
register = template.Library()

@register.filter
def ui_number(value):
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return vi_number(value)
    return value
