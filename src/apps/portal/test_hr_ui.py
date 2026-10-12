"""HR presentation regressions using synthetic fixtures and existing permissions."""
from datetime import date
from django.test import TestCase
from django.urls import reverse
from apps.portal import test_home_dashboard as home_fixtures
from apps.portal.test_personal_ui import Forms
from apps.lifecycle.models import ChecklistTemplate, ChecklistTemplateItem, EmployeeLifecycleCase, LifecycleChecklistItem
from apps.document.models import Document, DocumentCategory

class HRUITests(TestCase):
    user = home_fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        home_fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_hr_forms_keep_sensitive_fields_under_existing_guard(self):
        hr = self.user("HR_MANAGER", True)
        self.client.force_login(hr)
        response = self.client.get(reverse("portal:hr_employee_create"))
        self.assertContains(response, 'class="ui-page ui-hr"')
        forms = Forms(response.content.decode()).forms
        form = next(f for f in forms if "national_id" in {x.get("name") for x in f["fields"]})
        fields = {x["name"]: x for x in form["fields"]}
        self.assertIn("csrfmiddlewaretoken", fields)
        self.assertEqual(set(fields), {"csrfmiddlewaretoken", "employee_code", "first_name", "last_name", "full_name", "date_of_birth", "gender", "national_id", "tax_code", "social_insurance_no", "company_email", "personal_email", "mobile_phone", "address", "join_date", "leave_date", "department", "position", "job_title", "manager", "employment_status"})
        self.assertIn("required", fields["national_id"])
        self.assertNotIn("required", fields["tax_code"])
        self.assertTrue(all(f.get("id") for name, f in fields.items() if name != "csrfmiddlewaretoken"))
        employee = self.user("EMPLOYEE", True)
        self.client.force_login(employee)
        response = self.client.get(reverse("portal:hr_employee_create"))
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(self.client.get(reverse("portal:hr_employee_list")), 'name="national_id"')
        self.assertEqual(self.client.get(reverse("portal:hr_contract_list")).status_code, 403)

    def test_contract_constraints_and_selected_employee(self):
        hr = self.user("HR_OFFICER", True)
        self.client.force_login(hr)
        response = self.client.get(reverse("portal:hr_contract_create"), {"employee_id":hr.employee.pk})
        self.assertEqual(response.status_code, 200)
        form = next(f for f in Forms(response.content.decode()).forms if "contract_no" in {x.get("name") for x in f["fields"]})
        fields = {x["name"]:x for x in form["fields"]}
        self.assertEqual(set(fields), {"csrfmiddlewaretoken", "employee", "contract_type", "contract_no", "start_date", "end_date", "basic_salary", "status"})
        self.assertIn("required", fields["basic_salary"])
        self.assertNotIn("min", fields["basic_salary"])
        self.assertNotIn("required", fields["end_date"])
        self.assertEqual(response.context['selected_employee'], str(hr.employee.pk))

    def test_approval_post_values_and_director_permission(self):
        category = DocumentCategory.objects.create(category_code="HR-TEST",category_name="Tài liệu giả")
        doc = Document.objects.create(document_no="HR-TEST",document_name="Tài liệu giả",category=category,status="PendingApproval")
        director = self.user("DIRECTOR",True)
        self.client.force_login(director)
        response = self.client.get(reverse("portal:document_approval_list"))
        forms = [f for f in Forms(response.content.decode()).forms if f['attrs'].get('action') == reverse("portal:document_approve",args=[doc.pk])]
        self.assertEqual(len(forms),2)
        self.assertEqual([next(x['value'] for x in f['fields'] if x.get('name')=='decision') for f in forms],['Approved','Rejected'])
        self.assertTrue(all('data-ui-confirm' in f['attrs'] for f in forms))
        self.assertContains(response, 'id="ui-confirm-dialog"',count=1)
        employee = self.user("EMPLOYEE",True)
        self.client.force_login(employee)
        self.assertEqual(self.client.get(reverse("portal:document_approval_list")).status_code,302)
        doc.refresh_from_db()
        self.assertEqual(doc.status,'PendingApproval')

    def test_lifecycle_pending_guard_and_submitter_fields(self):
        hr = self.user("HR_MANAGER",True)
        tpl = ChecklistTemplate.objects.create(template_code="HR-TEST",template_name="Mẫu giả",template_type="Onboarding")
        ti = ChecklistTemplateItem.objects.create(template=tpl,sequence=1,item_name="Đầu việc giả",responsible_role_code="HR_MANAGER")
        case = EmployeeLifecycleCase.objects.create(employee=hr.employee,template=tpl,case_type="Onboarding",effective_date=date(2026,10,1),triggering_event_ref="HR-TEST")
        item = LifecycleChecklistItem.objects.create(case=case,template_item=ti,item_name=ti.item_name,responsible_role_code=ti.responsible_role_code,assigned_to_user=hr)
        self.client.force_login(hr)
        response = self.client.get(reverse("portal:lifecycle_case_detail",args=[case.pk]))
        form = next(f for f in Forms(response.content.decode()).forms if f['attrs'].get('action')==reverse("portal:lifecycle_item_update",args=[item.pk]))
        self.assertEqual([(x['name'],x['value']) for x in form['buttons']], [('action','done'),('action','skip')])
        self.assertEqual({x.get('name') for x in form['fields']},{'csrfmiddlewaretoken','skip_reason'})
        item.status='Done';item.save(update_fields=['status'])
        response = self.client.get(reverse("portal:lifecycle_case_detail",args=[case.pk]))
        self.assertNotContains(response,'name="skip_reason"')
        employee=self.user("EMPLOYEE",True);self.client.force_login(employee)
        self.assertEqual(self.client.get(reverse("portal:lifecycle_case_detail",args=[case.pk])).status_code,403)
