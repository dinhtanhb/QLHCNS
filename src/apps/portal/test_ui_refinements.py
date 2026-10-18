"""Directory contract gate and semantic year formatting regressions."""
from datetime import date
from django.test import TestCase
from django.template import Context, Template
from django.urls import reverse
from apps.contract.models import Contract, ContractType
from apps.portal import test_home_dashboard as home_fixtures
from apps.hrm.models import Employee


class UIRefinementTests(TestCase):
    user = home_fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        home_fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def contract(self, employee, status="Draft", number="UI-C1"):
        kind, _ = ContractType.objects.get_or_create(contract_type_code="UI-REF", defaults={"contract_type_name":"Loại giả"})
        return Contract.objects.create(employee=employee,contract_type=kind,contract_no=number,
            start_date=date(2020,1,1),end_date=date(2021,1,1),basic_salary=0,status=status)

    def test_directory_requires_contract_but_creation_can_select_uncontracted(self):
        hr=self.user("HR_MANAGER",True)
        uncontracted=self.user("EMPLOYEE",True)
        self.client.force_login(hr)
        page=self.client.get(reverse("portal:hr_employee_list"))
        self.assertEqual(page.context["page_obj"].paginator.count,0)
        create=self.client.get(reverse("portal:hr_contract_create"))
        self.assertContains(create,f'value="{uncontracted.employee_id}"')
        contract=self.contract(uncontracted.employee)
        page=self.client.get(reverse("portal:hr_employee_list"))
        self.assertEqual(page.context["page_obj"].paginator.count,1)
        self.assertContains(page,'popover="auto"')
        self.assertNotContains(page,'<details class="ui-row-menu">')
        # Multiple live contracts still produce one employee, not duplicate rows.
        extra=self.contract(uncontracted.employee,"Expired","UI-C2")
        self.assertEqual(self.client.get(reverse("portal:hr_employee_list")).context["page_obj"].paginator.count,1)
        contract.delete();extra.delete()
        self.assertEqual(self.client.get(reverse("portal:hr_employee_list")).context["page_obj"].paginator.count,0)
        self.assertTrue(Employee.objects.filter(pk=uncontracted.employee_id).exists())

    def test_contract_gate_keeps_role_scope_and_search(self):
        manager=self.user("DEPT_MANAGER",True)
        employee=self.user("EMPLOYEE",True)
        self.contract(employee.employee)
        self.client.force_login(manager)
        page=self.client.get(reverse("portal:hr_employee_list"),{"q":employee.employee.employee_code})
        self.assertEqual(page.context["page_obj"].paginator.count,1)
        self.assertNotContains(page,'popovertarget=')
        manager.employee.managed_departments.clear()
        self.assertEqual(self.client.get(reverse("portal:hr_employee_list")).context["page_obj"].paginator.count,0)
        self.client.force_login(employee)
        self.assertEqual(self.client.get(reverse("portal:hr_employee_list")).context["page_obj"].paginator.count,0)

    def test_years_are_not_grouped_while_quantities_remain_vietnamese(self):
        template=Template('{{ year|ui_year }}|{{ quantity|ui_number }}|{{ money|ui_number }}')
        self.assertEqual(template.render(Context(dict(year=2026,quantity=2026,money=5000000))),"2026|2.026|5.000.000")
        page=self.client
        hr=self.user("HR_MANAGER");page.force_login(hr)
        response=page.get(reverse("portal:report_headcount"),{"year":"2026"})
        self.assertContains(response,'value="2026"')
        self.assertNotContains(response,'2.026')

    def test_finance_short_fields_use_native_selects_without_narrowing_values(self):
        finance = self.user("FINANCE_OFFICER")
        self.client.force_login(finance)

        period_page = self.client.get(reverse("portal:finance_period_list"))
        self.assertContains(period_page, '<select id="period-month" name="payroll_month"')
        self.assertContains(period_page, '<option value="12">Tháng 12</option>')
        self.assertContains(period_page, '<option value="2000">2000</option>')
        self.assertContains(period_page, '<option value="2100">2100</option>')

        dependent_page = self.client.get(reverse("portal:finance_dependent_list"))
        self.assertContains(dependent_page, '<select id="dependent-relationship" name="relationship"')
        self.assertContains(dependent_page, '<option value="Con">Con</option>')
        self.assertContains(dependent_page, '<option value="Khác">Khác</option>')

    def test_deleted_employee_stays_hidden_even_with_live_contract(self):
        hr=self.user("HR_MANAGER",True)
        contract=self.contract(hr.employee)
        hr.employee.delete()
        self.client.force_login(hr)
        self.assertEqual(self.client.get(reverse("portal:hr_employee_list")).context["page_obj"].paginator.count,0)
