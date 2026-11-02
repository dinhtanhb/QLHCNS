"""Maker/checker boundary through all four live approval routes."""
from datetime import date,timedelta
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from apps.portal import tests_review_20261008 as fixtures
from apps.office.models import MeetingRoom,RoomBooking,Vehicle,VehicleBooking,SupplyRequest
from apps.procurement.models import ProcurementRequest


@override_settings(AXES_ENABLED=False)
class IndependentApprovalTests(fixtures.Review20261008Fixtures):
    sequence=0
    def request_for(self,kind,creator):
        self.sequence+=1;code='FIXC-'+str(self.sequence)
        shared={'created_by':creator}
        if kind=='procurement':
            return ProcurementRequest.objects.create(request_no=code,requested_by=creator.employee,department=self.department,request_date=date(2026,11,2),**shared)
        if kind=='supply':
            return SupplyRequest.objects.create(request_no=code,employee=creator.employee,request_date=date(2026,11,2),**shared)
        start=timezone.now()+timedelta(days=self.sequence)
        if kind=='room':
            room=MeetingRoom.objects.create(room_code=code,room_name='Synthetic')
            return RoomBooking.objects.create(room=room,employee=creator.employee,purpose='Synthetic',start_time=start,end_time=start+timedelta(hours=1),**shared)
        vehicle=Vehicle.objects.create(vehicle_code=code,vehicle_name='Synthetic',plate_number=code)
        return VehicleBooking.objects.create(vehicle=vehicle,employee=creator.employee,destination='Synthetic',start_time=start,end_time=start+timedelta(hours=1),**shared)

    def test_creator_cannot_decide_and_other_same_role_can_for_every_approval_role(self):
        for kind,roles in [('procurement',['FINANCE_OFFICER','DIRECTOR']),('room',['HR_MANAGER','HR_OFFICER','SYS_ADMIN']),('vehicle',['HR_MANAGER','HR_OFFICER','SYS_ADMIN']),('supply',['HR_MANAGER','HR_OFFICER','SYS_ADMIN'])]:
            for role in roles:
                with self.subTest(kind=kind,role=role):
                    creator=self.make_user(role,self.make_employee('MC-'+str(self.sequence)+'A'),'maker-'+str(self.sequence))
                    other=self.make_user(role,self.make_employee('MC-'+str(self.sequence)+'B'),'checker-'+str(self.sequence))
                    row=self.request_for(kind,creator)
                    route={'procurement':'procurement_request_approve','room':'room_booking_approve','vehicle':'vehicle_booking_approve','supply':'supply_request_approve'}[kind]
                    self.client.force_login(creator)
                    for decision in ['Approved','Rejected']:
                        self.client.post(reverse('portal:'+route,args=[row.pk]),{'decision':decision})
                        row.refresh_from_db();self.assertEqual(row.status,'Pending')
                    self.client.force_login(other)
                    self.client.post(reverse('portal:'+route,args=[row.pk]),{'decision':'Approved'})
                    row.refresh_from_db();self.assertEqual(row.status,'Approved')

    def test_superuser_is_not_exempt_and_request_creator_is_also_a_maker(self):
        from apps.security.models import User
        from apps.security.approval_rules import require_independent_approver
        from django.core.exceptions import ValidationError
        person=self.make_employee('MC-SUPER')
        actor=User.objects.create_superuser(username='maker-super-c',password='test-password',employee=person)
        row=self.request_for('procurement',actor)
        self.client.force_login(actor)
        self.client.post(reverse('portal:procurement_request_approve',args=[row.pk]),{'decision':'Approved'})
        row.refresh_from_db();self.assertEqual(row.status,'Pending')
        other=self.make_employee('MC-DELEGATED');row.requested_by=other
        with self.assertRaises(ValidationError):require_independent_approver(row,actor)

    def test_other_rejector_can_decide_once_and_own_approval_controls_are_hidden(self):
        maker=self.make_user('HR_MANAGER',self.make_employee('MC-UI'),'mc-ui-c')
        other=self.make_user('HR_MANAGER',self.make_employee('MC-REJECT'),'mc-reject-c')
        row=self.request_for('room',maker)
        self.client.force_login(maker)
        response=self.client.get(reverse('portal:room_booking_approval_list'))
        self.assertContains(response,'Đề nghị của bạn cần người duyệt khác cùng quyền.')
        self.assertNotContains(response,f'action="{reverse("portal:room_booking_approve",args=[row.pk])}"')
        self.client.force_login(other)
        response=self.client.get(reverse('portal:room_booking_approval_list'))
        self.assertContains(response,f'action="{reverse("portal:room_booking_approve",args=[row.pk])}"')
        self.client.post(reverse('portal:room_booking_approve',args=[row.pk]),{'decision':'Rejected'})
        row.refresh_from_db();self.assertEqual(row.status,'Rejected')
        self.client.post(reverse('portal:room_booking_approve',args=[row.pk]),{'decision':'Approved'})
        row.refresh_from_db();self.assertEqual(row.status,'Rejected')

    def test_admin_cannot_create_already_decided_requests_on_behalf_of_another_employee(self):
        from django.contrib import admin
        from django.core.exceptions import ValidationError
        from django.test import RequestFactory
        actor=self.make_user('HR_MANAGER',self.make_employee('MC-ADMIN'),'mc-admin-c')
        other=self.make_user('HR_MANAGER',self.make_employee('MC-ADMIN-OTHER'),'mc-admin-other-c')
        request=RequestFactory().post('/admin/');request.user=actor
        for kind in ['room','vehicle','supply','procurement']:
            with self.subTest(kind=kind):
                row=self.request_for(kind,other);row.pk=None;row.created_by=None;row.status='Approved'
                if hasattr(row,'request_no'):row.request_no+='-NEW'
                with self.assertRaises(ValidationError):
                    admin.site._registry[type(row)].save_model(request,row,None,False)
                previous=self.request_for(kind,actor)
                previous.created_by=other;previous.save(update_fields=['created_by'])
                if kind=='procurement':previous.requested_by=other.employee
                else:previous.employee=other.employee
                previous.status='Approved'
                with self.assertRaises(ValidationError):
                    admin.site._registry[type(previous)].save_model(request,previous,None,True)
