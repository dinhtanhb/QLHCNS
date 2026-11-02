"""Technical numeric domains, independent of statutory master rates."""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models


def validate_numbers(instance, fields, *, percentages=(), positive=()):
    errors = {}
    for name in fields:
        field = instance._meta.get_field(name)
        raw = getattr(instance, name)
        if raw is None and field.null:
            continue
        try:
            if isinstance(raw, bool):
                raise ValidationError('Giá trị số không hợp lệ.')
            if isinstance(field, models.IntegerField):
                original = Decimal(str(raw))
                if not original.is_finite() or original != original.to_integral_value():
                    raise ValidationError('Giá trị phải là số nguyên.')
            value = field.clean(raw, instance)
            number = Decimal(str(value))
            if not number.is_finite() or number < 0:
                raise ValidationError('Giá trị phải là số hữu hạn và không âm.')
            if name in percentages and number > 100:
                raise ValidationError('Tỷ lệ phần trăm phải từ 0 đến 100.')
            if name in positive and number <= 0:
                raise ValidationError('Giá trị phải lớn hơn 0.')
            setattr(instance, name, value)
        except (InvalidOperation, ValueError, TypeError):
            errors[name] = ['Giá trị số không hợp lệ.']
        except ValidationError as error:
            errors[name] = error.messages
    if errors:
        raise ValidationError(errors)
