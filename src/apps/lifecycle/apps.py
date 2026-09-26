from django.apps import AppConfig


class LifecycleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lifecycle"
    verbose_name = "Quy trình tiếp nhận và nghỉ việc"
