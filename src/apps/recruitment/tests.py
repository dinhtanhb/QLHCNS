from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.recruitment.models import Candidate, RecruitmentRequest
from apps.security.models import Role, User


class RecruitmentTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="REC-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="REC-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="REC-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="REC-EMP", first_name="An", last_name="Kiểm thử", full_name="REC-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="REC-EMP",
            company_email="rec-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )

    @classmethod
    def make_user(cls, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=cls.employee, role=role
        )


class RecruitmentModelValidationTests(RecruitmentTestBase):
    def test_candidate_cv_rejects_executable_upload(self):
        field = Candidate._meta.get_field("cv_file")
        with self.assertRaises(ValidationError):
            field.validators[0](SimpleUploadedFile("virus.exe", b"not executable"))

    def test_recruitment_request_code_is_unique(self):
        RecruitmentRequest.objects.create(
            request_code="REC-REQ-1", department=self.department, position=self.position,
            required_date=date(2026, 11, 1),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecruitmentRequest.objects.create(
                    request_code="REC-REQ-1", department=self.department, position=self.position,
                    required_date=date(2026, 12, 1),
                )


class RecruitmentViewPermissionTests(RecruitmentTestBase):
    def test_employee_cannot_create_recruitment_request_by_direct_post(self):
        self.client.force_login(self.make_user("EMPLOYEE", "rec-employee-requester"))

        response = self.client.post(reverse("portal:recruitment_create"), {
            "request_code": "REC-FORBIDDEN-1",
            "department": self.department.pk,
            "position": self.position.pk,
            "required_quantity": "1",
            "required_date": "2026-11-01",
        })

        self.assertRedirects(response, reverse("portal:recruitment_list"))
        self.assertFalse(RecruitmentRequest.objects.filter(request_code="REC-FORBIDDEN-1").exists())

    def test_employee_cannot_approve_recruitment_request_by_direct_post(self):
        request = RecruitmentRequest.objects.create(
            request_code="REC-PENDING-1", department=self.department, position=self.position,
            required_date=date(2026, 11, 1),
        )
        self.client.force_login(self.make_user("EMPLOYEE", "rec-employee-approver"))

        response = self.client.post(
            reverse("portal:recruitment_approve", args=(request.pk,)), {"decision": "Approved"}
        )

        request.refresh_from_db()
        self.assertRedirects(response, reverse("portal:recruitment_list"))
        self.assertEqual(request.status, "Pending")
