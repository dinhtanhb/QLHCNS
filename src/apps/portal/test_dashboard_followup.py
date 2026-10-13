"""Phase-one follow-up: truthful fallback cards, contracts and unchanged reads."""
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch
from django.db import connection
from django.template import engines
from django.template.loaders.locmem import Loader
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from apps.portal import test_home_dashboard as fixtures
from apps.portal import dashboard_data as data
from apps.portal.home_presentation import home_presentation
from apps.contract.models import Contract, ContractType
from apps.hrm.models import Employee
from apps.planning.models import HeadcountPlan, with_headcounts


class DashboardFollowupTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_duplicate_cards_only_removed_when_same_ready_or_empty_count(self):
        user = self.user('HR_MANAGER')
        for state in ('ready','empty','partial','error',None):
            with self.subTest(state=state):
                snapshot={'sections':{'status':{'state':state,'counts':{'active':0}},'queue':{'state':state,'rows':[{'value':0}]}}}
                result=home_presentation(user,dict(is_management_view=True,total_employees=0,pending_leave_approvals=0,
                                                  pending_recruitment=2,pending_documents=3,open_tasks_company=4,dashboard_snapshot=snapshot))
                cards=result['home_groups'][0]['cards'];labels=[c['label'] for c in cards]
                self.assertEqual('Nhân viên đang làm việc' in labels,state not in ('ready','empty'))
                self.assertEqual('Đơn nghỉ chờ duyệt' in labels,state not in ('ready','empty'))
                self.assertIn('Đề xuất tuyển dụng chờ duyệt',labels)
                for card in cards:
                    if card['label']=='Nhân viên đang làm việc':self.assertIsNone(card['href'])
        different=home_presentation(user,dict(is_management_view=True,total_employees=5,pending_leave_approvals=4,
            dashboard_snapshot={'sections':{'status':{'state':'ready','counts':{'active':3}},'queue':{'state':'ready','rows':[{'value':2}]}}}))
        self.assertIn('Nhân viên Active theo tổng quan cũ',[c['label'] for c in different['home_groups'][0]['cards']])
        self.assertIn('Đơn nghỉ chờ duyệt theo tổng quan cũ',[c['label'] for c in different['home_groups'][0]['cards']])
        manager=self.user('DEPT_MANAGER',True)
        cards=home_presentation(manager,dict(is_manager_view=True,dept_employee_count=7,dept_pending_leaves=1))['home_groups'][0]['cards']
        self.assertIsNone(cards[0]['href'])

    def test_zero_ready_contract_note_and_role_gate(self):
        self.assertEqual(data.metric('active','Active',0,'Scope','Note')['state'],'ready')
        hr=self.user('HR_MANAGER',True);other=self.user('EMPLOYEE',True)
        kind=ContractType.objects.create(contract_type_code='FOLLOW',contract_type_name='Giả')
        Contract.objects.create(employee=other.employee,contract_type=kind,contract_no='FOLLOW',start_date='2020-01-01',basic_salary=0,status='Draft')
        snap=data.dashboard_snapshot(hr,hr.employee)
        self.assertEqual(snap['uncontracted']['value'],1)
        for item in snap['metrics']:
            if item['key'] in ('managed','active'):self.assertIn('Gồm cả hồ sơ chưa có hợp đồng;',item['note'])
        self.assertNotIn('uncontracted',data.dashboard_snapshot(other,other.employee))
        self.client.force_login(hr)
        self.assertContains(self.client.get(reverse('portal:dashboard')),'Có 1 hồ sơ chưa có hợp đồng.')

    def test_active_sources_same_with_without_plan_deleted_and_nonactive(self):
        hr=self.user('HR_MANAGER',True);deleted=self.user('DELETED',True);deleted.employee.delete()
        for status in ('Probation','OnLeave','Resigned'):
            user=self.user(status,True);Employee.objects.filter(pk=user.employee_id).update(employment_status=status)
        today=timezone.localdate()
        without=data._headcount(today)['rows'][0]['actual']
        plan=HeadcountPlan.objects.create(department=self.department,year=today.year,planned_headcount=5)
        self.assertEqual(without,1)
        self.assertEqual(with_headcounts(HeadcountPlan.objects.filter(pk=plan.pk)).get().actual_headcount,without)
        self.assertEqual(data._headcount(today)['rows'][0]['actual'],without)
        Employee.objects.filter(pk=hr.employee_id).update(employment_status='Resigned')
        self.assertEqual(data._headcount(today)['rows'][0]['actual'],0)
        self.assertEqual(with_headcounts(HeadcountPlan.objects.filter(pk=plan.pk)).get().actual_headcount,0)
        # Current schema requires DepartmentID. Exercise the read-side unassigned
        # branch with a count stub; do not change that schema to create a fixture.
        original=Employee.objects.filter
        def scoped(*args,**kwargs):
            if kwargs.get('department__isnull'):return SimpleNamespace(count=lambda:2)
            return original(*args,**kwargs)
        with patch.object(Employee._meta.get_field('department'),'null',True), patch.object(Employee.objects,'filter',side_effect=scoped):
            rows=data._headcount(today)['rows']
        self.assertEqual(next(r for r in rows if r['id'] is None)['actual'],2)

    def test_cleaned_templates_keep_links_and_queries(self):
        user=self.user('HR_MANAGER',True);self.client.force_login(user)
        paths={'portal/hr_employee_detail.html':reverse('portal:hr_employee_detail',args=[user.employee_id]),
               'portal/timesheet_month.html':reverse('portal:timesheet_month'),
               'reporting/dashboard.html':reverse('reporting:dashboard')}
        root=Path(__file__).resolve().parents[2]
        evidence=Path(os.environ['TEMP'])/'ihrms-followup-20261013'
        engine=engines['django'].engine
        measurements={}
        for template,url in paths.items():
            filename=root/('templates/'+template if template.startswith('reporting/') else 'apps/portal/templates/'+template)
            text=filename.read_text(encoding='utf-8')
            self.assertNotRegex(text,r'text-(?:gray|blue|green|red|sm|xs)|border-gray|bg-(?:white|gray|yellow)|#[0-9a-fA-F]{3,8}\b|[📊⚙🏠👥📑📨⚠📥⬇]')
            before=(evidence/filename.name).read_text(encoding='utf-8-sig') if (evidence/filename.name).exists() else text
            self.client.get(url)
            with patch.object(engine,'template_loaders',[Loader(engine,{template:before})]+engine.template_loaders):
                with CaptureQueriesContext(connection) as old:
                    old_response=self.client.get(url)
            with CaptureQueriesContext(connection) as new:
                response=self.client.get(url)
            self.assertEqual(response.status_code,200)
            count=lambda captured:sum(q['sql'].lstrip().upper().startswith('SELECT') for q in captured)
            self.assertEqual(count(new),count(old))
            from html.parser import HTMLParser
            class Links(HTMLParser):
                def __init__(self):super().__init__();self.links=[]
                def handle_starttag(self,tag,attrs):
                    if tag=='a':self.links.append(dict(attrs).get('href'))
            a,b=Links(),Links();a.feed(old_response.content.decode());b.feed(response.content.decode());self.assertEqual(a.links,b.links)
            measurements[template]={'before':count(old),'after':count(new)}
        print('FOLLOWUP_PAGE_QUERY_COUNTS='+json.dumps(measurements))

    def test_eight_role_query_matrix(self):
        matrix={}
        # Reconstruct only the previous status aggregate without the optional
        # uncontracted note, in memory. Do not rewrite a working-tree file.
        namespace=dict(vars(data))
        source=Path(data.__file__).read_text(encoding='utf-8')
        source=source.replace('            if has_permission(user, "manage_hr"):\n                block["uncontracted"] = qs.filter(~Exists(Contract.objects.filter(employee_id=OuterRef("pk")))).count()\n','')
        source=source.replace('    unassigned = (Employee.objects.filter(department__isnull=True, employment_status="Active").count()\n                  if Employee._meta.get_field("department").null else 0)', '    unassigned = Employee.objects.filter(department__isnull=True, employment_status="Active").count()')
        exec(compile(source,'<pre-note-query-baseline>','exec'),namespace)
        for role in ('EMPLOYEE','DEPT_MANAGER','HR_OFFICER','HR_MANAGER','DIRECTOR','FINANCE_OFFICER','SYS_ADMIN','SUPER_ADMIN'):
            for linked in (False,True):
                user=self.user(role,linked);self.client.force_login(user);self.client.get(reverse('portal:dashboard'))
                with patch.object(data,'dashboard_snapshot',namespace['dashboard_snapshot']):
                    with CaptureQueriesContext(connection) as baseline:
                        self.client.get(reverse('portal:dashboard'))
                with CaptureQueriesContext(connection) as queries:
                    self.client.get(reverse('portal:dashboard'))
                count=sum(q['sql'].lstrip().upper().startswith('SELECT') for q in queries)
                self.assertLessEqual(count,17,(role,linked))
                old=sum(q['sql'].lstrip().upper().startswith('SELECT') for q in baseline)
                matrix[f'{role}-{linked}']={'before_note':old,'after':count}
        print('FOLLOWUP_QUERY_MATRIX='+json.dumps(matrix))
