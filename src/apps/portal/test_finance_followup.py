"""Finance follow-up regression gates against real role guards and populated lists."""
from datetime import date
from pathlib import Path
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from apps.payroll.models import EmployeeSalary, EmployeeDependent
from apps.portal.test_finance_ui import FinanceUITests
from apps.portal.ui_test_helpers import assert_internal_links
from apps.portal.test_personal_ui import Forms


class FinanceFollowupTests(FinanceUITests):
    def finance_fixture(self):
        user = self.user('FINANCE_OFFICER', True)
        EmployeeSalary.objects.create(employee=user.employee, current_basic_salary=12345678, effective_date=date(2026,1,1))
        EmployeeDependent.objects.create(employee=user.employee, full_name='Người phụ thuộc giả', relationship='Con', registered_from=date(2026,1,1))
        self.client.force_login(user)
        return user

    def test_salary_names_do_not_link_outside_finance_scope(self):
        user = self.finance_fixture()
        response = self.client.get(reverse('portal:finance_salary_list'))
        self.assertNotContains(response, 'href="'+reverse('portal:hr_employee_detail',args=[user.employee_id]))
        self.assertContains(response, '1 mức lương')

    def test_calculate_all_has_confirmation_and_original_post_contract(self):
        self.finance_fixture()
        response = self.client.get(reverse('portal:finance_payroll_run',args=[self.period.pk]))
        form = next(f for f in Forms(response.content.decode()).forms if f['attrs'].get('action')==reverse('portal:finance_payroll_calculate_all',args=[self.period.pk]))
        self.assertEqual(form['attrs'].get('method'), 'post')
        self.assertIn('data-ui-confirm',form['attrs'])
        self.assertEqual({x.get('name') for x in form['fields']},{'csrfmiddlewaretoken'})

    def test_links_and_query_baseline(self):
        self.finance_fixture()
        for route in ('finance_salary_list','finance_dependent_list','finance_tax_config','finance_period_list','finance_payroll_run'):
            url=reverse('portal:'+route,args=[self.period.pk] if route=='finance_payroll_run' else [])
            with CaptureQueriesContext(connection) as queries:
                response=self.client.get(url)
            print('FINANCE_QUERY_COUNT',route,len(queries))
            self.assertLessEqual(len(queries), {'finance_salary_list':14,'finance_dependent_list':10,'finance_tax_config':11,'finance_period_list':9,'finance_payroll_run':15}[route])
            self.assertEqual(response.status_code,200)
            assert_internal_links(self,response)

    def test_templates_use_shared_components_without_old_classes(self):
        root=Path(__file__).parent/'templates/portal'
        for route in ('finance_salary_list','finance_dependent_list','finance_tax_config','finance_period_list','finance_payroll_run','hr_employee_list'):
            text=(root/(route+'.html')).read_text(encoding='utf-8')
            self.assertNotIn('class=""',text)
            self.assertNotRegex(text,r'finance-[123]-')
            self.assertNotRegex(text,r'class="[^"]*(?:\bpx-\d|\bpy-\d|\btext-xs|hover:bg-)')
            if route.startswith('finance_'):
                self.assertIn('ui/page_header.html',text)
