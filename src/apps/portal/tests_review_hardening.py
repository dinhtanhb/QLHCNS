"""Regression tests for direct access, malformed inputs and atomic dispatch entry."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.test import TestCase, TransactionTestCase, RequestFactory
from django.db import connection, close_old_connections
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test.utils import CaptureQueriesContext
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse

from apps.attendance.models import MonthlyAttendanceSummary
from apps.document.models import DispatchBook, DispatchTracking, OfficialDispatch
from apps.kpi.models import EmployeeKPI, KPIPeriod, KPITemplate
from apps.notification.models import Notification
from apps.office.models import SupplyRequest
from apps.organization.models import Department
from apps.portal import tests as portal_tests
from apps.recruitment.models import Candidate, RecruitmentRequest
from apps.security.models import User
from apps.planning.models import AnnualBudget, Event, HeadcountPlan, TrainingCourse, with_headcounts
from apps.procurement.models import ProcurementRequest, ProcurementItem
from apps.attendance.models import TimesheetEntry, Holiday
from apps.leave.models import LeaveBalance, LeaveRequest, LeaveType
from apps.notification.services import notify_many


class ReviewHardeningTests(TestCase):
    setUpTestData = classmethod(portal_tests.PortalSensitiveWorkflowTests.setUpTestData.__func__)
    make_employee = portal_tests.PortalSensitiveWorkflowTests.make_employee
    make_user = portal_tests.PortalSensitiveWorkflowTests.make_user

    def setUp(self):
        self.employee = self.make_employee('REVIEW-STAFF')

    def test_employee_and_staff_flag_cannot_read_candidates(self):
        candidate = Candidate.objects.create(candidate_code='REVIEW-CANDIDATE', full_name='Test Candidate',
                                             phone_number='0000000000', email='candidate@example.test')
        user = self.make_user('EMPLOYEE', self.employee, 'review-reader')
        for staff_flag in (False, True):
            with self.subTest(staff_flag=staff_flag):
                user.is_staff = staff_flag
                user.save(update_fields=['is_staff'])
                self.client.force_login(user)
                for url in (reverse('portal:hr_candidate_list'), reverse('portal:hr_candidate_detail', args=[candidate.pk])):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 403)
                    self.assertNotContains(response, 'candidate@example.test', status_code=403)

    def test_hr_can_read_candidates(self):
        candidate = Candidate.objects.create(candidate_code='REVIEW-HR-CANDIDATE', full_name='HR Candidate',
                                             phone_number='0000000000', email='candidate@example.test')
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-hr'))
        self.assertEqual(self.client.get(reverse('portal:hr_candidate_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('portal:hr_candidate_detail', args=[candidate.pk])).status_code, 200)

    def test_recruitment_manager_cannot_post_outside_managed_departments(self):
        other = Department.objects.create(department_code='REVIEW-RECRUIT-OTHER', department_name='Other', organization=self.organization)
        self.department.manager = self.employee
        self.department.save(update_fields=['manager'])
        user = self.make_user('DEPT_MANAGER', self.employee, 'review-recruit-manager')
        self.client.force_login(user)
        data = {'request_code': 'REVIEW-RECRUIT', 'department': other.pk,
                'position': self.employee_position.pk, 'required_quantity': '1', 'required_date': '2026-11-01'}
        url = reverse('portal:recruitment_create')
        self.client.post(url, data)
        self.assertFalse(RecruitmentRequest.objects.exists())
        data['department'] = self.department.pk
        self.client.post(url, data)
        self.assertEqual(RecruitmentRequest.objects.get().department_id, self.department.pk)

    def test_unlinked_manager_has_no_recruitment_or_task_scope(self):
        self.client.force_login(self.make_user('DEPT_MANAGER', None, 'review-unlinked-manager'))
        recruitment = self.client.get(reverse('portal:recruitment_create'))
        self.assertEqual(list(recruitment.context['departments']), [])
        tasks = self.client.get(reverse('portal:task_create'))
        self.assertEqual(list(tasks.context['candidates']), [])
        self.client.post(reverse('portal:recruitment_create'), {
            'request_code': 'REVIEW-UNLINKED', 'department': self.department.pk,
            'position': self.employee_position.pk, 'required_quantity': '1', 'required_date': '2026-11-01'})
        self.assertFalse(RecruitmentRequest.objects.exists())

    def test_kpi_manager_cannot_update_other_department_or_without_employee(self):
        other_department = Department.objects.create(department_code='REVIEW-OTHER', department_name='Other',
                                                     organization=self.organization)
        target = self.make_employee('REVIEW-KPI-TARGET')
        target.department = other_department
        target.save(update_fields=['department'])
        self.department.manager = self.employee
        self.department.save(update_fields=['manager'])
        template = KPITemplate.objects.create(kpi_name='Review KPI', weight=100)
        period = KPIPeriod.objects.create(year=2026, month=10)
        result = EmployeeKPI.objects.create(employee=target, kpi_template=template, kpi_period=period, target=100)
        user = self.make_user('DEPT_MANAGER', self.employee, 'review-kpi-manager')
        for linked in (True, False):
            with self.subTest(linked=linked):
                if not linked:
                    user.employee = None
                    user.save(update_fields=['employee'])
                self.client.force_login(user)
                self.assertEqual(self.client.post(reverse('portal:kpi_score_update', args=[result.pk]), {'actual': '99'}).status_code, 404)
                result.refresh_from_db()
                self.assertIsNone(result.actual)
                self.assertFalse(Notification.objects.filter(employee=target).exists())

    def test_kpi_manager_can_update_managed_department(self):
        self.department.manager = self.employee
        self.department.save(update_fields=['manager'])
        target = self.make_employee('REVIEW-KPI-OWN')
        result = EmployeeKPI.objects.create(employee=target,
            kpi_template=KPITemplate.objects.create(kpi_name='Own KPI', weight=100),
            kpi_period=KPIPeriod.objects.create(year=2026, month=10), target=100)
        self.client.force_login(self.make_user('DEPT_MANAGER', self.employee, 'review-kpi-own'))
        response = self.client.post(reverse('portal:kpi_score_update', args=[result.pk]), {'actual': '80'})
        self.assertEqual(response.status_code, 302)
        result.refresh_from_db()
        self.assertEqual(result.actual, Decimal('80'))

    def test_kpi_assignment_cannot_bypass_department_scope(self):
        other = Department.objects.create(department_code='REVIEW-KPI-OTHER', department_name='Other', organization=self.organization)
        target = self.make_employee('REVIEW-KPI-FOREIGN')
        target.department = other
        target.save(update_fields=['department'])
        self.department.manager = self.employee
        self.department.save(update_fields=['manager'])
        user = self.make_user('DEPT_MANAGER', self.employee, 'review-kpi-assign')
        self.client.force_login(user)
        self.client.post(reverse('portal:kpi_assign_create'), {
            'employee': target.pk,
            'kpi_template': KPITemplate.objects.create(kpi_name='Foreign KPI', weight=100).pk,
            'kpi_period': KPIPeriod.objects.create(year=2026, month=10).pk,
            'target': '100',
        })
        self.assertFalse(EmployeeKPI.objects.filter(employee=target).exists())

    def test_notification_reading_requires_explicit_post_and_owner(self):
        other = self.make_employee('REVIEW-NOTICE-OTHER')
        owned = Notification.objects.create(employee=self.employee, notification_type='test', title='Owned', message='Test')
        foreign = Notification.objects.create(employee=other, notification_type='test', title='Foreign', message='Test')
        self.client.force_login(self.make_user('EMPLOYEE', self.employee, 'review-notifications'))
        self.client.get(reverse('portal:notification_list'))
        owned.refresh_from_db()
        self.assertFalse(owned.is_read)
        self.assertEqual(self.client.get(reverse('portal:notification_mark_read', args=[owned.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse('portal:notification_mark_read', args=[foreign.pk])).status_code, 404)
        self.client.post(reverse('portal:notification_mark_read', args=[owned.pk]))
        owned.refresh_from_db()
        self.assertTrue(owned.is_read)
        self.client.post(reverse('portal:notification_mark_all_read'))
        foreign.refresh_from_db()
        self.assertFalse(foreign.is_read)

    def test_employee_pagination_preserves_search_and_scope(self):
        self.department.manager = self.employee
        self.department.save(update_fields=['manager'])
        for index in range(22):
            self.make_employee(f'REVIEW-PAGE-{index:02}')
        self.client.force_login(self.make_user('DEPT_MANAGER', self.employee, 'review-pagination'))
        response = self.client.get(reverse('portal:hr_employee_list'), {'q': 'REVIEW-PAGE', 'page': '1'})
        self.assertEqual(len(response.context['employees']), 20)
        self.assertEqual(response.context['page_obj'].paginator.count, 22)
        self.assertContains(response, 'q=REVIEW-PAGE&amp;page=2')
        second = self.client.get(reverse('portal:hr_employee_list'), {'q': 'REVIEW-PAGE', 'page': '2'})
        self.assertEqual(len(second.context['employees']), 2)

    def test_timesheet_report_values_and_queries_are_independent_of_employee_count(self):
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-reports'))
        TimesheetEntry.objects.create(employee=self.employee, work_date=date(2026, 10, 1), hours=Decimal('8'))
        LeaveBalance.objects.create(employee=self.employee, year=2026, allocated_days=Decimal('12'))
        annual = LeaveType.objects.create(leave_type_code='AL', leave_type_name='Annual')
        LeaveRequest.objects.create(employee=self.employee, leave_type=annual, from_date=date(2026, 10, 1),
                                    to_date=date(2026, 10, 2), status='Approved')
        Holiday.objects.create(holiday_code='REVIEW-HOLIDAY', holiday_name='Test holiday', holiday_date=date(2026, 10, 2))
        MonthlyAttendanceSummary.objects.create(employee=self.employee, year=2026, month=10, annual_leave_days=Decimal('2'))
        url = reverse('portal:report_timesheet')
        with CaptureQueriesContext(connection) as small_queries:
            small = self.client.get(url, {'year': '2026', 'month': '10'})
        row = small.context['rows'][0]
        self.assertEqual(row['total_hours'], Decimal('8'))
        self.assertEqual(row['leave_remaining'], Decimal('11'))
        self.assertTrue(row['has_pending_summary'])
        for index in range(12):
            self.make_employee(f'REVIEW-REPORT-{index}')
        with CaptureQueriesContext(connection) as larger_queries:
            larger = self.client.get(url, {'year': '2026', 'month': '10'})
        self.assertEqual(len(larger.context['rows']), 13)
        self.assertLessEqual(len(larger_queries), len(small_queries) + 1)

    def test_budget_report_preserves_decimal_totals_and_excludes_deleted_and_pending(self):
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-budget'))
        for suffix, status, deleted in (('active', 'Approved', False), ('pending', 'Pending', False), ('deleted', 'Purchased', True)):
            procurement = ProcurementRequest.objects.create(request_no=f'REVIEW-{suffix}', requested_by=self.employee,
                department=self.department, request_date=date(2026, 10, 1), status=status)
            ProcurementItem.objects.create(procurement_request=procurement, item_name='Item', quantity=3, estimated_cost=Decimal('12.35'))
            if deleted:
                procurement.delete()
        AnnualBudget.objects.create(year=2026, department=self.department, category='Procurement', allocated_amount=Decimal('100'))
        AnnualBudget.objects.create(year=2026, department=None, category='Procurement', allocated_amount=Decimal('100'))
        response = self.client.get(reverse('portal:report_budget'), {'year': '2026'})
        self.assertEqual([row['actual'] for row in response.context['rows']], [Decimal('37.05'), Decimal('37.05')])
        self.assertTrue(all(row['remaining'] == Decimal('62.95') for row in response.context['rows']))

    def test_headcount_cache_preserves_soft_delete_and_avoids_row_queries(self):
        deleted = self.make_employee('REVIEW-HEADCOUNT-DELETED')
        deleted.delete()
        HeadcountPlan.objects.create(year=2026, department=self.department, planned_headcount=5)
        with self.assertNumQueries(1):
            plan = list(with_headcounts(HeadcountPlan.objects.all()))[0]
            self.assertEqual(plan.actual_headcount, 1)
            self.assertEqual(plan.gap, 4)
            self.assertEqual(plan.gap, 4)

    def test_training_and_event_reject_reversed_dates(self):
        course = TrainingCourse(course_code='REVIEW-REVERSED', course_name='Invalid', start_date=date(2026, 10, 2), end_date=date(2026, 10, 1))
        with self.assertRaises(ValidationError):
            course.full_clean()
        event = Event(title='Invalid', start_time=timezone.now(), end_time=timezone.now() - timezone.timedelta(hours=1))
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_report_invalid_dates_fall_back_to_valid_iso_inputs(self):
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-invalid-dates'))
        response = self.client.get(reverse('portal:report_personnel_changes'), {'from_date': '2026-99-01', 'to_date': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(date.fromisoformat(response.context['from_date']), date)

    def test_event_manager_cannot_post_another_department(self):
        other = Department.objects.create(department_code='REVIEW-EVENT-OTHER', department_name='Other', organization=self.organization)
        self.department.manager = self.employee
        self.department.save(update_fields=['manager'])
        self.client.force_login(self.make_user('DEPT_MANAGER', self.employee, 'review-event'))
        self.client.post(reverse('portal:event_list'), {'title': 'Forbidden event', 'department': other.pk,
            'start_time': '2026-10-01T08:00', 'end_time': '2026-10-01T09:00'})
        self.assertFalse(Event.objects.filter(title='Forbidden event').exists())

    def test_bulk_notices_deduplicate_recipients_without_query_per_employee(self):
        recipients = [self.make_employee(f'REVIEW-BULK-{index}') for index in range(12)]
        with CaptureQueriesContext(connection) as queries:
            notify_many(recipients + recipients, 'test', 'Bulk title', 'Bulk message')
        self.assertLessEqual(len(queries), 3)
        self.assertEqual(Notification.objects.filter(notification_type='test').count(), 12)

    def test_supply_bad_quantity_does_not_crash_or_create_request(self):
        self.client.force_login(self.make_user('EMPLOYEE', self.employee, 'review-supply'))
        for quantity in ('abc', '1.5', '-1', '0', '99999999999999999999999999999999999'):
            with self.subTest(quantity=quantity):
                response = self.client.post(reverse('portal:supply_request_create'), {'item': ['1'], 'quantity': [quantity]})
                self.assertEqual(response.status_code, 302)
                self.assertEqual(SupplyRequest.objects.count(), 0)

    def test_pending_attendance_does_not_reduce_required_hours(self):
        self.client.force_login(self.make_user('EMPLOYEE', self.employee, 'review-attendance'))
        summary = MonthlyAttendanceSummary.objects.create(employee=self.employee, year=2026, month=10,
                                                          annual_leave_days=Decimal('2'))
        url = reverse('portal:timesheet_month')
        pending = self.client.get(url, {'year': '2026', 'month': '10'})
        pending_required = pending.context['required_hours']
        summary.status = MonthlyAttendanceSummary.STATUS_APPROVED
        summary.save(update_fields=['status'])
        approved = self.client.get(url, {'year': '2026', 'month': '10'})
        self.assertEqual(pending_required - approved.context['required_hours'], Decimal('16'))

    def test_dispatch_failure_rolls_back_number_and_document(self):
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-dispatch'))
        book = DispatchBook.objects.create(book_code='Outgoing-2026', book_name='Test book', book_type='Outgoing', year=2026)
        data = {'dispatch_type': 'Outgoing', 'dispatch_no': 'REVIEW-001', 'title': 'Test dispatch',
                'issuing_organization': 'Test organization', 'issue_date': '2026-10-01', 'received_or_sent_date': '2026-10-01'}
        with patch('apps.portal.views.documents.DispatchTracking.objects.create', side_effect=RuntimeError('Test tracking failure')):
            self.client.post(reverse('portal:dispatch_create'), data)
        book.refresh_from_db()
        self.assertEqual(book.current_number, 0)
        self.assertFalse(OfficialDispatch.objects.filter(dispatch_no='REVIEW-001').exists())
        response = self.client.post(reverse('portal:dispatch_create'), data)
        self.assertEqual(response.status_code, 302)
        book.refresh_from_db()
        self.assertEqual(book.current_number, 1)
        self.assertEqual(DispatchTracking.objects.count(), 1)

    def test_bad_dispatch_type_and_date_do_not_create_books(self):
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-dispatch-invalid'))
        for dispatch_type, issue_date in (('wrong', '2026-10-01'), ('Outgoing', '2026-99-01')):
            self.client.post(reverse('portal:dispatch_create'), {'dispatch_type': dispatch_type, 'issue_date': issue_date})
        self.assertEqual(DispatchBook.objects.count(), 0)

    def test_internal_directive_uses_internal_book_type(self):
        self.client.force_login(self.make_user('HR_MANAGER', self.employee, 'review-internal'))
        response = self.client.post(reverse('portal:dispatch_create'), {
            'dispatch_type': 'InternalDirective', 'dispatch_no': 'REVIEW-INTERNAL', 'title': 'Test internal',
            'issuing_organization': 'Test', 'issue_date': '2026-10-01', 'received_or_sent_date': '2026-10-01',
        })
        self.assertEqual(response.status_code, 302)
        book = DispatchBook.objects.get()
        self.assertEqual(book.book_type, 'Internal')
        book.full_clean()


@skipUnless(connection.vendor == 'microsoft', 'Requires SQL Server row locking.')
class ConcurrentDispatchTests(TransactionTestCase):
    make_employee = portal_tests.PortalSensitiveWorkflowTests.make_employee
    make_user = portal_tests.PortalSensitiveWorkflowTests.make_user

    def setUp(self):
        portal_tests.PortalSensitiveWorkflowTests.setUpTestData.__func__(type(self))
        self.employee = self.make_employee('REVIEW-CONCURRENT')
        self.user = self.make_user('HR_MANAGER', self.employee, 'review-concurrent')
        self.book = DispatchBook.objects.create(book_code='Outgoing-2026', book_name='Concurrent book', book_type='Outgoing', year=2026)

    def test_two_simultaneous_entries_preserve_both_numbers_and_trackings(self):
        from apps.portal.views.documents import dispatch_create
        barrier = Barrier(2)
        def submit(index):
            close_old_connections()
            try:
                request = RequestFactory().post(reverse('portal:dispatch_create'), {
                    'dispatch_type': 'Outgoing', 'dispatch_no': f'REVIEW-CONCURRENT-{index}',
                    'title': 'Concurrent test', 'issuing_organization': 'Test',
                    'issue_date': '2026-10-01', 'received_or_sent_date': '2026-10-01',
                })
                request.user = User.objects.get(pk=self.user.pk)
                request.session = {}
                request._messages = FallbackStorage(request)
                barrier.wait(timeout=10)
                return dispatch_create(request).status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(submit, (1, 2))), [302, 302])
        self.book.refresh_from_db()
        self.assertEqual(self.book.current_number, 2)
        self.assertEqual(OfficialDispatch.objects.count(), 2)
        self.assertEqual(DispatchTracking.objects.count(), 2)
