from django.db import migrations, models

import apps.common.uploads


class Migration(migrations.Migration):

    dependencies = [
        ("document", "0002_dispatchbook_officialdispatch_dispatchtracking_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="uploaded_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.common.uploads.upload_to_documents,
                validators=[apps.common.uploads.validate_upload],
                verbose_name="Tệp đính kèm",
            ),
        ),
        migrations.AlterField(
            model_name="officialdispatch",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.common.uploads.upload_to_dispatches,
                validators=[apps.common.uploads.validate_upload],
                verbose_name="Tệp đính kèm scan",
            ),
        ),
    ]
