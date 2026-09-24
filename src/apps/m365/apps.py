from django.apps import AppConfig


class M365Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.m365"
    verbose_name = "Tích hợp Microsoft 365"