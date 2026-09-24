from django.db import migrations, models

import apps.common.uploads


class Migration(migrations.Migration):

    dependencies = [
        ("office", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="incomingdocument",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.common.uploads.upload_to_incoming_docs,
                validators=[apps.common.uploads.validate_upload],
                verbose_name="Tệp đính kèm",
            ),
        ),
        migrations.AlterField(
            model_name="outgoingdocument",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.common.uploads.upload_to_outgoing_docs,
                validators=[apps.common.uploads.validate_upload],
                verbose_name="Tệp đính kèm",
            ),
        ),
    ]
