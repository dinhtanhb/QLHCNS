"""UI authorization fixes without changing booking or report view guards."""
from datetime import timedelta
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.portal.test_home_dashboard import HomeDashboardTests
from apps.office.models import MeetingRoom, RoomBooking, Vehicle, VehicleBooking


class AdministrationFollowupTests(TestCase):
    user = HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        HomeDashboardTests.setUpTestData.__func__(cls)

    def test_cancel_only_for_owner_and_cancellable_status(self):
        owner = self.user('EMPLOYEE', True)
        other = self.user('HR_OFFICER', True)
        for kind in ('room', 'vehicle'):
            for status in ('Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed'):
                booking = SimpleNamespace(pk=999, employee=owner.employee,
                    employee_id=owner.employee_id, status=status, start_time=timezone.now(),
                    end_time=timezone.now(), room='Phòng giả', vehicle='Xe giả')
                for user in (owner, other):
                    request = RequestFactory().get('/'); request.user = user
                    html = render_to_string(f'portal/{kind}_booking_list.html',
                        {'request': request, 'user': user, 'upcoming': [booking]})
                    with self.subTest(kind=kind, status=status, owner=user==owner):
                        self.assertEqual(reverse(f'portal:{kind}_booking_cancel', args=[999]) in html,
                            user==owner and status in ('Pending', 'Approved'))

    def test_report_links_match_existing_report_permission(self):
        for role, allowed in [('EMPLOYEE', False), ('DEPT_MANAGER', False),
                              ('HR_MANAGER', True), ('DIRECTOR', True)]:
            self.client.force_login(self.user(role, True))
            response = self.client.get(reverse('portal:dispatch_list'))
            with self.subTest(role=role):
                self.assertEqual('Xuất Sổ CV' in response.content.decode(), allowed)

    def test_unlinked_account_has_no_profile_request_link(self):
        user = self.user('SYS_ADMIN', True)
        user.employee = None; user.save(update_fields=['employee'])
        self.client.force_login(user)
        html = self.client.get(reverse('portal:dispatch_list')).content.decode()
        self.assertNotIn('href="'+reverse('portal:profile_change_request_list')+'"', html)

    def test_owner_cancellation_post_preserves_existing_notice_and_status(self):
        user = self.user('EMPLOYEE', True); self.client.force_login(user)
        for kind, model, resource in [
            ('room', RoomBooking, MeetingRoom.objects.create(room_code='FOLLOW', room_name='Phòng giả')),
            ('vehicle', VehicleBooking, Vehicle.objects.create(vehicle_code='FOLLOW', vehicle_name='Xe giả', plate_number='TEST')),
        ]:
            fields = {kind: resource, 'employee': user.employee, 'purpose':'Kiểm thử',
                'start_time':timezone.now()+timedelta(days=30), 'end_time':timezone.now()+timedelta(days=30,hours=1)}
            if kind=='vehicle': fields['destination']='Văn phòng giả'
            booking = model.objects.create(**fields)
            response=self.client.post(reverse(f'portal:{kind}_booking_cancel', args=[booking.pk]), follow=True)
            booking.refresh_from_db()
            self.assertEqual(booking.status, 'Cancelled')
            self.assertContains(response, 'Đã hủy đặt '+('phòng' if kind=='room' else 'xe'))
