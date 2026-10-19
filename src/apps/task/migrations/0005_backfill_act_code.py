from django.db import migrations, models, transaction


# Frozen catalogue approved in docs/ActCode.md on 19/10/2026; never import live choices.
ACT_CODES = (
    "46.9.1.1.2.1", "46.9.1.1.2.2", "46.9.1.1.2.3",
    "46.9.1.1.3.1", "46.9.1.1.3.2", "46.9.1.1.3.3", "46.9.1.1.3.4",
    "46.9.1.2.1", "46.9.1.3.1", "46.9.1.4.1", "46.9.1.5.1",
    "46.9.2.1.1", "46.9.2.1.2", "46.9.2.1.3", "46.9.2.1.4",
    "46.9.3.1", "46.9.3.2", "46.9.3.3",
)


def backfill(apps, schema_editor):
    Task = apps.get_model("task", "Task")
    alias = schema_editor.connection.alias
    while True:
        with transaction.atomic(using=alias):
            matching = Task.objects.using(alias).filter(act_code__isnull=True, task_code__in=ACT_CODES)
            keys = list(matching.order_by("pk").values_list("pk", flat=True)[:100])
            if not keys:
                break
            matching.filter(pk__in=keys).update(act_code=models.F("task_code"))


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("task", "0004_task_act_code")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop, atomic=False)]
