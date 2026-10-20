"""Three synthetic HTTP business workflows; browsers and live data are not used."""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from apps.portal import tests as portal_tests
from apps.hrm.models import Employee
from apps.attendance.models import TimesheetEntry, MonthlyAttendanceSummary
from apps.leave.models import LeaveRequest, LeaveApproval, LeaveType, LeaveBalance


class BusinessWorkflowScenarioTests(TestCase):
    make_employee = portal_tests.PortalSensitiveWorkflowTests.make_employee
    make_user = portal_tests.PortalSensitiveWorkflowTests.make_user

    @classmethod
    def setUpTestData(cls):
        portal_tests.PortalSensitiveWorkflowTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.staff = self.make_employee('UAT-STAFF')
        self.hr = self.make_employee('UAT-HR')
        self.staff_user = self.make_user('EMPLOYEE', self.staff, 'uat-staff')
        self.hr_user = self.make_user('HR_MANAGER', self.hr, 'uat-hr')

    def login_form(self, user, name, args=()):
        self.client.force_login(user)
        response = self.client.get(reverse(name, args=args))
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', self.client.cookies)

    def post(self, name, data, args=()):
        return self.client.post(reverse(name, args=args), data, HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)

    def test_01_hr_create_edit_and_reject_duplicate_employee(self):
        self.login_form(self.hr_user, 'portal:hr_employee_create')
        data = dict(employee_code='UAT-NEW', first_name='Giả định', last_name='Kiểm thử', full_name='Nhân viên giả định UAT', date_of_birth='1990-01-01', gender='Other', national_id='UAT-FAKE-ID-001', company_email='uat-new@example.test', mobile_phone='0900000000', join_date='2026-10-01', department=str(self.department.pk), position=str(self.employee_position.pk), employment_status='Active')
        response = self.post('portal:hr_employee_create', data)
        new = Employee.objects.get(employee_code='UAT-NEW')
        self.assertRedirects(response, reverse('portal:hr_employee_detail', args=(new.pk,)))
        self.assertEqual(new.created_by_id, self.hr_user.pk)
        self.login_form(self.hr_user, 'portal:hr_employee_edit', (new.pk,))
        data.update(mobile_phone='0911111111', address='Địa chỉ giả định kiểm thử')
        response = self.post('portal:hr_employee_edit', data, (new.pk,))
        self.assertRedirects(response, reverse('portal:hr_employee_detail', args=(new.pk,)))
        new.refresh_from_db()
        self.assertEqual(new.mobile_phone, '0911111111')
        self.assertEqual(new.address, data['address'])
        self.assertEqual(new.modified_by_id, self.hr_user.pk)
        self.assertContains(self.client.get(reverse('portal:hr_employee_detail', args=(new.pk,))), '0911111111')
        response = self.post('portal:hr_employee_create', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Employee.objects.filter(employee_code='UAT-NEW').count(), 1)
        self.client.force_login(self.staff_user)
        data['mobile_phone'] = '0999999999'
        self.assertEqual(self.post('portal:hr_employee_edit', data, (new.pk,)).status_code, 302)
        new.refresh_from_db()
        self.assertEqual(new.mobile_phone, '0911111111')
        print('CASE 1 PASS: HR create, edit, persisted detail, duplicate and unauthorized edit rejected.')

    def test_02_timesheet_save_update_and_owner_soft_delete(self):
        self.login_form(self.staff_user, 'portal:timesheet_month')
        data = dict(work_date='2026-10-02', hours='8', task_description='Lập hồ sơ công việc giả định')
        self.assertEqual(self.post('portal:timesheet_entry_create', data).status_code, 302)
        row = TimesheetEntry.objects.get(employee=self.staff)
        self.assertEqual(row.hours, Decimal('8'))
        response = self.client.get(reverse('portal:timesheet_month'), {'year':2026, 'month':10})
        self.assertContains(response, data['task_description'])
        monthly = dict(year=2026, month=10, sick_days='1', maternity_days='0', compensatory_days='0', annual_leave_days='0', unpaid_leave_days='0')
        self.assertEqual(self.post('portal:timesheet_summary_update', monthly).status_code, 302)
        summary = MonthlyAttendanceSummary.objects.get(employee=self.staff, year=2026, month=10)
        self.assertEqual(summary.sick_days, Decimal('1'))
        monthly['sick_days'] = '2'
        self.assertEqual(self.post('portal:timesheet_summary_update', monthly).status_code, 302)
        summary.refresh_from_db()
        self.assertEqual(summary.sick_days, Decimal('2'))
        self.assertEqual(summary.status, 'Pending')
        self.assertContains(
            self.client.get(reverse('portal:timesheet_month'), {'year': 2026, 'month': 10}),
            'name="sick_days" value="2.0"',
        )
        self.client.force_login(self.hr_user)
        self.assertEqual(self.post('portal:timesheet_entry_delete', {}, (row.pk,)).status_code, 404)
        self.assertTrue(TimesheetEntry.objects.filter(pk=row.pk).exists())
        self.client.force_login(self.staff_user)
        self.assertEqual(self.client.get(reverse('portal:timesheet_entry_delete', args=(row.pk,))).status_code, 405)
        self.assertEqual(self.post('portal:timesheet_entry_delete', {}, (row.pk,)).status_code, 302)
        self.assertFalse(TimesheetEntry.objects.filter(pk=row.pk).exists())
        self.assertTrue(TimesheetEntry.all_objects.get(pk=row.pk).is_deleted)
        self.assertNotContains(self.client.get(reverse('portal:timesheet_month'), {'year':2026, 'month':10}), data['task_description'])
        print('CASE 2 PASS: timesheet save, monthly summary edit, owner POST soft delete, cross-user/GET deletion blocked.')

    def test_03_leave_submission_overlap_and_approval(self):
        self.staff.manager = self.hr
        self.staff.save(update_fields=['manager'])
        leave_type, _ = LeaveType.objects.get_or_create(leave_type_code='AL', defaults={'leave_type_name':'Phép năm kiểm thử', 'is_paid':True})
        LeaveBalance.objects.create(employee=self.staff, year=2026, allocated_days=12)
        self.login_form(self.staff_user, 'portal:leave_create')
        data = dict(leave_type=str(leave_type.pk), from_date='2026-11-02', to_date='2026-11-03', reason='Đơn nghỉ giả định UAT')
        self.assertEqual(self.post('portal:leave_create', data).status_code, 302)
        leave = LeaveRequest.objects.get(employee=self.staff)
        self.assertEqual(leave.status, 'Pending')
        self.assertEqual(leave.total_days, Decimal('2'))
        self.assertContains(self.client.get(reverse('portal:leave_list')), data['reason'])
        self.assertEqual(self.post('portal:leave_create', data).status_code, 200)
        self.assertEqual(LeaveRequest.objects.filter(employee=self.staff).count(), 1)
        self.assertEqual(self.post('portal:leave_approve', {'decision':'Approved'}, (leave.pk,)).status_code, 302)
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Pending')
        self.client.force_login(self.hr_user)
        self.assertEqual(self.client.get(reverse('portal:leave_approval_list')).status_code, 200)
        self.assertEqual(self.post('portal:leave_approve', {'decision':'Approved'}, (leave.pk,)).status_code, 302)
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Approved')
        self.assertEqual(LeaveApproval.objects.filter(leave_request=leave, approver=self.hr).count(), 1)
        self.assertEqual(self.post('portal:leave_approve', {'decision':'Approved'}, (leave.pk,)).status_code, 404)
        self.assertEqual(LeaveApproval.objects.filter(leave_request=leave).count(), 1)
        self.client.force_login(self.staff_user)
        self.assertContains(self.client.get(reverse('portal:leave_list')), 'Đã duyệt')
        print('CASE 3 PASS: leave submission, day count, overlap rejection, correct HR approval, employee/repeated approval blocked.')
