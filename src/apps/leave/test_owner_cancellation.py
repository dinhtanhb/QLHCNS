"""Retired employees cannot submit; owners may cancel reserved pending leave."""
from datetime import date
from django.core.exceptions import PermissionDenied,ValidationError
from django.test import override_settings
from apps.portal import tests_review_20261008 as fixtures
from apps.leave.models import LeaveRequest,LeaveType,LeaveBalance
from apps.leave.services import submit_leave
from django.test import Client,TransactionTestCase
from django.db import connection,close_old_connections
from django.urls import reverse
from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier


@override_settings(AXES_ENABLED=False)
class OwnerLeaveTests(fixtures.Review20261008Fixtures):
    def setUp(self):
        self.employee=self.make_employee('LEAVE-C')
        self.user=self.make_user('EMPLOYEE',self.employee,'leave-c-owner')
        self.other=self.make_user('EMPLOYEE',self.make_employee('LEAVE-C-OTHER'),'leave-c-other')
        self.kind=LeaveType.objects.create(leave_type_code='AL',leave_type_name='Synthetic annual')
        self.balance=LeaveBalance.objects.create(employee=self.employee,year=2026,allocated_days=10)

    def submit(self):
        return submit_leave(self.user,leave_type=self.kind.pk,from_date=date(2026,11,3),to_date=date(2026,11,3))

    def test_resigned_employee_with_active_account_cannot_submit(self):
        self.employee.employment_status='Resigned';self.employee.save(update_fields=['employment_status'])
        with self.assertRaises(ValidationError):self.submit()
        self.assertEqual(LeaveRequest.objects.count(),0)

    def test_pending_owner_cancellation_releases_only_reserved_days_and_records_event(self):
        from apps.leave.services import cancel_leave
        from apps.security.models import SecurityEvent
        leave=self.submit();self.assertEqual(self.balance.available_annual_days,9)
        cancel_leave(self.user,leave.pk);leave.refresh_from_db()
        self.assertEqual(leave.status,'Cancelled');self.assertEqual(self.balance.available_annual_days,10)
        self.assertTrue(SecurityEvent.objects.filter(user=self.user,action='leave_cancel',record_id=str(leave.pk)).exists())
        with self.assertRaises(ValidationError):cancel_leave(self.user,leave.pk)
        self.assertEqual(self.balance.available_annual_days,10)

    def test_other_owner_or_approved_leave_cannot_be_cancelled(self):
        from apps.leave.services import cancel_leave
        leave=self.submit()
        with self.assertRaises(PermissionDenied):cancel_leave(self.other,leave.pk)
        LeaveRequest.objects.filter(pk=leave.pk).update(status='Approved')
        with self.assertRaises(ValidationError):cancel_leave(self.user,leave.pk)
        leave.refresh_from_db();self.assertEqual(leave.status,'Approved')

    def test_web_cancel_requires_post_and_csrf_and_resigned_mobile_submit_keeps_error_shape(self):
        leave=self.submit();client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertContains(client.get(reverse('portal:leave_list')), 'id="ui-confirm-dialog"')
        self.assertEqual(client.get(reverse('portal:leave_cancel',args=[leave.pk])).status_code,405)
        self.assertEqual(client.post(reverse('portal:leave_cancel',args=[leave.pk])).status_code,403)
        self.employee.employment_status='Resigned';self.employee.save(update_fields=['employment_status'])
        from django.test import override_settings
        with override_settings(MOBILE_API_ENABLED=True):
            result=self.client.post('/api/mobile/v1/login/',{'username':self.user.username,'password':'test-password'},content_type='application/json')
            self.assertEqual(result.status_code,200)
            self.client.defaults['HTTP_AUTHORIZATION']='Bearer '+result.json()['token']
            denied=self.client.post('/api/mobile/v1/leaves/',{'leave_type':self.kind.pk,'from_date':'2026-11-04','to_date':'2026-11-04'},content_type='application/json')
            self.assertEqual(denied.status_code,400);self.assertIn('đã nghỉ việc',denied.json()['error'])


@skipUnless(connection.vendor=='microsoft','Requires SQL Server row locking.')
class ConcurrentOwnerCancellationTests(TransactionTestCase):
    def test_two_cancellations_produce_one_transition_and_one_audit_event(self):
        from apps.leave.services import cancel_leave
        from apps.security.models import User,SecurityEvent
        fixtures.Review20261008Fixtures.setUpTestData.__func__(type(self))
        employee=fixtures.Review20261008Fixtures.make_employee(self,'CANCEL-RACE')
        user=fixtures.Review20261008Fixtures.make_user(self,'EMPLOYEE',employee,'cancel-race-c')
        kind=LeaveType.objects.create(leave_type_code='AL',leave_type_name='Synthetic annual')
        balance=LeaveBalance.objects.create(employee=employee,year=2026,allocated_days=10)
        leave=submit_leave(user,leave_type=kind.pk,from_date=date(2026,11,3),to_date=date(2026,11,3))
        barrier=Barrier(2)
        def attempt():
            close_old_connections()
            try:
                actor=User.objects.get(pk=user.pk);barrier.wait(timeout=10)
                try:cancel_leave(actor,leave.pk);return 'cancelled'
                except ValidationError:return 'already-decided'
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:attempt(),range(2)))
        self.assertCountEqual(results,['cancelled','already-decided'])
        self.assertEqual(SecurityEvent.objects.filter(action='leave_cancel',record_id=str(leave.pk)).count(),1)
        self.assertEqual(balance.available_annual_days,10)
