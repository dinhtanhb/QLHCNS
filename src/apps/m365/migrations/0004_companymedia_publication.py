from django.db import migrations, models


def publish_existing(apps, schema_editor):
    # Owner decision 2026-11-02: preserve visibility of every pre-existing row.
    Media = apps.get_model('m365', 'CompanyMedia')
    Media._base_manager.using(schema_editor.connection.alias).all().update(status='Published')


class Migration(migrations.Migration):
    dependencies = [('m365', '0003_alter_companymedia_options_and_more')]
    operations = [
        migrations.AddField(
            model_name='companymedia', name='status',
            field=models.CharField(choices=[('Draft', 'Nháp'), ('Published', 'Đã xuất bản')],
                                   db_column='Status', default='Draft', max_length=9, verbose_name='Trạng thái'),
        ),
        migrations.RunPython(publish_existing, migrations.RunPython.noop),
    ]
