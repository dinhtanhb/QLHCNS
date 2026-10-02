from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.organization.models import Department, JobTitle, Organization, Position
from apps.security.models import Role, User


class OrganizationModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            organization_code="ORG-TST", organization_name="Tổ chức kiểm thử"
        )
        cls.department = Department.objects.create(
            organization=cls.organization, department_code="ORG-DPT", department_name="Phòng thử"
        )

    def test_organization_code_is_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Organization.objects.create(
                    organization_code="ORG-TST", organization_name="Tổ chức trùng"
                )

    def test_department_code_is_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Department.objects.create(
                    organization=self.organization, department_code="ORG-DPT", department_name="Phòng trùng"
                )

    def test_position_code_is_unique(self):
        Position.objects.create(position_code="ORG-POS", position_name="Nhân viên")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Position.objects.create(position_code="ORG-POS", position_name="Chức danh trùng")

    def test_job_title_code_is_unique(self):
        JobTitle.objects.create(job_title_code="ORG-JOB", job_title_name="Điều phối viên")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobTitle.objects.create(job_title_code="ORG-JOB", job_title_name="Chức danh trùng")


class OrganizationPortalAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(
            organization_code="ORG-VIEW", organization_name="Tổ chức sơ đồ"
        )
        department = Department.objects.create(
            organization=organization, department_code="ORG-VIEW-D", department_name="Phòng xem"
        )
        position = Position.objects.create(position_code="ORG-VIEW-P", position_name="Nhân viên")
        employee = Employee.objects.create(
            employee_code="ORG-VIEW-E", first_name="An", last_name="Kiểm thử", full_name="ORG-VIEW-E",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="ORG-VIEW-E",
            company_email="org-view@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=department, position=position,
        )
        role, _ = Role.objects.get_or_create(role_code="EMPLOYEE", defaults={"role_name": "Nhân viên"})
        cls.user = User.objects.create_user(
            username="org-chart-employee", password="test-password", employee=employee, role=role
        )

    def test_authenticated_employee_can_read_organization_chart(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("portal:org_chart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sơ đồ tổ chức")
