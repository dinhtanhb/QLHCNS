from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.contract.models import Contract, ContractAppendix, ContractType
from apps.document.models import PersonnelDecision
from apps.hrm.models import Employee, EmployeePromotion, EmployeeTransfer, EmployeeReward, EmployeeDiscipline
from apps.notification.models import Notification
from apps.organization.models import Department, Position
from apps.payroll.models import EmployeeSalary
from apps.security.models import SecurityEvent
from .tests_hcns import HCNSFormTests as Fixtures


class HRWorkflowTests(TestCase):
    user = classmethod(Fixtures.user.__func__)

    @classmethod
    def setUpTestData(cls):
        Fixtures.setUpTestData.__func__(cls)
        cls.hr_manager_employee = Employee.objects.create(
            employee_code="WF-HR-MANAGER", first_name="HR", last_name="Manager", full_name="HR Manager Test",
            date_of_birth=date(1985, 1, 1), gender="Other", national_id="WF-HR-NATIONAL",
            company_email="workflow-hr-manager@example.test", mobile_phone="0000000001",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )
        cls.director_employee = Employee.objects.create(
            employee_code="WF-DIRECTOR", first_name="Test", last_name="Director", full_name="Director Test",
            date_of_birth=date(1980, 1, 1), gender="Other", national_id="WF-DIR-NATIONAL",
            company_email="workflow-director@example.test", mobile_phone="0000000002",
            join_date=date(2019, 1, 1), department=cls.department, position=cls.position,
        )
        cls.hr_manager = Fixtures.user.__func__(cls, "workflow-hr-manager", "HR_MANAGER", cls.hr_manager_employee)
        cls.director = Fixtures.user.__func__(cls, "workflow-director", "DIRECTOR", cls.director_employee)

    def setUp(self):
        self.client.force_login(self.superuser)
        self.employee = self.employees[0]

    def history(self, kind, **data):
        return self.client.post(reverse('portal:hr_employee_history_create', args=[self.employee.pk, kind]), data)

    def test_future_salary_save_draft_and_historical_export(self):
        old = EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=10000000, effective_date=date(2020, 1, 1))
        response = self.client.post(reverse('portal:hr_salary_create', args=[self.employee.pk]),
                                    {'current_basic_salary': '23000000', 'effective_date': '2090-01-01', 'next': 'hcns'})
        record = EmployeeSalary.objects.exclude(pk=old.pk).get(employee=self.employee)
        self.assertIn(f'salary_id={record.pk}', response.url)
        draft = self.client.get(response.url)
        self.assertEqual(draft.status_code, 200)
        self.assertEqual(draft.context['form'].initial['salary'], Decimal('23000000'))
        self.assertEqual(draft.context['form'].initial['effective_date'], date(2090, 1, 1))
        old.refresh_from_db()
        self.assertEqual(old.end_date, date(2089, 12, 31))
        draft_url = reverse('portal:hcns_draft', args=['salary-decision'])
        current = self.client.get(draft_url, {'employee_id': self.employee.pk})
        self.assertEqual(current.context['form'].initial['salary'], Decimal('10000000'))
        historical = self.client.get(draft_url, {'salary_id': old.pk})
        self.assertEqual(historical.context['form'].initial['salary'], Decimal('10000000'))
        exported = self.client.get(draft_url, {'salary_id': record.pk, 'export': '1'})
        self.assertEqual(exported.status_code, 200)
        self.assertIn('attachment', exported['Content-Disposition'])

    def test_future_promotion_and_transfer_keep_recorded_targets(self):
        position = Position.objects.create(position_code='NEW', position_name='Synthetic manager')
        department = Department.objects.create(department_code='NEW', department_name='Synthetic destination', organization=self.department.organization)
        response = self.history('promotion', new_position=position.pk, effective_date='2090-01-01', reason='Synthetic', next='hcns')
        record = EmployeePromotion.objects.get(employee=self.employee)
        self.assertIn(f'promotion_id={record.pk}', response.url)
        draft = self.client.get(response.url)
        self.assertEqual(draft.context['form'].initial['new_position'], position.pk)
        self.assertEqual(draft.context['form'].initial['decision_action'], 'Bổ nhiệm')
        self.assertEqual(draft.context['form'].initial['position'], self.position.pk)
        response = self.history('transfer', to_department=department.pk, effective_date='2090-02-01', reason='Synthetic', next='hcns')
        draft = self.client.get(response.url)
        self.assertEqual(draft.context['form'].initial['department'], department.pk)
        self.assertEqual(draft.context['form'].initial['workplace'], department.pk)
        self.assertEqual(draft.context['form'].initial['effective_date'], date(2090, 2, 1))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.department_id, self.department.pk)
        self.assertEqual(self.employee.position_id, self.position.pk)

    def test_invalid_history_never_creates_records(self):
        for kind, model, data in [
            ('transfer', EmployeeTransfer, {'to_department': self.department.pk, 'effective_date': 'bad'}),
            ('promotion', EmployeePromotion, {'new_position': 999999, 'effective_date': '2090-01-01'}),
            ('reward', EmployeeReward, {'reward_type': '', 'reward_date': '2090-01-01'}),
            ('discipline', EmployeeDiscipline, {'discipline_type': 'Synthetic', 'discipline_date': 'bad'}),
        ]:
            with self.subTest(kind=kind):
                response = self.history(kind, **data, next='hcns')
                self.assertEqual(response.status_code, 302)
                self.assertNotIn('hcns', response.url)
                self.assertFalse(model.objects.filter(employee=self.employee).exists())
        self.history('unknown')
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position_id, self.position.pk)

    def test_invalid_salary_rolls_back_and_rejects_backdated_transition(self):
        old = EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=100, effective_date=date(2020, 1, 1))
        for amount, day in [('-1', '2090-01-01'), ('200', '2019-01-01'), ('200', 'bad')]:
            self.client.post(reverse('portal:hr_salary_create', args=[self.employee.pk]), {'current_basic_salary': amount, 'effective_date': day, 'next': 'hcns'})
            old.refresh_from_db()
            self.assertEqual(old.status, 'Active')
            self.assertIsNone(old.end_date)
            self.assertEqual(EmployeeSalary.objects.filter(employee=self.employee).count(), 1)

    def test_source_access_wrong_template_multiple_deleted_and_staff_denial(self):
        salary = EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=100, effective_date=date(2020, 1, 1))
        url = reverse('portal:hcns_draft', args=['salary-decision'])
        self.assertEqual(self.client.get(reverse('portal:hcns_draft', args=['appointment-decision']), {'salary_id': salary.pk}).status_code, 404)
        self.assertEqual(self.client.get(url, {'salary_id': salary.pk, 'employee_id': self.employee.pk}).status_code, 404)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url, {'salary_id': salary.pk}).status_code, 403)
        for action in ('transfer', 'promotion', 'reward', 'discipline'):
            self.history(action, effective_date='2090-01-01')
        self.assertFalse(EmployeeTransfer.objects.exists())
        self.assertFalse(EmployeePromotion.objects.exists())
        self.client.force_login(self.superuser)
        self.employee.is_deleted = True
        self.employee.save(update_fields=['is_deleted'])
        self.assertEqual(self.client.get(url, {'salary_id': salary.pk}).status_code, 404)

    def test_reward_discipline_navigation_and_contract_renewal_rollback(self):
        self.history('reward', reward_type='Synthetic', reward_date='2090-01-01', amount='50')
        self.history('discipline', discipline_type='Synthetic', discipline_date='2090-01-01')
        self.assertEqual(EmployeeReward.objects.count(), 1)
        self.assertEqual(EmployeeDiscipline.objects.count(), 1)
        detail = self.client.get(reverse('portal:hr_employee_detail', args=[self.employee.pk]))
        self.assertContains(detail, 'name="next"', count=3)
        self.assertContains(detail, f'employee_id={self.employee.pk}')
        listing = self.client.get(reverse('portal:hr_employee_list'))
        self.assertContains(listing, '#khenthuong')
        self.assertContains(listing, '#kyluat')
        form = self.client.get(reverse('portal:hr_contract_create'), {'employee_id': self.employee.pk})
        self.assertEqual(form.context['selected_employee'], str(self.employee.pk))
        ct = ContractType.objects.create(contract_type_code='SYN', contract_type_name='Synthetic')
        contract = Contract.objects.create(employee=self.employee, contract_type=ct, contract_no='SYN-1', start_date=date(2020, 1, 1), end_date=date(2025, 1, 1), basic_salary=100, status='Active')
        renew_url = reverse('portal:hr_contract_renew', args=[self.employee.pk])
        self.client.post(renew_url, {'new_end_date': '2019-01-01'})
        contract.refresh_from_db()
        self.assertEqual(contract.end_date, date(2025, 1, 1))
        self.assertFalse(ContractAppendix.objects.exists())
        self.client.post(renew_url, {'new_end_date': '2090-01-01'})
        contract.refresh_from_db()
        self.assertEqual(contract.end_date, date(2090, 1, 1))
        self.assertEqual(ContractAppendix.objects.count(), 1)
        for day in ('', '2080-01-01', '2090-01-01'):
            self.client.post(renew_url, {'new_end_date': day})
            self.assertEqual(ContractAppendix.objects.count(), 1)

    def test_contract_create_and_appendix_preserve_employee_and_validate(self):
        ct = ContractType.objects.create(contract_type_code='SYN', contract_type_name='Synthetic')
        url = reverse('portal:hr_contract_create')
        data = {'employee': self.employee.pk, 'contract_type': ct.pk, 'contract_no': 'SYN-2',
                'start_date': '2020-01-01', 'end_date': '2030-01-01', 'basic_salary': '100', 'status': 'Active'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        contract = Contract.objects.get(contract_no='SYN-2')
        self.assertEqual(contract.employee_id, self.employee.pk)
        appendix_url = reverse('portal:hr_contract_appendix_create', args=[contract.pk])
        self.client.post(appendix_url, {'appendix_no': 'SYN-PL', 'effective_date': 'bad', 'description': 'Synthetic'})
        self.assertFalse(ContractAppendix.objects.exists())
        self.client.post(appendix_url, {'appendix_no': 'SYN-PL', 'effective_date': '2030-01-01', 'description': 'Synthetic'})
        self.assertEqual(ContractAppendix.objects.get().contract_id, contract.pk)
        detail = self.client.get(reverse('portal:hr_employee_detail', args=[self.employee.pk]))
        self.assertContains(detail, 'SYN-PL')
        self.assertContains(detail, appendix_url)
        data.update(contract_no='INVALID', end_date='2019-01-01')
        self.client.post(url, data)
        self.assertFalse(Contract.objects.filter(contract_no='INVALID').exists())

    def _save_salary_decision(self, user=None, **overrides):
        user = user or self.hr
        self.client.force_login(user)
        data = Fixtures.data(self, "salary-decision", action="save_decision", full_name=str(self.employee.pk),
            decision_no="QD-TEST-001", document_date="2026-10-06", effective_date="2026-11-01",
            salary="23000000", **overrides)
        return self.client.post(reverse("portal:hcns_draft", args=["salary-decision"]), data)

    def test_decision_snapshot_reopens_and_exports_with_original_employee(self):
        duplicate = self.employees[1]
        duplicate.full_name = self.employee.full_name
        duplicate.save(update_fields=["full_name"])
        response = self._save_salary_decision()
        self.assertEqual(response.status_code, 302)
        decision = PersonnelDecision.objects.get()
        self.assertEqual(decision.employee_id, self.employee.pk)
        self.assertEqual(decision.status, "Draft")
        self.assertEqual(decision.content_snapshot["values"]["full_name"], self.employee.full_name)
        self.assertEqual(decision.history.get().action, "DraftCreated")
        self.assertFalse(Notification.objects.exists())

        edit_url = reverse("portal:hcns_draft", args=["salary-decision"])
        wrong_template = reverse("portal:hcns_draft", args=["appointment-decision"])
        self.assertEqual(self.client.get(wrong_template, {"decision_id": decision.pk}).status_code, 404)
        edit = self.client.get(edit_url, {"decision_id": decision.pk})
        self.assertEqual(edit.status_code, 200)
        self.assertEqual(edit.context["form"].initial["full_name"], self.employee.pk)
        self.assertContains(edit, "Lưu bản nháp quyết định")
        exported = self.client.get(reverse("portal:personnel_decision_word", args=[decision.pk]))
        self.assertEqual(exported.status_code, 200)
        self.assertIn("attachment", exported["Content-Disposition"])
        self.assertEqual(SecurityEvent.objects.filter(resource="hcns:salary-decision").count(), 1)

    def test_draft_save_cannot_revert_a_concurrent_submission(self):
        from apps.document.hcns import views
        self._save_salary_decision()
        decision = PersonnelDecision.objects.get()
        original = views._save_personnel_decision

        def submit_before_save(*args, **kwargs):
            PersonnelDecision.objects.filter(pk=decision.pk).update(status="PendingApproval")
            return original(*args, **kwargs)

        data = Fixtures.data(self, "salary-decision", action="save_decision", full_name=str(self.employee.pk), salary="24000000")
        url = reverse("portal:hcns_draft", args=["salary-decision"]) + f"?decision_id={decision.pk}"
        with patch.object(views, "_save_personnel_decision", side_effect=submit_before_save):
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 422)
        self.assertTrue(response.context["form"].non_field_errors())
        decision.refresh_from_db()
        self.assertEqual(decision.status, "PendingApproval")
        self.assertEqual(decision.content_snapshot["values"]["salary"], "23000000")
        self.assertEqual(decision.history.count(), 1)

    def test_long_decision_number_returns_form_error_without_writes(self):
        self.client.force_login(self.hr)
        data = Fixtures.data(self, "salary-decision", action="save_decision", full_name=str(self.employee.pk), decision_no="X" * 101)
        response = self.client.post(reverse("portal:hcns_draft", args=["salary-decision"]), data)
        self.assertEqual(response.status_code, 422)
        self.assertIn("decision_no", response.context["form"].errors)
        self.assertFalse(PersonnelDecision.objects.exists())

    def test_edit_preserves_salary_source_without_refreshing_snapshot(self):
        self.client.force_login(self.hr)
        salary = EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=23000000, effective_date=date(2026, 11, 1))
        url = reverse("portal:hcns_draft", args=["salary-decision"])
        data = Fixtures.data(self, "salary-decision", action="save_decision", full_name=str(self.employee.pk), salary="23000000")
        self.client.post(url + f"?salary_id={salary.pk}", data)
        decision = PersonnelDecision.objects.get()
        label = decision.content_snapshot["source_label"]
        EmployeeSalary.objects.filter(pk=salary.pk).update(current_basic_salary=25000000)
        edit_url = url + f"?decision_id={decision.pk}"
        response = self.client.get(edit_url)
        self.assertTrue(response.context["workflow_source"])
        self.assertEqual(response.context["form"].initial["salary"], "23000000")
        self.assertEqual(self.client.post(edit_url, data).status_code, 302)
        decision.refresh_from_db()
        self.assertEqual(decision.content_snapshot["source_query"], f"salary_id={salary.pk}")
        self.assertEqual(decision.content_snapshot["source_label"], label)
        data["full_name"] = str(self.employees[1].pk)
        self.assertEqual(self.client.post(edit_url, data).status_code, 302)
        decision.refresh_from_db()
        self.assertEqual(decision.employee_id, self.employees[1].pk)
        self.assertEqual(decision.content_snapshot["source_query"], f"employee_id={self.employees[1].pk}")

    def test_saved_decision_loads_layout_and_print_controls(self):
        self._save_salary_decision()
        decision = PersonnelDecision.objects.get()
        response = self.client.get(reverse("portal:personnel_decision_detail", args=[decision.pk]))
        self.assertContains(response, "css/hcns_forms.css")
        self.assertContains(response, "js/hcns_forms.js")
        self.assertContains(response, decision.content_snapshot["rendered"]["profile"]["page_css"])
        self.assertContains(response, 'id="hcns-export-name"')
        self.assertContains(response, '<section class="no-print border-t')

    def test_decision_approval_issue_and_private_pdf_access(self):
        response = self._save_salary_decision(self.hr_manager)
        decision = PersonnelDecision.objects.get()
        self.client.post(reverse("portal:personnel_decision_transition", args=[decision.pk, "submit"]))
        decision.refresh_from_db()
        self.assertEqual(decision.status, "PendingApproval")
        approver_notice = Notification.objects.get(
            employee=self.director_employee, notification_type="personnel-decision"
        )
        self.assertEqual(approver_notice.link, reverse("portal:personnel_decision_detail", args=[decision.pk]))
        self.assertIn("QD-TEST-001", approver_notice.message)
        self.assertFalse(Notification.objects.filter(employee=self.hr_manager_employee).exists())

        self.client.post(reverse("portal:personnel_decision_transition", args=[decision.pk, "approve"]))
        decision.refresh_from_db()
        self.assertEqual(decision.status, "PendingApproval")
        self.assertFalse(Notification.objects.filter(employee=self.hr_manager_employee).exists())

        self.client.force_login(self.director)
        pending = self.client.get(reverse("portal:personnel_decision_list"))
        self.assertContains(pending, "QD-TEST-001")
        self.client.post(reverse("portal:personnel_decision_transition", args=[decision.pk, "approve"]), {"comment": "Đã kiểm tra"})
        decision.refresh_from_db()
        self.assertEqual(decision.status, "Approved")
        self.assertEqual(self.client.get(reverse("portal:personnel_decision_detail", args=[decision.pk])).status_code, 200)
        approval_notice = Notification.objects.get(
            employee=self.hr_manager_employee, notification_type="personnel-decision"
        )
        self.assertEqual(approval_notice.title, "Quyết định đã được duyệt")
        self.assertIn("Đã kiểm tra", approval_notice.message)

        self.client.force_login(self.hr)
        invalid_pdf = SimpleUploadedFile("wrong.docx", b"not a PDF", content_type="application/pdf")
        self.client.post(
            reverse("portal:personnel_decision_transition", args=[decision.pk, "issue"]),
            {"issued_file": invalid_pdf},
        )
        decision.refresh_from_db()
        self.assertEqual(decision.status, "Approved")

        signed_pdf = SimpleUploadedFile("QD-TEST-001.pdf", b"%PDF-1.4\nsynthetic signed copy", content_type="application/pdf")
        response = self.client.post(
            reverse("portal:personnel_decision_transition", args=[decision.pk, "issue"]),
            {"comment": "Đã ký", "issued_file": signed_pdf},
        )
        self.assertEqual(response.status_code, 302)
        decision.refresh_from_db()
        self.assertEqual(decision.status, "Issued")
        self.assertIsNotNone(decision.issued_at)
        self.assertEqual(list(decision.history.values_list("action", flat=True)), ["DraftCreated", "Submitted", "Approved", "Issued"])
        self.assertTrue(Notification.objects.filter(
            employee=self.employee, notification_type="personnel-decision", title="Quyết định nhân sự đã ban hành"
        ).exists())
        self.assertEqual(Notification.objects.filter(employee=self.hr_manager_employee).count(), 2)

        private_download = self.client.get(decision.issued_file.url)
        self.assertEqual(private_download.status_code, 200)
        self.assertEqual(b"".join(private_download.streaming_content), b"%PDF-1.4\nsynthetic signed copy")
        self.client.force_login(self.director)
        self.assertEqual(self.client.get(decision.issued_file.url).status_code, 200)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(decision.issued_file.url).status_code, 404)
        self.assertEqual(self.client.get(reverse("portal:personnel_decision_detail", args=[decision.pk])).status_code, 403)
        self.hr.role = self.staff.role
        self.hr.save(update_fields=["role"])
        self.client.force_login(self.hr)
        employee_detail = self.client.get(reverse("portal:personnel_decision_detail", args=[decision.pk]))
        self.assertEqual(employee_detail.status_code, 200)
        self.assertTrue(employee_detail.context["is_employee_recipient"])
        self.assertEqual(employee_detail.context["unread_notification_count"], 1)
        self.assertContains(employee_detail, "Tải PDF đã ký")
        self.assertNotContains(employee_detail, "Tải Word")
        self.assertNotContains(employee_detail, "Lịch sử xử lý")
        self.assertNotContains(employee_detail, "BẢN SOẠN THẢO")
        self.assertContains(employee_detail, "Quyết định đã ban hành")
        employee_pdf = self.client.get(decision.issued_file.url)
        self.assertEqual(employee_pdf.status_code, 200)
        self.assertEqual(b"".join(employee_pdf.streaming_content), b"%PDF-1.4\nsynthetic signed copy")

    def test_rejection_requires_comment_and_saved_rejection_returns_to_draft(self):
        self._save_salary_decision()
        decision = PersonnelDecision.objects.get()
        self.client.post(reverse("portal:personnel_decision_transition", args=[decision.pk, "submit"]))

        self.client.force_login(self.director)
        self.client.post(reverse("portal:personnel_decision_transition", args=[decision.pk, "reject"]))
        decision.refresh_from_db()
        self.assertEqual(decision.status, "PendingApproval")
        self.client.post(reverse("portal:personnel_decision_transition", args=[decision.pk, "reject"]), {"comment": "Bổ sung căn cứ"})
        decision.refresh_from_db()
        self.assertEqual(decision.status, "Rejected")
        rejection_notice = Notification.objects.get(
            employee=self.employee, title="Quyết định bị từ chối"
        )
        self.assertIn("Bổ sung căn cứ", rejection_notice.message)

        self.client.force_login(self.hr)
        edit_url = reverse("portal:hcns_draft", args=["salary-decision"])
        edit_response = self.client.get(edit_url, {"decision_id": decision.pk})
        self.assertEqual(edit_response.status_code, 200)
        data = Fixtures.data(self, "salary-decision", action="save_decision", full_name=str(self.employee.pk),
            decision_no="QD-TEST-001", document_date="2026-10-06", effective_date="2026-11-01", salary="24000000")
        response = self.client.post(f"{edit_url}?decision_id={decision.pk}", data)
        self.assertEqual(response.status_code, 302)
        decision.refresh_from_db()
        self.assertEqual(decision.status, "Draft")
        self.assertEqual(decision.content_snapshot["values"]["salary"], "24000000")
        self.assertEqual(list(decision.history.values_list("action", flat=True)), ["DraftCreated", "Submitted", "Rejected", "DraftUpdated"])
