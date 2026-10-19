from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("task", "0003_task_completed_date")]

    operations = [migrations.AddField(
        model_name="task", name="act_code",
        field=models.CharField("Mã ActCode", max_length=50, null=True, blank=True,
                               db_index=True, db_column="ActCode"),
    )]
