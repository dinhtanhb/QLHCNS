from datetime import date
from django.utils import timezone

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.recruitment.models import Candidate, RecruitmentRequest, Interview, Offer
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

    def test_hr_offer_update_status_rejects_invalid_choice(self):
        hr_user = self.make_user("HR_MANAGER", "rec-hr-mgr-offer")
        candidate = Candidate.objects.create(
            candidate_code="CAN-OFFER-1",
            full_name="Ứng viên Test", email="candidate@test.com", phone_number="0912345678",
        )
        offer = Offer.objects.create(
            candidate=candidate, offer_date=date(2026, 10, 1), expected_join_date=date(2026, 10, 15),
            salary_offer=10000000, status="Sent",
        )
        self.client.force_login(hr_user)
        response = self.client.post(
            reverse("portal:hr_offer_update_status", args=(offer.pk,)),
            {"status": "NOT_A_VALID_STATUS"},
        )
        self.assertRedirects(response, reverse("portal:hr_candidate_detail", args=(candidate.pk,)))
        offer.refresh_from_db()
        self.assertEqual(offer.status, "Sent")

    def test_hr_interview_result_rejects_invalid_choice(self):
        hr_user = self.make_user("HR_MANAGER", "rec-hr-mgr-interview")
        candidate = Candidate.objects.create(
            candidate_code="CAN-INTERVIEW-1",
            full_name="Ứng viên Phỏng vấn", email="cand-interview@test.com", phone_number="0912345679",
        )
        interview = Interview.objects.create(
            candidate=candidate, interview_date=timezone.now(), interview_type="Online",
            interviewer=self.employee, result="Pending",
        )
        self.client.force_login(hr_user)
        response = self.client.post(
            reverse("portal:hr_interview_result", args=(interview.pk,)),
            {"result": "INVALID_RESULT", "comments": "Không hợp lệ"},
        )
        self.assertRedirects(response, reverse("portal:hr_candidate_detail", args=(candidate.pk,)))
        interview.refresh_from_db()
        self.assertEqual(interview.result, "Pending")
