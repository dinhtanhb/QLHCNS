from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planning", "0002_alter_event_department_alter_event_event_type")]

    operations = [
        # Existing events have no known mode; do not infer historical attendance.
        migrations.AddField(
            model_name="event", name="attendance_mode",
            field=models.CharField(
                "Hình thức", max_length=10, null=True, blank=True,
                choices=[("Online", "Online"), ("Offline", "Offline")],
                db_column="AttendanceMode",
            ),
        ),
        migrations.AlterField(
            model_name="event", name="attendance_mode",
            field=models.CharField(
                "Hình thức", max_length=10, null=True, blank=True, default="Offline",
                choices=[("Online", "Online"), ("Offline", "Offline")],
                db_column="AttendanceMode",
            ),
        ),
    ]
