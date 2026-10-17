"""Project form behavior on isolated test data; no production lookups."""
from datetime import timedelta
from types import SimpleNamespace
from django.test import TestCase, SimpleTestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.security.models import User
from apps.planning.models import Event
from apps.common.ui_choices import text_choices
from django.test import override_settings


class ChoiceTests(SimpleTestCase):
    def test_suggestions_use_only_supplied_rows_and_keep_new_values_possible(self):
        rows = [SimpleNamespace(location=x) for x in (' Office A ', 'Office   A', '', None, 'Office B')]
        self.assertEqual(text_choices(rows, 'location'), ['Office A', 'Office B'])

    def test_asset_hash_refreshes_when_static_content_changes_in_running_process(self):
        import tempfile
        from pathlib import Path
        from apps.common.asset_version import get_asset_hash, clear_asset_hash_cache
        with tempfile.TemporaryDirectory() as temp, override_settings(BASE_DIR=Path(temp)):
            file=Path(temp)/'static/css/example.css'
            file.parent.mkdir(parents=True)
            file.write_text('a{}')
            before=get_asset_hash('css/example.css')
            file.write_text('a{color:red}')
            self.assertNotEqual(before,get_asset_hash('css/example.css'))
        clear_asset_hash_cache()


class EventModeTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser(username='forms-admin', password='test-password', email='forms@example.test')
        self.client.force_login(self.user)
        now=timezone.localtime()+timedelta(days=2)
        self.payload={'title':'Synthetic event', 'event_type':'Meeting', 'department':'',
                      'start_time':now.strftime('%Y-%m-%dT%H:%M'),
                      'end_time':(now+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
                      'location':'New location', 'description':'Preserved description'}

    def test_online_offline_and_missing_mode_default_are_persisted(self):
        for mode in ('Online','Offline',None):
            data=dict(self.payload)
            if mode is not None:data['attendance_mode']=mode
            response=self.client.post(reverse('portal:event_list'),data)
            self.assertEqual(response.status_code,302)
            event=Event.objects.latest('pk')
            self.assertEqual(event.attendance_mode, mode or 'Offline')
            self.assertEqual(event.location,'New location')

    def test_invalid_mode_and_time_do_not_write_and_preserve_input(self):
        for changes in ({'attendance_mode':'Hybrid'}, {'attendance_mode':'Online','end_time':self.payload['start_time']}):
            response=self.client.post(reverse('portal:event_list'),dict(self.payload,**changes))
            self.assertEqual(response.status_code,200)
            self.assertEqual(Event.objects.count(),0)
            self.assertContains(response,'Preserved description')
            self.assertContains(response,'New location')
            if changes['attendance_mode']=='Online':self.assertContains(response,'value="Online" selected')

    def test_legacy_unknown_display_and_other_department_location_not_suggested(self):
        from apps.organization.models import Organization,Department
        org=Organization.objects.create(organization_code='SYN',organization_name='Synthetic')
        dep=Department.objects.create(organization=org,department_code='SYN-D',department_name='Other')
        now=timezone.now()
        Event.objects.create(title='Legacy',start_time=now,end_time=now+timedelta(days=2),attendance_mode=None)
        Event.objects.create(title='Private',department=dep,start_time=now,end_time=now+timedelta(days=2),location='PRIVATE_LOCATION_SENTINEL')
        response=self.client.get(reverse('portal:event_list'))
        self.assertContains(response,'Chưa xác định')
        self.assertNotContains(response,'PRIVATE_LOCATION_SENTINEL')

    def test_model_choice_validation(self):
        event=Event(title='Invalid',start_time=timezone.now(),end_time=timezone.now()+timedelta(hours=1),attendance_mode='Hybrid')
        with self.assertRaises(ValidationError):event.full_clean()

    def test_admin_uses_explicit_unknown_label_for_legacy_mode(self):
        from django.contrib import admin
        from apps.planning.admin import EventAdmin
        model_admin=EventAdmin(Event,admin.site)
        self.assertEqual(model_admin.attendance_mode_label(Event(attendance_mode=None)), 'Chưa xác định')
        self.assertEqual(model_admin.attendance_mode_label(Event(attendance_mode='Online')), 'Online')



class FailedChoiceFormsTests(TransactionTestCase):
    # Invalid datetime reaches model.save(); use request-like transactions rather
    # than TestCase's outer atomic block, which would stay rollback-only.
    def setUp(self):
        EventModeTests.setUp(self)

    def test_failed_asset_and_inventory_forms_keep_values_after_redirect(self):
        for route, data, field, value in (
            ('asset_admin_create', {'asset_code':'DRAFT','asset_name':'Draft asset','location':'New office','quantity':'invalid'}, 'location','New office'),
            ('inventory_session_create', {'session_name':'Draft inventory','office_name':'New department','inventory_datetime':'invalid'}, 'office_name','New department'),
        ):
            response=self.client.post(reverse('portal:'+route),data)
            self.assertEqual(response.status_code,302,route)
            target=response.url
            response=self.client.get(target)
            self.assertContains(response,'value="'+value+'"')
            self.assertEqual(response.context['submitted'][field],value)
            self.assertNotIn(field,self.client.get(target).context['submitted'])

    def test_failed_bookings_keep_selected_catalogue_and_text(self):
        from apps.office.tests import OfficeTestBase
        OfficeTestBase.setUpTestData()
        self.user.employee=OfficeTestBase.employee
        self.user.save(update_fields=['employee'])
        for kind,resource in (('room',OfficeTestBase.room),('vehicle',OfficeTestBase.vehicle)):
            payload={kind:str(resource.pk),'purpose':'Draft purpose','destination':'New destination','start_time':'invalid','end_time':'invalid'}
            response=self.client.post(reverse('portal:'+kind+'_booking_create'),payload,follow=True)
            self.assertEqual(response.redirect_chain[-1][1],302)
            self.assertContains(response,'value="'+str(resource.pk)+'" selected')
            self.assertContains(response,'value="Draft purpose"')
            if kind=='vehicle':self.assertContains(response,'value="New destination"')


class EventModeMigrationTests(TransactionTestCase):
    def test_existing_rows_stay_unknown_while_new_rows_default_offline(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        executor=MigrationExecutor(connection)
        executor.migrate([('planning','0002_alter_event_department_alter_event_event_type')])
        try:
            old=executor.loader.project_state([('planning','0002_alter_event_department_alter_event_event_type')]).apps.get_model('planning','Event')
            now=timezone.now()
            row=old.objects.create(title='Legacy migration fixture',start_time=now,end_time=now+timedelta(hours=1))
            executor=MigrationExecutor(connection)
            executor.migrate([('planning','0003_event_attendance_mode')])
            new=executor.loader.project_state([('planning','0003_event_attendance_mode')]).apps.get_model('planning','Event')
            self.assertIsNone(new.objects.get(pk=row.pk).attendance_mode)
            self.assertEqual(new.objects.create(title='New fixture',start_time=now,end_time=now+timedelta(hours=1)).attendance_mode,'Offline')
        finally:
            MigrationExecutor(connection).migrate([('planning','0003_event_attendance_mode')])
