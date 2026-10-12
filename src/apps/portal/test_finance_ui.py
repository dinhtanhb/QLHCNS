"""Finance UI contracts; synthetic records and unchanged backend guards."""
from datetime import date
from html.parser import HTMLParser
from django.test import TestCase
from django.urls import reverse
from apps.portal import test_home_dashboard as fixtures
from apps.portal.test_personal_ui import Forms
from apps.payroll.models import PayrollPeriod, Payroll, PersonalIncomeTaxBracket


class Controls(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.inputs = []
        self.labels = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self.inputs.append(dict(attrs))
        elif tag == "label":
            self.labels.append(dict(attrs))


class FinanceUITests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.period = PayrollPeriod.objects.create(payroll_month=10, payroll_year=2026,
            start_date=date(2026,10,1), end_date=date(2026,10,31), status="Open")

    def test_external_payroll_fields_and_lock_confirmation_keep_contract(self):
        finance = self.user("FINANCE_OFFICER", True)
        row = Payroll.objects.create(employee=finance.employee, payroll_period=self.period,
            basic_salary="12345678", allowance="1000000")
        self.client.force_login(finance)
        response = self.client.get(reverse("portal:finance_payroll_run", args=[self.period.pk]))
        self.assertContains(response, "12.345.678 đ")
        parsed = Controls(response.content.decode())
        fields = [x for x in parsed.inputs if x.get("form") == "pf"+str(row.pk)]
        self.assertEqual({x["name"] for x in fields}, {"insurance_salary", "allowance", "overtime_amount", "overtime_tax_exempt_amount", "deduction_amount"})
        labels = {x.get("for") for x in parsed.labels}
        for field in fields:
            self.assertEqual(field["type"], "number")
            self.assertEqual(field["min"], "0")
            self.assertEqual(field["step"], "1")
            self.assertIn(field["id"], labels)
        forms = Forms(response.content.decode()).forms
        lock = next(f for f in forms if f["attrs"].get("action") == reverse("portal:finance_payroll_lock", args=[self.period.pk]))
        self.assertIn("data-ui-confirm", lock["attrs"])
        self.assertEqual({x.get("name") for x in lock["fields"]}, {"csrfmiddlewaretoken"})
        self.assertContains(response, 'id="ui-confirm-dialog"', count=1)
        self.assertNotContains(response, "onsubmit=")

    def test_locked_period_hides_write_fields_but_keeps_payslip_issue(self):
        finance = self.user("FINANCE_OFFICER", True)
        Payroll.objects.create(employee=finance.employee, payroll_period=self.period, basic_salary="12345678")
        self.period.status="Locked"; self.period.save(update_fields=["status"])
        self.client.force_login(finance)
        response = self.client.get(reverse("portal:finance_payroll_run", args=[self.period.pk]))
        for name in ("insurance_salary", "allowance", "overtime_amount", "overtime_tax_exempt_amount", "deduction_amount"):
            self.assertNotContains(response, 'name="'+name+'"')
        self.assertNotContains(response, 'action="'+reverse("portal:finance_payroll_lock",args=[self.period.pk])+'"')
        self.assertContains(response, 'action="'+reverse("portal:finance_payslip_issue",args=[self.period.pk])+'"')
        self.assertContains(response, "Đã khóa")
        employee = self.user("EMPLOYEE", True)
        self.client.force_login(employee)
        for route in ("finance_period_list", "finance_salary_list", "finance_tax_config", "finance_dependent_list"):
            self.assertEqual(self.client.get(reverse("portal:"+route)).status_code,302)

    def test_tax_forms_preserve_discriminators_constraints_and_zero_upper_bound(self):
        finance = self.user("FINANCE_OFFICER", True)
        PersonalIncomeTaxBracket.objects.create(effective_from=date(2026,1,1),bracket_no=1,
            income_from_monthly=0,income_to_monthly=0,tax_rate=0)
        self.client.force_login(finance)
        response = self.client.get(reverse("portal:finance_tax_config"))
        forms = [f for f in Forms(response.content.decode()).forms if any(x.get("name")=="form_type" for x in f["fields"])]
        self.assertEqual(len(forms),3)
        self.assertEqual([next(x["value"] for x in f["fields"] if x.get("name")=="form_type") for f in forms], ["insurance", "deduction", "bracket"])
        identifiers=[]
        for form in forms:
            self.assertIn("data-ui-form",form["attrs"])
            for field in form["fields"]:
                if field.get("type")=="hidden":
                    continue
                identifiers.append(field["id"])
                self.assertContains(response, 'for="'+field["id"]+'"')
                self.assertNotIn("min",field)
                if "rate" in field.get("name", ""):
                    self.assertEqual(field["step"], "0.01")
                if field.get("name")=="income_to_monthly":
                    self.assertNotIn("required",field)
        self.assertEqual(len(identifiers),len(set(identifiers)))
        self.assertNotContains(response,"Trở lên")
        self.assertContains(response,"0 đ")

    def test_dependent_form_keeps_required_names_and_visible_labels(self):
        finance = self.user("FINANCE_OFFICER", True)
        self.client.force_login(finance)
        response = self.client.get(reverse("portal:finance_dependent_list"))
        form = next(f for f in Forms(response.content.decode()).forms if "data-ui-form" in f["attrs"])
        fields = {x["name"]:x for x in form["fields"]}
        self.assertEqual(set(fields),{"csrfmiddlewaretoken","employee","full_name","relationship","registered_from"})
        for name in ("employee","full_name","relationship","registered_from"):
            self.assertIn("required",fields[name])
            self.assertContains(response,'for="'+fields[name]["id"]+'"')
