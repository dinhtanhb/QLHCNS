from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.hrm.models import Employee
from apps.office.models import (
    IncomingDocument, MeetingRoom, OutgoingDocument, RoomBooking, Vehicle, VehicleBooking,
)
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User


class OfficeTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="OFF-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="OFF-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="OFF-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="OFF-EMP", first_name="An", last_name="Kiểm thử", full_name="OFF-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="OFF-EMP",
            company_email="off-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )
        cls.room = MeetingRoom.objects.create(room_code="OFF-ROOM", room_name="Phòng họp")
        cls.vehicle = Vehicle.objects.create(
            vehicle_code="OFF-CAR", vehicle_name="Xe kiểm thử", plate_number="51A-00001"
        )

    @classmethod
    def make_user(cls, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=cls.employee, role=role
        )

    @staticmethod
    def at(hour, minute=0):
        return timezone.make_aware(datetime(2026, 10, 5, hour, minute))


class OfficeModelValidationTests(OfficeTestBase):
    def test_vehicle_booking_accepts_pending_and_rejected_states(self):
        booking = VehicleBooking(
            vehicle=self.vehicle, employee=self.employee, destination="Biên Hòa",
            start_time=self.at(15), end_time=self.at(16), status="Pending",
        )
        booking.full_clean()
        booking.status = "Rejected"
        booking.full_clean()

    def test_room_booking_requires_end_after_start(self):
        booking = RoomBooking(
            room=self.room, employee=self.employee, purpose="Họp",
            start_time=self.at(10), end_time=self.at(10),
        )
        with self.assertRaises(ValidationError):
            booking.clean()

    def test_room_booking_rejects_overlapping_approved_booking(self):
        RoomBooking.objects.create(
            room=self.room, employee=self.employee, purpose="Cuộc họp đã duyệt",
            start_time=self.at(10), end_time=self.at(11), status="Approved",
        )
        overlapping = RoomBooking(
            room=self.room, employee=self.employee, purpose="Cuộc họp mới",
            start_time=self.at(10, 30), end_time=self.at(11, 30),
        )
        with self.assertRaises(ValidationError):
            overlapping.clean()

    def test_vehicle_booking_requires_end_after_start(self):
        booking = VehicleBooking(
            vehicle=self.vehicle, employee=self.employee, destination="Đồng Nai",
            start_time=self.at(10), end_time=self.at(9),
        )
        with self.assertRaises(ValidationError):
            booking.clean()

    def test_vehicle_booking_rejects_overlapping_approved_booking(self):
        VehicleBooking.objects.create(
            vehicle=self.vehicle, employee=self.employee, destination="Biên Hòa",
            start_time=self.at(10), end_time=self.at(11), status="Approved",
        )
        overlapping = VehicleBooking(
            vehicle=self.vehicle, employee=self.employee, destination="Long Khánh",
            start_time=self.at(10, 30), end_time=self.at(11, 30),
        )
        with self.assertRaises(ValidationError):
            overlapping.clean()

    def test_office_document_attachment_rejects_executable_upload(self):
        for model in (IncomingDocument, OutgoingDocument):
            with self.subTest(model=model.__name__):
                field = model._meta.get_field("attachment")
                with self.assertRaises(ValidationError):
                    field.validators[0](SimpleUploadedFile("virus.exe", b"not executable"))


class OfficeViewPermissionTests(OfficeTestBase):
    def test_employee_can_submit_vehicle_booking_for_approval(self):
        self.client.force_login(self.make_user("EMPLOYEE", "off-vehicle-requester"))
        response = self.client.post(reverse("portal:vehicle_booking_create"), {
            "vehicle": self.vehicle.pk,
            "destination": "Biên Hòa",
            "start_time": "2026-10-05T15:00",
            "end_time": "2026-10-05T16:00",
        })
        self.assertRedirects(response, reverse("portal:vehicle_booking_list"))
        self.assertTrue(VehicleBooking.objects.filter(
            vehicle=self.vehicle, employee=self.employee,
            destination="Biên Hòa", status="Pending",
        ).exists())

    def test_employee_cannot_approve_room_booking_by_direct_post(self):
        booking = RoomBooking.objects.create(
            room=self.room, employee=self.employee, purpose="Họp chờ duyệt",
            start_time=self.at(10), end_time=self.at(11), status="Pending",
        )
        self.client.force_login(self.make_user("EMPLOYEE", "off-employee-approver"))

        response = self.client.post(
            reverse("portal:room_booking_approve", args=(booking.pk,)), {"decision": "Approved"}
        )

        booking.refresh_from_db()
        self.assertRedirects(response, reverse("portal:dashboard"))
        self.assertEqual(booking.status, "Pending")
