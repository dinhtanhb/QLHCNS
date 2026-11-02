"""Only disposable test databases exercise publication data migration."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MediaPublicationMigrationTests(TransactionTestCase):
    def test_legacy_rows_publish_while_new_rows_default_to_draft(self):
        from django.core.management import call_command
        from io import StringIO
        sql=StringIO();call_command('sqlmigrate','m365','0004',stdout=sql)
        print('FIX_C_SQLMIGRATE_BEGIN',connection.vendor,flush=True)
        print(sql.getvalue(),flush=True)
        print('FIX_C_SQLMIGRATE_END',connection.vendor,flush=True)
        before=[('m365','0003_alter_companymedia_options_and_more')]
        after=[('m365','0004_companymedia_publication')]
        executor=MigrationExecutor(connection)
        try:
            executor.migrate(before)
            OldMedia=executor.loader.project_state(before).apps.get_model('m365','CompanyMedia')
            first=OldMedia.objects.create(title='Synthetic legacy media',media_type='Image',file='synthetic/legacy.png')
            second=OldMedia.objects.create(title='Synthetic deleted legacy',media_type='Image',file='synthetic/legacy-deleted.png',is_deleted=True)
            executor=MigrationExecutor(connection);executor.migrate(after)
            NewMedia=executor.loader.project_state(after).apps.get_model('m365','CompanyMedia')
            self.assertEqual(set(NewMedia._base_manager.filter(pk__in=[first.pk,second.pk]).values_list('status',flat=True)),{'Published'})
            new=NewMedia.objects.create(title='Synthetic new',media_type='Image',file='synthetic/new.png')
            self.assertEqual(new.status,'Draft')
        finally:
            MigrationExecutor(connection).migrate(after)
