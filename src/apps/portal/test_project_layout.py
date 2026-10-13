"""Filter round trips and read/write contracts behind the shared screen layout."""
from datetime import date
from html.parser import HTMLParser

from django.template import engines
from django.test import TestCase
from django.urls import reverse

from apps.portal import test_home_dashboard as fixtures
from apps.asset.models import InventorySession


class QueryForms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.forms = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form' and 'ui-query-bar' in attrs.get('class', '').split():
            self.current = {'names':[], 'submit':0}
            self.forms.append(self.current)
        if self.current:
            if tag in ('input','select') and attrs.get('name'):
                self.current['names'].append(attrs['name'])
            if tag == 'button' and attrs.get('type', 'submit') == 'submit':
                self.current['submit'] += 1

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current = None


class ProjectLayoutTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_all_templates_compile(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        engine = engines['django'].engine
        files = list((root/'templates').rglob('*.html'))
        for app in (root/'apps').iterdir():
            if app.is_dir() and (app/'templates').is_dir():
                files.extend((app/'templates').rglob('*.html'))
        for path in files:
            with self.subTest(template=str(path.relative_to(root))):
                engine.from_string(path.read_text(encoding='utf-8'))

    def test_employee_filter_roundtrip_preserves_scope_and_parameter(self):
        hr = self.user('HR_MANAGER',True)
        from apps.contract.models import Contract, ContractType
        kind=ContractType.objects.create(contract_type_code='LAYOUT',contract_type_name='Fake')
        Contract.objects.create(employee=hr.employee,contract_type=kind,contract_no='LAYOUT',
            start_date=date(2020,1,1),status='Draft',basic_salary=0)
        self.client.force_login(hr)
        response=self.client.get(reverse('portal:hr_employee_list'),{'q':hr.employee.employee_code})
        self.assertEqual(response.context['page_obj'].paginator.count,1)
        forms=QueryForms();forms.feed(response.content.decode())
        self.assertEqual(forms.forms,[{'names':['q'],'submit':1}])
        response=self.client.get(reverse('portal:hr_employee_list'),{'q':'NOT-FOUND'})
        self.assertEqual(response.context['page_obj'].paginator.count,0)

    def test_month_year_filters_remain_raw_years(self):
        hr=self.user('HR_MANAGER',True);self.client.force_login(hr)
        for name,params,names in (
            ('timesheet_month',{'month':'2','year':'2026'},['month','year']),
            ('report_timesheet',{'month':'2','year':'2026'},['month','year']),
            ('report_headcount',{'year':'2026'},['year']),
            ('report_budget',{'year':'2026'},['year']),
        ):
            with self.subTest(page=name):
                response=self.client.get(reverse('portal:'+name),params)
                self.assertEqual(response.status_code,200)
                forms=QueryForms();forms.feed(response.content.decode())
                self.assertEqual(forms.forms,[{'names':names,'submit':1}])
                self.assertContains(response,'value="2026"')
                self.assertNotContains(response,'value="2.026"')

    def test_inventory_payload_and_permission_preserved(self):
        hr=self.user('HR_MANAGER',True);person=self.user('EMPLOYEE',True)
        payload={'session_name':'Synthetic layout inventory','office_name':'Fake office',
            'inventory_datetime':'2026-10-13T09:00'}
        self.client.force_login(person)
        response=self.client.post(reverse('portal:inventory_session_create'),payload)
        self.assertEqual(InventorySession.objects.count(),0)
        self.client.force_login(hr)
        response=self.client.post(reverse('portal:inventory_session_create'),payload)
        self.assertEqual(response.status_code,302)
        self.assertTrue(InventorySession.objects.filter(session_name=payload['session_name'],office_name=payload['office_name']).exists())

    def test_office_approval_pages_render_and_keep_permission_gate(self):
        admin = self.user('SYS_ADMIN')
        admin.is_superuser = True
        admin.save(update_fields=['is_superuser'])
        person = self.user('EMPLOYEE', True)
        for name in ('room_booking_approval_list', 'vehicle_booking_approval_list', 'supply_request_approval_list'):
            with self.subTest(page=name):
                self.client.force_login(admin)
                self.assertEqual(self.client.get(reverse('portal:' + name)).status_code, 200)
                self.client.force_login(person)
                response = self.client.get(reverse('portal:' + name))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse('portal:dashboard'))

    def test_timesheet_print_values_use_saved_summary_and_keep_screen_inputs(self):
        from decimal import Decimal
        from apps.attendance.models import MonthlyAttendanceSummary
        person = self.user('EMPLOYEE', True)
        self.client.force_login(person)
        url = reverse('portal:timesheet_month')
        self.client.get(url, {'month':10, 'year':2026})
        summary = MonthlyAttendanceSummary.objects.get(employee=person.employee, month=10, year=2026)
        summary.sick_days = Decimal('1.5')
        summary.save()
        response = self.client.get(url, {'month':10, 'year':2026})
        self.assertContains(response, '<span class="ui-print-only">1,5</span>', html=True)
        self.assertContains(response, 'name="sick_days"')
        self.assertContains(response, 'class="timesheet-summary-form"')
        self.assertContains(response, 'print_forms.css')

    def test_inventory_print_nullable_values_stay_blank_and_zero_is_retained(self):
        from django.utils import timezone
        from apps.asset.models import AssetType, Asset, InventoryLine
        hr = self.user('HR_MANAGER', True)
        self.client.force_login(hr)
        kind = AssetType.objects.create(asset_type_code='PRINT', asset_type_name='Synthetic')
        asset = Asset.objects.create(asset_type=kind, asset_code='PRINT', asset_name='Synthetic', purchase_value=0)
        session = InventorySession.objects.create(session_name='Synthetic', office_name='Fake office', inventory_datetime=timezone.now())
        InventoryLine.objects.create(session=session, asset=asset)
        response = self.client.get(reverse('portal:inventory_session_print', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ui-print-landscape')
        self.assertNotContains(response, '>None<')
        self.assertContains(response, '>0</td>')
