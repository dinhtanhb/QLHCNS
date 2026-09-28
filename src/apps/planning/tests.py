from datetime import date
from decimal import Decimal
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Holiday
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.planning.models import AnnualBudget, HeadcountPlan, TrainingCourse, TrainingEnrollment
from apps.security.models import Role, User

D = Decimal


class PlanningTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="PLN-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="PLN-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="PLN-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="PLN-EMP", first_name="An", last_name="Kiểm thử", full_name="PLN-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="PLN-EMP",
            company_email="pln-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )

    @classmethod
    def make_user(cls, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=cls.employee, role=role
        )


class PlanningUniqueConstraintTests(PlanningTestBase):
    def test_headcount_plan_is_unique_by_year_and_department(self):
        HeadcountPlan.objects.create(year=2026, department=self.department, planned_headcount=10)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HeadcountPlan.objects.create(year=2026, department=self.department, planned_headcount=12)

    def test_training_enrollment_is_unique_by_course_and_employee(self):
        course = TrainingCourse.objects.create(
            course_code="PLN-COURSE-1", course_name="An toàn", start_date=date(2026, 10, 1)
        )
        TrainingEnrollment.objects.create(course=course, employee=self.employee)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TrainingEnrollment.objects.create(course=course, employee=self.employee)

    def test_annual_budget_is_unique_by_year_department_and_category(self):
        AnnualBudget.objects.create(
            year=2026, department=self.department, category="Other", allocated_amount=D("1000")
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AnnualBudget.objects.create(
                    year=2026, department=self.department, category="Other", allocated_amount=D("2000")
                )

    @skipUnless(
        connection.vendor == "microsoft",
        "SQL Server treats NULL as equal for this unique index; SQLite allows multiple NULL values.",
    )
    def test_company_wide_annual_budget_with_null_department_is_unique(self):
        """SQL Server-specific NULL uniqueness; this is not a production defect on SQL Server."""
        AnnualBudget.objects.create(
            year=2026, department=None, category="Other", allocated_amount=D("1000")
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AnnualBudget.objects.create(
                    year=2026, department=None, category="Other", allocated_amount=D("2000")
                )


class PlanningViewPermissionTests(PlanningTestBase):
    def test_employee_cannot_create_company_holiday_by_direct_post(self):
        self.client.force_login(self.make_user("EMPLOYEE", "pln-employee-calendar"))

        response = self.client.post(reverse("portal:holiday_list"), {
            "holiday_code": "PLN-FORBIDDEN-HOLIDAY",
            "holiday_name": "Không được tạo",
            "holiday_date": "2026-12-31",
        })

        self.assertRedirects(response, reverse("portal:dashboard"))
        self.assertFalse(Holiday.objects.filter(holiday_code="PLN-FORBIDDEN-HOLIDAY").exists())
