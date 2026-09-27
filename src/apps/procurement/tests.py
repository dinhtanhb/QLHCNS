from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.procurement.models import ProcurementItem, ProcurementRequest
from apps.security.models import Role, User


class ProcurementTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="PRO-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="PRO-DEPT", department_name="Phòng kiểm thử"
        )
        position = Position.objects.create(position_code="PRO-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="PRO-EMP", first_name="An", last_name="Kiểm thử", full_name="PRO-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="PRO-EMP",
            company_email="pro-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=position,
        )

    @classmethod
    def make_user(cls, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=cls.employee, role=role
        )


class ProcurementModelTests(ProcurementTestBase):
    def test_request_total_estimated_cost_sums_quantity_times_unit_cost(self):
        request = ProcurementRequest.objects.create(
            request_no="PRO-REQ-1", requested_by=self.employee, department=self.department,
            request_date=date(2026, 9, 27),
        )
        ProcurementItem.objects.create(
            procurement_request=request, item_name="Máy tính", quantity=2,
            estimated_cost=Decimal("12500000"),
        )
        ProcurementItem.objects.create(
            procurement_request=request, item_name="Chuột", quantity=3,
            estimated_cost=Decimal("250000"),
        )

        self.assertEqual(request.total_estimated_cost, Decimal("25750000"))


class ProcurementViewPermissionTests(ProcurementTestBase):
    def test_procurement_request_list_is_renderable(self):
        """The employee-facing list route must render instead of failing at template lookup."""
        self.client.force_login(self.make_user("EMPLOYEE", "pro-employee-reader"))

        response = self.client.get(reverse("portal:procurement_request_list"))

        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_create_procurement_request_by_direct_post(self):
        self.client.force_login(self.make_user("EMPLOYEE", "pro-employee-requester"))

        response = self.client.post(reverse("portal:procurement_request_create"), {
            "reason": "Không được phép",
            "item_name": ["Máy tính"],
            "quantity": ["1"],
            "estimated_cost": ["1000000"],
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("portal:procurement_request_list"))
        self.assertFalse(ProcurementRequest.objects.exists())
