"""Regression tests for owner-approved review fixes; synthetic data only."""
from django.test import TestCase, Client
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import transaction, IntegrityError
from apps.portal import tests as fixture
from apps.office.models import SupplyItem, SupplyRequest, SupplyRequestItem
from apps.attendance.models import TimesheetEntry, MonthlyAttendanceSummary
from apps.asset.models import Asset, AssetType, AssetAllocation
from apps.leave.models import LeaveType, LeaveRequest
from apps.payroll.models import Payroll, PayrollPeriod, Payslip
from apps.organization.models import Department
from apps.task.models import Task

class ApprovedReviewRegressionTests(TestCase):
    make_employee = fixture.PortalSensitiveWorkflowTests.make_employee
    make_user = fixture.PortalSensitiveWorkflowTests.make_user
    @classmethod
    def setUpTestData(cls):
        fixture.PortalSensitiveWorkflowTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.emp = self.make_employee('REVIEW-EMP')
        self.user = self.make_user('EMPLOYEE', self.emp, 'review-employee')
        self.hr = self.make_user('HR_MANAGER', self.make_employee('REVIEW-HR'), 'review-hr')
        self.hr.is_staff = True
        self.hr.save(update_fields=['is_staff'])

    def test_ip_threshold_blocks_password_spraying_but_coworker_success_keeps_other_failures(self):
        from axes.models import AccessAttempt
        from django.utils import timezone
        AccessAttempt.objects.create(username="spray-other", ip_address="127.0.0.1", user_agent="",
            http_accept="", path_info="/portal/login/", attempt_time=timezone.now(), failures_since_start=49)
        self.client.post(reverse("portal:login"), {"username":"spray-next", "password":"wrong"})
        response = self.client.post(reverse("portal:login"), {"username":self.hr.username,"password":"test-password"})
        self.assertEqual(response.status_code,429)
        self.assertNotIn("_auth_user_id",self.client.session)

    def test_valid_coworker_does_not_clear_other_username_lock(self):
        for _ in range(5):
            self.client.post(reverse("portal:login"), {"username":self.user.username,"password":"wrong"})
        self.assertEqual(self.client.post(reverse("portal:login"),
            {"username":self.hr.username,"password":"test-password"}).status_code,302)
        self.client.logout()
        self.assertEqual(self.client.post(reverse("portal:login"),
            {"username":self.user.username,"password":"test-password"}).status_code,429)

    def test_graph_outage_is_controlled_503_without_internal_details(self):
        from unittest.mock import patch
        from django.core.files.base import ContentFile
        from apps.m365.graph_client import GraphAPIError
        kind=LeaveType.objects.create(leave_type_code="REVIEW-NET",leave_type_name="Test")
        leave=LeaveRequest.objects.create(employee=self.emp,leave_type=kind,from_date=date(2026,10,5),to_date=date(2026,10,5))
        leave.attachment.save("test.pdf",ContentFile(b"%PDF test"))
        self.client.force_login(self.user)
        with patch("apps.m365.storage.ConfiguredStorage._open",side_effect=GraphAPIError("private token/URL",status_code=429,retry_after="17")):
            response=self.client.get(leave.attachment.url)
        self.assertEqual(response.status_code,503)
        self.assertEqual(response["Retry-After"],"17")
        self.assertNotContains(response,"private token",status_code=503)

    def test_duplicate_supply_lines_with_sufficient_stock_issue_once(self):
        item, req = self.supply(10,"Approved",[4,4])
        self.client.force_login(self.hr)
        self.client.post(reverse("portal:supply_request_issue",args=[req.pk]))
        item.refresh_from_db(); req.refresh_from_db()
        self.assertEqual((item.quantity_in_stock,req.status),(2,"Issued"))
        self.client.post(reverse("portal:supply_request_issue",args=[req.pk]))
        item.refresh_from_db(); self.assertEqual(item.quantity_in_stock,2)

    def test_database_rejects_negative_stock_and_rolls_back(self):
        from django.db import IntegrityError, transaction
        item, req = self.supply(5,"Approved",[1])
        with self.assertRaises(IntegrityError), transaction.atomic():
            SupplyItem.objects.filter(pk=item.pk).update(quantity_in_stock=-1)
        item.refresh_from_db(); self.assertEqual(item.quantity_in_stock,5)

    def test_day_total_across_projects_cannot_exceed_24(self):
        from apps.project.models import Project
        project = Project.objects.create(project_code="REVIEW-PROJ",project_name="Test")
        TimesheetEntry.objects.create(employee=self.emp,work_date=date(2026,10,2),hours=20)
        self.client.force_login(self.user)
        self.client.post(reverse("portal:timesheet_entry_create"),
            {"work_date":"2026-10-02","hours":"8","project":project.pk})
        self.assertEqual(TimesheetEntry.objects.filter(employee=self.emp).count(),1)

    def test_restore_then_delete_allocation_queryset_updates_asset(self):
        asset, row = self.asset()
        AssetAllocation.objects.filter(pk=row.pk).delete(user=self.hr)
        asset.refresh_from_db(); self.assertEqual(asset.status,"Available")
        AssetAllocation.all_objects.filter(pk=row.pk).restore(user=self.hr)
        asset.refresh_from_db(); self.assertEqual(asset.status,"InUse")
        self.assertEqual(AssetAllocation.objects.filter(asset=asset).count(),1)

    def test_employee_cannot_delete_approved_timesheet(self):
        row=TimesheetEntry.objects.create(employee=self.emp,work_date=date(2026,9,26),hours=8)
        MonthlyAttendanceSummary.objects.create(employee=self.emp,year=2026,month=9,status="Approved")
        self.client.force_login(self.user)
        response=self.client.post(reverse("portal:timesheet_entry_delete",args=[row.pk]))
        self.assertEqual(response.status_code,302)
        self.assertTrue(TimesheetEntry.objects.filter(pk=row.pk).exists())

    def test_summary_update_checks_status_from_locked_read(self):
        from unittest.mock import Mock, patch
        from django.contrib.messages import get_messages
        summary=MonthlyAttendanceSummary.objects.create(employee=self.emp,year=2026,month=9)
        approved=MonthlyAttendanceSummary.objects.get(pk=summary.pk)
        approved.status="Approved"
        locked_query=Mock()
        locked_query.get_or_create.return_value=(approved,False)
        self.client.force_login(self.user)
        # Deterministic locked-read simulation, not a SQL Server concurrency test.
        with patch.object(MonthlyAttendanceSummary.objects,"select_for_update",return_value=locked_query):
            response=self.client.post(reverse("portal:timesheet_summary_update"),{"year":"2026","month":"9","sick_days":"0"})
        self.assertTrue(any("không thể tự sửa" in str(message) for message in get_messages(response.wsgi_request)))
        summary.refresh_from_db(); self.assertEqual(summary.status,"Pending")
        self.assertEqual(summary.sick_days,Decimal("0"))

    def test_summary_for_locked_period_is_controlled_and_not_created(self):
        period=self.period();period.status="Locked";period.save()
        self.client.force_login(self.user)
        response=self.client.post(reverse("portal:timesheet_summary_update"),{"year":"2026","month":"10"})
        self.assertEqual(response.status_code,302)
        self.assertFalse(MonthlyAttendanceSummary.objects.filter(employee=self.emp,year=2026,month=10).exists())

    def test_period_with_missing_payable_employee_cannot_close(self):
        self.rates()
        period=self.period()
        row=Payroll.objects.create(payroll_period=period,employee=self.emp,basic_salary=10000000)
        row.calculate();row.save()
        self.client.force_login(self.make_user("FINANCE_OFFICER",self.make_employee("REVIEW-FIN"),"review-finance"))
        self.client.post(reverse("portal:finance_payroll_lock",args=[period.pk]))
        period.refresh_from_db();self.assertEqual(period.status,"Open")
        self.assertFalse(Payslip.objects.filter(payroll__payroll_period=period).exists())

    def test_department_manager_cannot_assign_foreign_employee_kpi_in_admin(self):
        from apps.kpi.models import EmployeeKPI, KPIPeriod, KPITemplate
        manager=self.manager()
        other=Department.objects.create(organization=self.organization,department_code="REVIEW-OTHER",department_name="Other")
        self.emp.department=other;self.emp.save(update_fields=["department"])
        self.client.force_login(manager)
        response=self.client.post(reverse("admin:kpi_employeekpi_add"),{
            "employee":self.emp.pk,"kpi_template":KPITemplate.objects.create(kpi_name="Test",weight=100).pk,
            "kpi_period":KPIPeriod.objects.create(year=2026,month=10).pk,"target":"100","_save":"Save"})
        self.assertEqual(response.status_code,200)
        self.assertIn("employee",response.context["adminform"].form.errors)
        self.assertFalse(EmployeeKPI.objects.filter(employee=self.emp).exists())

    def test_department_manager_cannot_create_foreign_department_event_in_admin(self):
        from apps.planning.models import Event
        manager=self.manager()
        other=Department.objects.create(organization=self.organization,department_code="REVIEW-OTHER",department_name="Other")
        self.client.force_login(manager)
        response=self.client.post(reverse("admin:planning_event_add"),{
            "title":"Review Event","event_type":"Meeting","department":other.pk,
            "start_time_0":"2026-10-02","start_time_1":"09:00:00",
            "end_time_0":"2026-10-02","end_time_1":"10:00:00","_save":"Save"})
        self.assertEqual(response.status_code,200)
        self.assertIn("department",response.context["adminform"].form.errors)
        self.assertFalse(Event.objects.filter(title="Review Event").exists())

    def test_integrity_audit_is_read_only_and_rejects_legacy_invalid_hours(self):
        from django.core.management import call_command, CommandError
        from io import StringIO
        TimesheetEntry.objects.bulk_create([TimesheetEntry(employee=self.emp,work_date=date(2026,10,2),hours=48)])
        output=StringIO()
        with self.assertRaises(CommandError):
            call_command("audit_review_integrity",stdout=output)
        self.assertIn("invalid_timesheet_hours: 1",output.getvalue())
        self.assertNotIn(self.emp.full_name,output.getvalue())
        self.assertEqual(TimesheetEntry.objects.get(employee=self.emp).hours,Decimal("48"))

    def test_integrity_audit_passes_valid_data(self):
        from django.core.management import call_command
        from io import StringIO
        TimesheetEntry.objects.create(employee=self.emp,work_date=date(2026,10,2),hours=8)
        output=StringIO();call_command("audit_review_integrity",stdout=output)
        self.assertNotIn(": 1",output.getvalue())
        self.assertEqual(TimesheetEntry.objects.filter(employee=self.emp).count(),1)

    def rates(self):
        from apps.payroll.test_fixtures import create_calculation_rates
        create_calculation_rates()

    def test_calculated_payroll_can_close_but_changed_approved_days_require_recalculation(self):
        self.rates()
        period = self.period()
        row = Payroll.objects.create(payroll_period=period, employee=self.emp, basic_salary=10000000)
        row.calculate(); row.save()
        summary = MonthlyAttendanceSummary.objects.create(employee=self.emp,year=2026,month=10,
            status='Approved', unpaid_leave_days=1)
        self.client.force_login(self.make_user('FINANCE_OFFICER',self.make_employee('REVIEW-FIN'),'review-finance'))
        self.client.post(reverse('portal:finance_payroll_generate',args=[period.pk]))
        for other in Payroll.objects.filter(payroll_period=period).exclude(pk=row.pk):
            other.calculate(); other.save()
        self.client.post(reverse('portal:finance_payroll_lock',args=[period.pk]))
        period.refresh_from_db(); self.assertEqual(period.status,'Open')
        row.calculate(); row.save()
        self.client.post(reverse('portal:finance_payroll_lock',args=[period.pk]))
        period.refresh_from_db(); self.assertEqual(period.status,'Locked')
        self.assertTrue(Payslip.objects.filter(payroll=row).exists())

    def supply(self, qty, status, requests):
        item = SupplyItem.objects.create(item_code='REVIEW-ITEM',item_name='Test',quantity_in_stock=qty)
        req = SupplyRequest.objects.create(request_no='REVIEW-REQ',employee=self.emp,request_date=date(2026,10,2),status=status)
        for count in requests:
            SupplyRequestItem.objects.create(supply_request=req,item=item,quantity_requested=count)
        return item,req

    def period(self):
        return PayrollPeriod.objects.create(payroll_month=10,payroll_year=2026,start_date=date(2026,10,1),end_date=date(2026,10,31))

    def asset(self):
        kind = AssetType.objects.create(asset_type_code='REVIEW-KIND',asset_type_name='Test')
        asset = Asset.objects.create(asset_code='REVIEW-ASSET',asset_name='Test',asset_type=kind)
        allocation = AssetAllocation.objects.create(asset=asset,employee=self.emp,assigned_date=date(2026,10,1))
        return asset,allocation

    def manager(self):
        manager = self.make_user('DEPT_MANAGER',self.make_employee('REVIEW-MGR'),'review-manager')
        manager.is_staff = True
        manager.save(update_fields=['is_staff'])
        self.department.manager = manager.employee
        self.department.save(update_fields=['manager'])
        return manager

    def test_01_portal_rejects_duplicate_lines_exceeding_stock(self):
        item,req = self.supply(5,'Approved',[4,4])
        self.client.force_login(self.hr)
        self.client.post(reverse('portal:supply_request_issue',args=[req.pk]))
        item.refresh_from_db(); req.refresh_from_db()
        self.assertEqual((item.quantity_in_stock,req.status),(5,'Approved'))

    def test_02_admin_rejects_issue_exceeding_stock(self):
        item,req = self.supply(2,'Pending',[5])
        self.client.force_login(self.hr)
        self.client.post(reverse('admin:office_supplyrequest_changelist'),{'action':'approve_and_issue','_selected_action':str(req.pk)})
        item.refresh_from_db(); req.refresh_from_db()
        self.assertEqual((item.quantity_in_stock,req.status),(2,'Pending'))

    def test_03_cannot_lock_uncalculated_payroll(self):
        period = self.period()
        row = Payroll.objects.create(payroll_period=period,employee=self.emp,basic_salary=Decimal('10000000'))
        finance = self.make_user('FINANCE_OFFICER',self.make_employee('REVIEW-FIN'),'review-finance')
        self.client.force_login(finance)
        self.client.post(reverse('portal:finance_payroll_lock',args=[period.pk]))
        period.refresh_from_db()
        self.assertEqual(period.status,'Open')
        self.assertFalse(Payslip.objects.filter(payroll=row).exists())

    def test_04_cannot_lock_stale_payroll_after_input_edit(self):
        period = self.period()
        row = Payroll.objects.create(payroll_period=period,employee=self.emp,basic_salary=Decimal('1000'),gross_income=Decimal('1000'),net_income=Decimal('1000'))
        finance = self.make_user('FINANCE_OFFICER',self.make_employee('REVIEW-FIN'),'review-finance')
        self.client.force_login(finance)
        self.rates()
        row.calculate(); row.save()
        self.client.post(reverse('portal:finance_payroll_update_line',args=[row.pk]),{'allowance':'500','insurance_salary':'1000'})
        self.client.post(reverse('portal:finance_payroll_lock',args=[period.pk]))
        row.refresh_from_db();period.refresh_from_db()
        self.assertEqual((row.allowance,row.gross_income,row.net_income,period.status),(Decimal('500'),Decimal('1000'),Decimal('895'),'Open'))

    def test_05_department_manager_cannot_self_approve_leave_in_admin(self):
        manager = self.manager()
        kind = LeaveType.objects.create(leave_type_code='REVIEW-LEAVE',leave_type_name='Test')
        leave = LeaveRequest.objects.create(employee=manager.employee,leave_type=kind,from_date=date(2026,10,5),to_date=date(2026,10,5))
        self.client.force_login(manager)
        self.client.post(reverse('admin:leave_leaverequest_changelist'),{'action':'approve_selected','_selected_action':str(leave.pk)})
        leave.refresh_from_db()
        self.assertEqual(leave.status,'Pending')

    def test_06_department_manager_cannot_see_other_department_timesheets(self):
        manager = self.manager()
        other_dept = Department.objects.create(organization=self.organization,department_code='REVIEW-OTHER',department_name='Other')
        self.emp.department=other_dept;self.emp.save(update_fields=['department'])
        row = TimesheetEntry.objects.create(employee=self.emp,work_date=date(2026,10,2),hours=8)
        self.client.force_login(manager)
        response = self.client.get(reverse('admin:attendance_timesheetentry_changelist'))
        self.assertNotIn(row,list(response.context['cl'].queryset))

    def test_07_bad_timesheet_date_returns_controlled_response(self):
        client=Client(raise_request_exception=False)
        client.force_login(self.user)
        response=client.post(reverse('portal:timesheet_entry_create'),{'work_date':'not-a-date','hours':'8'})
        self.assertEqual(response.status_code,302)

    def test_08_negative_timesheet_hours_are_rejected(self):
        self.client.force_login(self.user)
        self.client.post(reverse('portal:timesheet_entry_create'),{'work_date':'2026-10-02','hours':'-4'})
        self.assertFalse(TimesheetEntry.objects.filter(employee=self.emp).exists())

    def test_09_48_hours_one_day_are_rejected(self):
        self.client.force_login(self.user)
        self.client.post(reverse('portal:timesheet_entry_create'),{'work_date':'2026-10-02','hours':'48'})
        self.assertFalse(TimesheetEntry.objects.filter(employee=self.emp).exists())

    def test_10_soft_delete_allocation_releases_asset(self):
        asset,allocation=self.asset()
        allocation.delete(user=self.hr)
        asset.refresh_from_db()
        self.assertFalse(AssetAllocation.objects.filter(asset=asset,return_date__isnull=True).exists())
        self.assertEqual(asset.status,'Available')

    def test_11_restore_allocation_cannot_bypass_overlap_check(self):
        asset,allocation=self.asset()
        allocation.delete(user=self.hr)
        Asset.objects.filter(pk=asset.pk).update(status='Available')
        AssetAllocation.objects.create(asset=asset,employee=self.hr.employee,assigned_date=date(2026,10,2))
        with self.assertRaises(ValidationError):
            allocation.restore(user=self.hr)
        self.assertEqual(AssetAllocation.objects.filter(asset=asset,return_date__isnull=True).count(),1)

    def test_12_deleted_payroll_cannot_download_payslip(self):
        period=self.period();period.status='Locked';period.save()
        row=Payroll.objects.create(payroll_period=period,employee=self.emp,basic_salary=1000,net_income=1000)
        slip=Payslip.objects.create(payroll=row)
        row.delete(user=self.hr)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('portal:payslip_pdf',args=[slip.pk])).status_code,404)

    def test_14_approved_timesheet_cannot_gain_credit_without_reapproval(self):
        from apps.attendance.services import compensatory_days_earned
        MonthlyAttendanceSummary.objects.create(employee=self.emp,year=2026,month=9,status='Approved')
        self.assertEqual(compensatory_days_earned(self.emp,2026),Decimal('0'))
        self.client.force_login(self.user)
        self.client.post(reverse('portal:timesheet_entry_create'),{'work_date':'2026-09-26','hours':'8'})
        self.assertEqual(compensatory_days_earned(self.emp,2026),Decimal('0'))

    def test_15_payroll_generation_rechecks_locked_state(self):
        from unittest.mock import patch
        period=self.period()
        finance=self.make_user('FINANCE_OFFICER',self.make_employee('REVIEW-FIN'),'review-finance')
        self.client.force_login(finance)
        manager=PayrollPeriod.objects
        original=manager.select_for_update
        def lock_between_reads(*args,**kwargs):
            PayrollPeriod.objects.filter(pk=period.pk).update(status='Locked')
            return original(*args,**kwargs)
        with patch.object(manager,'select_for_update',side_effect=lock_between_reads):
            self.client.post(reverse('portal:finance_payroll_generate',args=[period.pk]))
        period.refresh_from_db()
        self.assertEqual(period.status,'Locked')
        self.assertFalse(Payroll.objects.filter(payroll_period=period).exists())

    def test_16_five_failures_do_not_block_valid_coworker_behind_same_ip(self):
        for _ in range(5):
            self.client.post(reverse('portal:login'),{'username':self.user.username,'password':'wrong'})
        response=self.client.post(reverse('portal:login'),{'username':self.hr.username,'password':'test-password'})
        self.assertEqual(response.status_code,302)

    def test_17_missing_sharepoint_file_returns_404(self):
        from unittest.mock import patch
        from django.core.files.base import ContentFile
        from apps.m365.graph_client import GraphAPIError
        kind=LeaveType.objects.create(leave_type_code='REVIEW-FILE',leave_type_name='Test')
        leave=LeaveRequest.objects.create(employee=self.emp,leave_type=kind,from_date=date(2026,10,5),to_date=date(2026,10,5))
        leave.attachment.save('test.pdf',ContentFile(b'%PDF test'))
        client=Client(raise_request_exception=False)
        client.force_login(self.user)
        with patch('apps.m365.storage.ConfiguredStorage._open',side_effect=GraphAPIError('Missing file', status_code=404)):
            response=client.get(leave.attachment.url)
        self.assertEqual(response.status_code,404)

    def test_13_department_manager_cannot_create_cross_department_task_via_admin(self):
        manager=self.manager()
        other=Department.objects.create(organization=self.organization,department_code='REVIEW-OTHER',department_name='Other')
        self.emp.department=other;self.emp.save(update_fields=['department'])
        self.client.force_login(manager)
        response=self.client.post(reverse('admin:task_task_add'),{
            'task_code':'REVIEW-TASK','task_name':'Test','assigned_by_employee':str(manager.employee_id),
            'assigned_to_employee':str(self.emp.pk),'department':str(other.pk),'priority':'Normal','status':'Todo',
            'start_date':'2026-10-02','due_date':'2026-10-03',
            'comments-TOTAL_FORMS':'0','comments-INITIAL_FORMS':'0','comments-MIN_NUM_FORMS':'0','comments-MAX_NUM_FORMS':'1000',
            '_save':'Save'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(Task.objects.filter(task_code='REVIEW-TASK').exists())

