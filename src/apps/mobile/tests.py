from datetime import date, timedelta
from importlib import import_module
import json
import time
from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.hrm.models import Employee
from apps.leave.models import LeaveApproval, LeaveBalance, LeaveRequest, LeaveType
from apps.notification.models import Notification
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User

BASE = '/api/mobile/v1/'


@override_settings(MOBILE_API_ENABLED=True, AXES_ENABLED=False)
class MobileAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code='MOBILE', organization_name='QA mobile')
        dep = Department.objects.create(organization=org, department_code='MOBILE', department_name='QA')
        position = Position.objects.create(position_code='MOBILE', position_name='QA')
        cls.people, cls.users = [], []
        for index, role in enumerate(('EMPLOYEE', 'DEPT_MANAGER', 'HR_MANAGER', 'EMPLOYEE')):
            person = Employee.objects.create(employee_code=f'MOB-{index}', first_name='QA', last_name=str(index),
                full_name=f'QA mobile {index}', date_of_birth=date(1990, 1, 1), gender='Other',
                national_id=f'MOBILE-QA-{index}', company_email=f'mobile-{index}@example.test', join_date=date(2020, 1, 1),
                department=dep, position=position, employment_status='Active')
            assigned, _ = Role.objects.get_or_create(role_code=role, defaults={'role_name': role})
            user = User.objects.create_user(username=f'mobile-{index}', password='qa-password', employee=person, role=assigned)
            cls.people.append(person)
            cls.users.append(user)
        cls.people[0].manager = cls.people[1]
        cls.people[0].save(update_fields=['manager'])
        cls.people[1].manager = cls.people[2]
        cls.people[1].save(update_fields=['manager'])
        cls.kind = LeaveType.objects.create(leave_type_code='MOB-QA', leave_type_name='Nghỉ QA')

    def post(self, path, data=None, client=None):
        return (client or self.client).post(BASE+path, json.dumps(data or {}), content_type='application/json')

    def login_as(self, index=0, client=None):
        client = client or self.client
        result = self.post('login/', {'username': self.users[index].username, 'password': 'qa-password'}, client)
        self.assertEqual(result.status_code, 200, result.content)
        token = result.json()['token']
        client.defaults['HTTP_AUTHORIZATION'] = 'Bearer '+token
        return token

    def leave(self, employee=0, **kwargs):
        return LeaveRequest.objects.create(employee=self.people[employee], leave_type=self.kind,
            from_date=date(2026, 11, 2), to_date=date(2026, 11, 2), reason='QA', **kwargs)

    def test_profile_request_is_owned_validated_and_requires_hr_review(self):
        from apps.hrm.models import EmployeeProfileChangeRequest
        self.login_as()
        payload = {'field_name': 'personal_email', 'new_value': 'qa-new@example.test', 'employee_id': self.people[3].pk, 'status': 'Approved'}
        self.assertEqual(self.post('profile-requests/', payload).status_code, 201)
        row = EmployeeProfileChangeRequest.objects.get()
        self.assertEqual(row.employee_id, self.people[0].pk)
        self.assertEqual(row.status, 'Pending')
        self.people[0].refresh_from_db()
        self.assertNotEqual(self.people[0].personal_email, row.new_value)
        self.assertEqual(self.post('profile-requests/', payload).status_code, 400)
        self.assertEqual(self.post('profile-requests/', {'field_name': 'personal_email', 'new_value': 'bad-email'}).status_code, 400)
        self.assertEqual(self.post('profile-requests/', {'field_name': 'department', 'new_value': 'x'}).status_code, 403)
        self.login_as(3)
        self.assertEqual(self.client.get(BASE+'profile-requests/').json()['count'], 0)

    def test_password_change_checks_old_confirmation_strength_and_revokes_sessions(self):
        self.login_as()
        second = Client(); self.login_as(client=second)
        payload = {'old_password': 'wrong', 'new_password': 'QA-strong!2026-session', 'confirm_password': 'QA-strong!2026-session'}
        self.assertEqual(self.post('change-password/', payload).status_code, 400)
        self.assertEqual(self.client.get(BASE+'me/').status_code, 200)
        payload['old_password'] = 'qa-password'; payload['confirm_password'] = 'mismatch'
        self.assertEqual(self.post('change-password/', payload).status_code, 400)
        payload.update(new_password='123', confirm_password='123')
        self.assertEqual(self.post('change-password/', payload).status_code, 400)
        payload.update(new_password='QA-strong!2026-session', confirm_password='QA-strong!2026-session')
        self.assertEqual(self.post('change-password/', payload).status_code, 200)
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)
        self.assertEqual(second.get(BASE+'me/').status_code, 401)
        self.users[0].refresh_from_db()
        self.assertTrue(self.users[0].check_password(payload['new_password']))

    def test_account_endpoints_reject_anonymous(self):
        self.assertEqual(self.post('change-password/').status_code, 401)
        self.assertEqual(self.post('profile-requests/').status_code, 401)

    def test_profile_detail_and_history_never_accept_another_employee(self):
        from apps.hrm.models import EmployeeReward
        from apps.payroll.models import EmployeeSalary
        for index in (0, 3):
            EmployeeSalary.objects.create(employee=self.people[index], current_basic_salary=10000000+index, effective_date=date(2026, 1, 1))
            EmployeeReward.objects.create(employee=self.people[index], reward_type=f'PRIVATE-{index}', reward_date=date(2026, 1, 1), amount=123)
        self.login_as()
        result = self.client.get(BASE+f'my-profile/?employee={self.people[3].pk}').json()
        self.assertEqual(result['profile']['employee_code'], self.people[0].employee_code)
        self.assertEqual(result['salary']['basic'], '10000000.00')
        self.assertNotIn('national_id', result['profile'])
        history = self.client.get(BASE+f'profile-history/?kind=rewards&employee={self.people[3].pk}').json()
        self.assertEqual(history['count'], 1)
        self.assertEqual(history['items'][0]['description'], 'PRIVATE-0')
        self.assertEqual(history['items'][0]['amount'], '123.00')
        self.assertEqual(self.client.get(BASE+'profile-history/?kind=invalid').status_code, 400)

    def test_directory_contains_only_active_public_fields(self):
        self.people[3].employment_status = 'Resigned'; self.people[3].save(update_fields=['employment_status'])
        self.login_as()
        result = self.client.get(BASE+'organization/').json()
        self.assertEqual(result['count'], 3)
        self.assertEqual(set(result['items'][0]), {'id', 'name', 'employee_code', 'department', 'position', 'manager_id', 'manager'})

    def test_profile_approvals_permissions_repeat_decisions_and_notifications(self):
        from apps.hrm.models import EmployeeProfileChangeRequest
        self.login_as()
        self.post('profile-requests/', {'field_name': 'address', 'new_value': 'QA Approved address'})
        row = EmployeeProfileChangeRequest.objects.get()
        self.assertEqual(self.client.get(BASE+'profile-approvals/').status_code, 403)
        self.assertEqual(self.post(f'profile-requests/{row.pk}/decision/', {'decision': 'approve'}).status_code, 403)
        self.login_as(2)
        self.assertTrue(self.client.get(BASE+'me/').json()['can_approve_profile_change'])
        self.assertEqual(self.client.get(BASE+'profile-approvals/').json()['count'], 1)
        self.assertEqual(self.post(f'profile-requests/{row.pk}/decision/', {'decision': 'approve', 'note': 'QA'}).status_code, 200)
        self.assertEqual(self.post(f'profile-requests/{row.pk}/decision/', {'decision': 'reject'}).status_code, 404)
        self.people[0].refresh_from_db(); self.assertEqual(self.people[0].address, 'QA Approved address')
        self.assertEqual(Notification.objects.filter(employee=self.people[0], notification_type='profile-change').count(), 1)
        self.login_as()
        self.assertEqual(self.client.get(BASE+'notifications/').json()['items'][0]['destination'], 'profile-requests')

    def test_profile_stale_snapshot_and_nonapproval_preserve_employee(self):
        from apps.hrm.models import EmployeeProfileChangeRequest
        self.login_as(2)
        for decision, expected in [('reject', 'Rejected'), ('more_info', 'NeedsMoreInfo')]:
            row = EmployeeProfileChangeRequest.objects.create(employee=self.people[0], field_name='address',
                old_value=self.people[0].address or '', submitted_snapshot=self.people[0].address or '', new_value='QA unused')
            self.assertEqual(self.post(f'profile-requests/{row.pk}/decision/', {'decision': decision}).status_code, 200)
            row.refresh_from_db(); self.assertEqual(row.status, expected)
        row = EmployeeProfileChangeRequest.objects.create(employee=self.people[0], field_name='address',
            old_value='OLD', submitted_snapshot='STALE', new_value='QA unused')
        self.assertEqual(self.post(f'profile-requests/{row.pk}/decision/', {'decision': 'approve'}).status_code, 400)
        self.people[0].refresh_from_db(); self.assertNotEqual(self.people[0].address, 'QA unused')
        row.refresh_from_db(); self.assertEqual(row.status, 'Pending')

    def test_login_session_is_separate_and_does_not_set_cookies(self):
        portal = Client()
        portal.force_login(self.users[3])
        web_key = portal.session.session_key
        result = self.post('login/', {'username': 'mobile-0', 'password': 'qa-password'}, portal)
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.cookies)
        self.assertNotEqual(result.json()['token'], web_key)
        self.assertEqual(portal.get('/portal/profile/').wsgi_request.user.pk, self.users[3].pk)

    def test_cookie_only_and_web_session_as_bearer_are_rejected(self):
        self.client.force_login(self.users[0])
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer '+self.client.session.session_key
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)

    def test_logout_revokes_copied_token(self):
        token = self.login_as()
        copied = Client(HTTP_AUTHORIZATION='Bearer '+token)
        self.assertEqual(self.post('logout/').status_code, 200)
        self.assertEqual(copied.get(BASE+'me/').status_code, 401)

    def test_password_change_and_deactivation_revoke_access(self):
        self.login_as()
        self.users[0].set_password('changed')
        self.users[0].save()
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)
        self.login_as(1)
        User.objects.filter(pk=self.users[1].pk).update(is_active=False)
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)

    def test_idle_and_absolute_expiry_are_enforced(self):
        token = self.login_as()
        store = import_module(settings.SESSION_ENGINE).SessionStore(token)
        store['security_last_activity'] = int(time.time())-settings.SESSION_IDLE_TIMEOUT-1
        store.save()
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)
        token = self.login_as()
        store = import_module(settings.SESSION_ENGINE).SessionStore(token)
        store.set_expiry(timezone.now()-timedelta(seconds=1))
        store.save()
        self.assertEqual(self.client.get(BASE+'me/').status_code, 401)

    def test_read_does_not_extend_absolute_session_lifetime(self):
        from django.contrib.sessions.models import Session
        token = self.login_as()
        before = Session.objects.get(session_key=token).expire_date
        self.assertEqual(self.client.get(BASE+'me/').status_code, 200)
        self.assertEqual(Session.objects.get(session_key=token).expire_date, before)

    def test_profile_and_attendance_are_owner_only(self):
        Attendance.objects.create(employee=self.people[0], attendance_date=date(2026, 10, 28), working_hours=8)
        Attendance.objects.create(employee=self.people[3], attendance_date=date(2026, 10, 28), working_hours=4)
        self.login_as()
        profile = self.client.get(BASE+'me/?employee=4').json()
        self.assertEqual(profile['profile']['employee_code'], 'MOB-0')
        self.assertNotIn('national_id', profile['profile'])
        self.assertNotIn('salary', profile['profile'])
        rows = self.client.get(BASE+'attendance/?employee=4').json()['items']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['hours'], '8.00')

    def test_leave_scope_is_tree_even_for_hr(self):
        own, other = self.leave(), self.leave(3)
        self.login_as(2)
        ids = [r['id'] for r in self.client.get(BASE+'leaves/').json()['items']]
        self.assertIn(own.pk, ids)
        self.assertNotIn(other.pk, ids)

    def test_submit_derives_employee_status_days_and_prevents_repeat(self):
        self.login_as()
        data = {'leave_type': self.kind.pk, 'from_date': '2026-11-03', 'to_date': '2026-11-03',
                'reason': 'QA mobile', 'employee': self.people[3].pk, 'status': 'Approved', 'total_days': 99}
        result = self.post('leaves/', data)
        self.assertEqual(result.status_code, 201, result.content)
        leave = LeaveRequest.objects.get(pk=result.json()['item']['id'])
        self.assertEqual(leave.employee, self.people[0])
        self.assertEqual(leave.status, 'Pending')
        self.assertEqual(leave.total_days, 1)
        self.assertEqual(leave.created_by, self.users[0])
        self.assertEqual(Notification.objects.filter(employee=self.people[1]).count(), 1)
        self.assertEqual(self.post('leaves/', data).status_code, 400)
        self.assertEqual(LeaveRequest.objects.count(), 1)

    def test_quota_and_dates_are_shared_with_web(self):
        kind = LeaveType.objects.create(leave_type_code='AL', leave_type_name='Phép năm')
        self.login_as()
        data = {'leave_type': kind.pk, 'from_date': '2026-11-03', 'to_date': '2026-11-03'}
        self.assertEqual(self.post('leaves/', data).status_code, 400)
        LeaveBalance.objects.create(employee=self.people[0], year=2026, allocated_days=1)
        self.assertEqual(self.post('leaves/', data).status_code, 201)
        data.update(from_date='2026-11-04', to_date='2026-11-04')
        self.assertEqual(self.post('leaves/', data).status_code, 400)
        data.update(from_date='invalid')
        self.assertEqual(self.post('leaves/', data).status_code, 400)

    def test_approval_permission_scope_self_guard_and_repeat(self):
        own, other, self_leave = self.leave(), self.leave(3), self.leave(1)
        self.login_as()
        self.assertEqual(self.client.get(BASE+'approvals/').status_code, 403)
        self.assertEqual(self.post(f'leaves/{own.pk}/decision/', {'decision': 'Approved'}).status_code, 403)
        self.login_as(1)
        self.assertEqual(self.post(f'leaves/{self_leave.pk}/decision/', {'decision': 'Approved'}).status_code, 403)
        self.assertEqual(self.post(f'leaves/{other.pk}/decision/', {'decision': 'Approved'}).status_code, 404)
        self.assertEqual(self.post(f'leaves/{own.pk}/decision/', {'decision': 'wrong'}).status_code, 400)
        self.assertEqual(self.post(f'leaves/{own.pk}/decision/', {'decision': 'Approved'}).status_code, 200)
        self.assertEqual(self.post(f'leaves/{own.pk}/decision/', {'decision': 'Rejected'}).status_code, 404)
        own.refresh_from_db()
        self.assertEqual(own.status, 'Approved')
        self.assertEqual(LeaveApproval.objects.filter(leave_request=own).count(), 1)
        self.assertTrue(Notification.objects.filter(employee=self.people[0]).exists())

    def test_notification_read_is_owner_only(self):
        own = Notification.objects.create(employee=self.people[0], notification_type='leave', title='QA', message='QA')
        other = Notification.objects.create(employee=self.people[3], notification_type='leave', title='Private', message='Private')
        self.login_as()
        self.assertEqual(self.client.get(BASE+'notifications/').json()['count'], 1)
        self.assertEqual(self.post(f'notifications/{other.pk}/read/').status_code, 404)
        self.assertEqual(self.post(f'notifications/{own.pk}/read/').status_code, 200)
        own.refresh_from_db()
        self.assertTrue(own.is_read)

    def test_unlinked_and_deleted_employee_cannot_write(self):
        self.users[0].employee = None
        self.users[0].save()
        self.login_as()
        self.assertIsNone(self.client.get(BASE+'me/').json()['profile'])
        self.assertEqual(self.post('leaves/', {'leave_type': self.kind.pk,
            'from_date': '2026-11-03', 'to_date': '2026-11-03'}).status_code, 403)
        Employee.objects.filter(pk=self.people[1].pk).delete()
        self.login_as(1)
        self.assertIsNone(self.client.get(BASE+'me/').json()['profile'])

    def test_json_methods_limits_pagination_and_no_cache(self):
        self.login_as()
        self.assertEqual(self.client.post(BASE+'leaves/', {'leave_type': 1}).status_code, 415)
        self.assertEqual(self.client.post(BASE+'leaves/', '[]', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(BASE+'leaves/', '{', content_type='application/json').status_code, 400)
        self.assertEqual(self.post('leaves/', {'reason': 'x'*17000}).status_code, 413)
        self.assertEqual(self.client.get(BASE+'logout/').status_code, 405)
        self.assertEqual(self.client.get(BASE+'leaves/?page=invalid').status_code, 400)
        result = self.client.get(BASE+'me/')
        self.assertIn('no-store', result['Cache-Control'])
        self.assertFalse(result.cookies)

    def test_api_can_be_disabled(self):
        with override_settings(MOBILE_API_ENABLED=False):
            self.assertEqual(self.client.get(BASE+'me/').status_code, 404)

    @override_settings(MOBILE_PUSH_ENABLED=True)
    def test_push_registration_moves_address_to_current_account(self):
        self.login_as()
        token = 'ExpoPushToken[qaDevice123456]'
        self.assertEqual(self.post('push-token/', {'token': token}).status_code, 200)
        second = Client()
        self.login_as(3, second)
        self.assertEqual(self.post('push-token/', {'token': token}, second).status_code, 200)
        from apps.mobile.push import send_generic_push
        with patch('apps.mobile.push.urlopen') as network:
            send_generic_push([self.people[0].pk])
            network.assert_not_called()
            network.return_value.__enter__.return_value.read.return_value = b'{"data":[{"status":"ok"}]}'
            send_generic_push([self.people[3].pk])
            network.assert_called_once()
            payload = json.loads(network.call_args.args[0].data)
            self.assertEqual(payload[0]['body'], 'Bạn có cập nhật mới. Mở IHRMS để xem chi tiết.')
            self.assertEqual(payload[0]['data'], {'screen': 'notifications'})
            self.assertEqual(payload[0]['priority'], 'high')
            self.assertNotIn(self.people[3].full_name, json.dumps(payload, ensure_ascii=False))
        self.assertEqual(self.post('push-token/', {'token': 'not-a-token'}).status_code, 400)
        self.assertEqual(self.post('logout/', client=second).status_code, 200)
        with patch('apps.mobile.push.urlopen') as network:
            send_generic_push([self.people[3].pk])
            network.assert_not_called()

    def test_push_disabled_by_default_and_no_external_delivery(self):
        self.login_as()
        self.assertEqual(self.post('push-token/', {'token': 'ExpoPushToken[qaDevice123456]'}).status_code, 503)
        from apps.mobile.push import send_generic_push
        with patch('apps.mobile.push.urlopen') as network:
            send_generic_push([self.people[0].pk])
            network.assert_not_called()

    @override_settings(MOBILE_PUSH_ENABLED=True)
    def test_cached_inflight_session_cannot_resurrect_moved_push_or_logout(self):
        from apps.mobile.middleware import save_native_session
        from apps.mobile.push import send_generic_push
        from django.contrib.sessions.backends.db import SessionStore
        old_token = self.login_as()
        address = 'ExpoPushToken[qaInFlightDevice]'
        self.assertEqual(self.post('push-token/', {'token': address}).status_code, 200)
        stale = SessionStore(old_token)
        self.assertEqual(stale['expo_push_token'], address)  # Cache before transfer.
        second = Client()
        self.login_as(3, second)
        self.assertEqual(self.post('push-token/', {'token': address}, second).status_code, 200)
        stale['security_last_activity'] = int(time.time())
        self.assertTrue(save_native_session(stale))
        with patch('apps.mobile.push.urlopen') as network:
            send_generic_push([self.people[0].pk])
            network.assert_not_called()
        SessionStore(old_token).flush()
        self.assertFalse(save_native_session(stale))

    @override_settings(MOBILE_PUSH_ENABLED=True)
    def test_push_not_sent_before_commit_or_after_rollback(self):
        from apps.notification.services import notify
        from django.db import transaction
        with patch('apps.mobile.push.send_generic_push') as send:
            with self.captureOnCommitCallbacks(execute=True):
                notify(self.people[0], 'leave', 'Private title', 'Private details')
                send.assert_not_called()
            send.assert_called_once_with((self.people[0].pk,))
            send.reset_mock()
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic():
                        notify(self.people[0], 'leave', 'Rolled back', 'Private')
                        raise ValueError
                except ValueError:
                    pass
            send.assert_not_called()

    @override_settings(AXES_ENABLED=True)
    def test_login_uses_persistent_axes_lockout(self):
        for _ in range(settings.AXES_FAILURE_LIMIT):
            result = self.post('login/', {'username': 'mobile-0', 'password': 'wrong'})
        self.assertIn(result.status_code, (403, 429))
        locked = self.post('login/', {'username': 'mobile-0', 'password': 'qa-password'})
        self.assertIn(locked.status_code, (403, 429))
        self.assertNotIn('token', locked.json() if locked.headers.get('Content-Type', '').startswith('application/json') else {})
