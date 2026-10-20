from django.db import migrations, models
from django.utils import timezone


def acknowledge_existing_history(apps, schema_editor):
    # Preserve current profiles. Legacy history is acknowledged, not proof that
    # each decision was executed; HR must reconcile previously missed decisions.
    now = timezone.now()
    for name in ("EmployeeTransfer", "EmployeePromotion"):
        model = apps.get_model("hrm", name)
        model._base_manager.using(schema_editor.connection.alias).filter(
            effective_date__lte=timezone.localdate(now),
        ).update(processed_at=now)


class Migration(migrations.Migration):
    dependencies = [("hrm", "0006_alter_employee_company_email")]
    operations = [
        migrations.AddField(
            model_name="employeetransfer", name="processed_at",
            field=models.DateTimeField(blank=True, db_column="ProcessedAt", editable=False, null=True),
        ),
        migrations.AddField(
            model_name="employeepromotion", name="processed_at",
            field=models.DateTimeField(blank=True, db_column="ProcessedAt", editable=False, null=True),
        ),
        migrations.RunPython(acknowledge_existing_history, migrations.RunPython.noop),
    ]
