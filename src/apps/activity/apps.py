from django.apps import AppConfig


class ActivityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.activity"
    verbose_name = "Hoạt động dự án"

    def ready(self):
        from apps.activity import signals  # noqa: F401
