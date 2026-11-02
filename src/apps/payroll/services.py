"""Validate a master configuration before closing its previous generation."""
from django.db import transaction


@transaction.atomic
def add_configuration(configuration):
    from datetime import timedelta

    configuration.full_clean()
    type(configuration).objects.filter(effective_to__isnull=True).exclude(
        effective_from__gte=configuration.effective_from,
    ).update(effective_to=configuration.effective_from - timedelta(days=1))
    configuration.save()
    return configuration
