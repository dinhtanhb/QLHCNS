from django.db import migrations, models

import apps.common.uploads


class Migration(migrations.Migration):

    dependencies = [
        ("recruitment", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="candidate",
            name="cv_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.common.uploads.upload_to_candidate_cv,
                validators=[apps.common.uploads.validate_upload],
                verbose_name="Hồ sơ CV",
            ),
        ),
    ]
