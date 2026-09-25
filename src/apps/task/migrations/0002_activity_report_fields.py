import apps.common.uploads
import apps.m365.storage
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0001_initial"),
        ("task", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="activity",
            field=models.ForeignKey(
                blank=True,
                db_column="ActivityID",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to="activity.activity",
                verbose_name="Hoạt động dự án liên quan",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="report_file",
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.m365.storage.activity_reports_storage,
                upload_to=apps.common.uploads.upload_to_activity_reports,
                validators=[apps.common.uploads.validate_upload],
                verbose_name="Tệp báo cáo hoạt động",
            ),
        ),
    ]
