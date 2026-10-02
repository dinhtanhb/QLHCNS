"""Authentication metadata only: no credentials or personal field values."""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import SecurityEvent


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    SecurityEvent.objects.create(user=user, action='login', resource='authentication')


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user is not None:
        SecurityEvent.objects.create(user=user, action='logout', resource='authentication')
