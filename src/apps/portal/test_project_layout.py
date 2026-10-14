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

    def test_all_query_bars_share_actions_labels_and_reset_contract(self):
        admin = self.user('SUPER_ADMIN', True)
        admin.is_superuser = True
        admin.save(update_fields=['is_superuser'])
        self.client.force_login(admin)
        pages = {
            'activity_calendar':['month','cbda'], 'activity_dashboard':['month','cbda'],
            'hcns_catalog':['employee_id'], 'dashboard_people':['metric','on_date','q'],
            'dispatch_list':['q','type','status'], 'hr_employee_list':['q'],
            'kpi_score_list':['period'], 'personnel_decision_list':['q','status'],
            'report_budget':['year'], 'report_headcount':['year'],
            'report_hub':['from_date','to_date'], 'report_personnel_changes':['from_date','to_date'],
            'report_timesheet':['month','year'], 'timesheet_month':['month','year'],
        }
        import re
        for name, expected in pages.items():
            with self.subTest(page=name):
                response = self.client.get(reverse('portal:' + name))
                self.assertEqual(response.status_code,200)
                forms=QueryForms();forms.feed(response.content.decode())
                self.assertEqual(forms.forms,[{'names':expected,'submit':1}])
                html=response.content.decode()
                form=re.search(r'<form[^>]*class="ui-query-bar".*?</form>',html,re.S)[0]
                self.assertIn('>Áp dụng</button>',form)
                self.assertNotIn('>Xóa lọc</a>',form)
                self.assertIn('ui-query-card',html)
                for field in expected:
                    if field in ('metric','on_date'):continue
                    ident=re.search(r'<(?:input|select)[^>]*id="([^"]+)"[^>]*name="'+field+'"',form)[1]
                    self.assertIn('for="'+ident+'"',form)
                value={'q':'SYNTHETIC','year':'2026','month':'2026-10' if name.startswith('activity') else '10','from_date':'2026-01-01','employee_id':str(admin.employee_id),'period':'1'}
                parameter=next(x for x in expected if x not in ('metric','on_date','cbda','type','status'))
                filtered=self.client.get(reverse('portal:'+name),{parameter:value[parameter]})
                self.assertEqual(filtered.status_code,200)
                self.assertContains(filtered,'>Xóa lọc</a>')

    def test_query_css_has_one_owner_and_inline_actions(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[2]
        css=(root/'static/css/shared_components.css').read_text()
        self.assertIn('.ui-query-bar { display:flex;',css)
        self.assertNotIn('ui-query-',(root/'static/css/project_layout.css').read_text())
        self.assertNotIn('justify-content:flex-end',css[css.index('.ui-query-actions {'):css.index('.ui-page {')])

    def test_filter_and_results_share_a_card_without_hidden_results(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        files = [p for p in (root / 'apps').rglob('*.html')
                 if 'class="ui-query-bar"' in p.read_text(encoding='utf-8')]
        self.assertEqual(len(files), 14)
        for path in files:
            with self.subTest(template=path.name):
                source = path.read_text(encoding='utf-8')
                self.assertIn('ui-results-card', source)
                self.assertIn('<div class="ui-query-card no-print">', source)
                self.assertNotIn('ui-card ui-query-card no-print', source)
                title = source.split('{% block title %}', 1)[1].split('{% endblock %}', 1)[0]
                self.assertNotIn('</section>', title)

    def test_changed_cascade_assets_have_fresh_versions(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        base = (root / 'templates/base.html').read_text(encoding='utf-8')
        for name in ('shared_components.css', 'shared_components.js'):
            self.assertIn(name + "' %}?v=20261014-results-workflow", base)
        self.assertIn("project_layout.css' %}?v=20261014-bcc-timesheet-final", base)
        self.assertIn("print_forms.css' %}?v=20261014-dispatch-register", base)
        worker = (root / 'static/js/service-worker.js').read_text(encoding='utf-8')
        self.assertIn('ihrms-static-v19-planning-20261014', worker)

    def test_reset_filter_excludes_scope_and_empty_values(self):
        from django.http import QueryDict
        from apps.common.templatetags.ui_components import ui_has_filters
        self.assertFalse(ui_has_filters(QueryDict('metric=active&page=2&q='),'q,status'))
        self.assertTrue(ui_has_filters(QueryDict('metric=active&q=abc'),'q,status'))

    def test_decision_filters_keep_recipient_scope_and_pagination_parameters(self):
        from apps.document.models import PersonnelDecision
        hr=self.user('HR_MANAGER',True)
        recipient=self.user('EMPLOYEE',True)
        for i in range(26):
            PersonnelDecision.objects.create(employee=hr.employee,template_slug='salary-decision',
                decision_no='needle & '+str(i),decision_date=date(2026,10,13),status='Draft')
        self.client.force_login(hr)
        response=self.client.get(reverse('portal:personnel_decision_list'),{'q':'needle &','status':'Draft'})
        self.assertEqual(response.context['page_obj'].paginator.count,26)
        self.assertContains(response,'q=needle%20%26&amp;status=Draft&amp;page=2')
        self.client.force_login(recipient)
        response=self.client.get(reverse('portal:personnel_decision_list'))
        self.assertEqual(response.status_code,403)
        director=self.user('DIRECTOR',True)
        self.client.force_login(director)
        response=self.client.get(reverse('portal:personnel_decision_list'))
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'name="status"')
        self.assertNotContains(response,'needle &amp;')
        self.client.force_login(recipient)
        for name in ('report_hub','report_budget','report_headcount'):
            self.assertEqual(self.client.get(reverse('portal:'+name)).status_code,302)

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
