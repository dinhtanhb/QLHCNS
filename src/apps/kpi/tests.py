from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.kpi.models import CompanyKPI, EmployeeKPI, KPIPeriod, KPITemplate
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User

D = Decimal


class KPITestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="KPI-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="KPI-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="KPI-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="KPI-EMP", first_name="An", last_name="Kiểm thử", full_name="KPI-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="KPI-EMP",
            company_email="kpi-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )
        cls.period = KPIPeriod.objects.create(year=2026, quarter=3)
        cls.template = KPITemplate.objects.create(kpi_name="Hoàn thành kế hoạch", weight=D("25"))

    @classmethod
    def make_user(cls, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=cls.employee, role=role
        )


class KPICalculationTests(KPITestBase):
    def test_employee_kpi_persists_achievement_and_weighted_score(self):
        result = EmployeeKPI.objects.create(
            employee=self.employee, kpi_template=self.template, kpi_period=self.period,
            target=D("8"), actual=D("6"),
        )

        self.assertEqual(result.achievement, D("75.00"))
        self.assertEqual(result.score, D("18.75"))

    def test_zero_target_does_not_divide_by_zero(self):
        result = CompanyKPI.objects.create(
            kpi_template=self.template, kpi_period=self.period, target=D("0"), actual=D("5"),
        )

        self.assertEqual(result.achievement, D("0"))
        self.assertEqual(result.score, D("0"))


class KPIViewPermissionTests(KPITestBase):
    def test_employee_cannot_score_kpi_by_direct_post(self):
        result = EmployeeKPI.objects.create(
            employee=self.employee, kpi_template=self.template, kpi_period=self.period,
            target=D("10"), actual=D("2"),
        )
        self.client.force_login(self.make_user("EMPLOYEE", "kpi-employee-scorer"))

        response = self.client.post(
            reverse("portal:kpi_score_update", args=(result.pk,)), {"actual": "9"}
        )

        result.refresh_from_db()
        self.assertRedirects(response, reverse("portal:dashboard"))
        self.assertEqual(result.actual, D("2"))
