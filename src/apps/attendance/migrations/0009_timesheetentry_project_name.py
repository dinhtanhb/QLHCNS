from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("attendance", "0008_alter_timesheetentry_hours")]
    operations = [
        migrations.AddField(
            model_name="timesheetentry",
            name="project_name",
            field=models.CharField("Dự án nhập tay", max_length=255, blank=True, default="", db_column="ProjectName"),
        ),
    ]
