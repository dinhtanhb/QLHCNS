"""Vietnamese display only; stored and submitted numbers remain canonical."""
from decimal import Decimal

def vi_number(value, places=None):
    number = value if isinstance(value, Decimal) else Decimal(str(value))
    if not number.is_finite():
        return ""
    text = format(number, ",f" if places is None else f",.{places}f")
    if places is None and "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.translate(str.maketrans({",": ".", ".": ","}))
