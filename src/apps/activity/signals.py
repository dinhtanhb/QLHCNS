from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.activity.models import Activity
from apps.activity.services import create_task_for_activity


@receiver(post_save, sender=Activity, dispatch_uid="activity.create_report_task")
def create_report_task_when_dispatch_is_linked(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if instance.status == "Cancelled":
        from apps.task.models import Task
        Task.objects.filter(activity=instance).exclude(status__in=("Done", "Cancelled")).update(
            status="Cancelled"
        )
        return
    if not instance.outgoing_document_id:
        return
    create_task_for_activity(instance)
