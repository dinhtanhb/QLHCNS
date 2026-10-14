"""Planning presentation and genuine role/form boundaries."""
from datetime import date
from pathlib import Path
from decimal import Decimal
import re
from django.test import TestCase
from django.urls import reverse
from apps.portal.test_home_dashboard import HomeDashboardTests
from apps.portal.ui_test_helpers import assert_internal_links
from apps.portal.test_personal_ui import Forms
from apps.kpi.models import KPIPeriod,KPITemplate,EmployeeKPI
from apps.planning.models import TrainingCourse,TrainingEnrollment


class PlanningUITests(TestCase):
    user=HomeDashboardTests.user
    @classmethod
    def setUpTestData(cls):
        HomeDashboardTests.setUpTestData.__func__(cls)
        cls.period=KPIPeriod.objects.create(year=2026,month=10)
        cls.template=KPITemplate.objects.create(kpi_name='Chỉ tiêu giả',weight=Decimal('30'))
        cls.course=TrainingCourse.objects.create(course_code='PLAN-TEST',course_name='Khóa học giả',start_date=date(2026,10,1))

    def test_templates_use_shared_components_and_preserve_post_csrf(self):
        root=Path(__file__).parent/'templates/portal'
        for stem in ('holiday_list','training_my_list','kpi_score_list','kpi_assign_create'):
            text=(root/(stem+'.html')).read_text(encoding='utf-8')
            with self.subTest(template=stem):
                self.assertIn('portal/planning_base.html',text)
                self.assertIn('ui/page_header.html',text)
                self.assertNotIn('class=""',text);self.assertNotIn('style="',text)
                self.assertNotRegex(text,r'class="[^"]*\b(?:px-\d|py-\d|text-xs|text-sm|bg-gray-|grid-cols-|space-y-)')
                self.assertNotRegex(text,r'[\U0001f300-\U0001faff\u2600-\u27ff]')
                for form in re.findall(r'<form\b.*?</form>',text,re.S):
                    if 'method="post"' in form:self.assertIn('{% csrf_token %}',form)
                if '<table' in text:
                    self.assertIn('scope="col"',text);self.assertIn('<caption',text)

    def test_roles_links_labels_and_kpi_zero_year_display(self):
        for role in ('EMPLOYEE','DEPT_MANAGER','HR_OFFICER','HR_MANAGER','DIRECTOR','FINANCE_OFFICER','SYS_ADMIN','SUPERUSER','UNLINKED'):
            user=self.user('SUPER_ADMIN' if role=='SUPERUSER' else 'EMPLOYEE' if role=='UNLINKED' else role,role!='UNLINKED')
            if role=='SUPERUSER':user.is_superuser=True;user.save(update_fields=['is_superuser'])
            if user.employee_id:
                EmployeeKPI.objects.create(employee=user.employee,kpi_template=self.template,kpi_period=self.period,target=Decimal('100'),actual=Decimal('0'))
                TrainingEnrollment.objects.create(employee=user.employee,course=self.course)
            self.client.force_login(user)
            for name in ('holiday_list','training_my_list','kpi_score_list','kpi_assign_create','event_list','report_hub'):
                response=self.client.get(reverse('portal:'+name))
                with self.subTest(role=role,page=name):
                    self.assertIn(response.status_code,(200,302))
                    if response.status_code!=200:continue
                    assert_internal_links(self,response)
                    for form in Forms(response.content.decode()).forms:
                        if form['attrs'].get('method','').lower()=='post':self.assertTrue(any(f.get('name')=='csrfmiddlewaretoken' for f in form['fields']))
                    if name=='kpi_score_list':
                        self.assertContains(response,'Áp dụng');self.assertContains(response,'2026');self.assertNotContains(response,'2.026')
                        self.assertContains(response,'id="kpi-actual-')
                        self.assertContains(response,'value="0.00"')
                    if name=='training_my_list' and user.employee_id:self.assertContains(response,'Đã đăng ký')

    def test_kpi_filter_reset_and_unique_field_labels(self):
        user=self.user('HR_MANAGER',True);self.client.force_login(user)
        for _ in range(2):EmployeeKPI.objects.create(employee=user.employee,kpi_template=self.template,kpi_period=self.period,target=Decimal('100'),actual=Decimal('0'))
        html=self.client.get(reverse('portal:kpi_score_list'),{'period':self.period.pk}).content.decode()
        self.assertIn('Xóa lọc',html)
        ids=re.findall(r'<input[^>]+id="(kpi-actual-\d+)"',html)
        self.assertEqual(len(ids),2);self.assertEqual(len(set(ids)),2)
        for id in ids:self.assertIn('for="'+id+'"',html)
