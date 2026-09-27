from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.contract.models import Contract, ContractType
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User


class ContractTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(
            organization_code="CON-ORG", organization_name="Tổ chức kiểm thử hợp đồng"
        )
        cls.department = Department.objects.create(
            organization=org, department_code="CON-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="CON-POS", position_name="Nhân viên")
        cls.employee = cls.make_employee("CON-EMP-1")
        cls.other_employee = cls.make_employee("CON-EMP-2")
        cls.contract_type = ContractType.objects.create(
            contract_type_code="CON-FULLTIME", contract_type_name="Không xác định thời hạn"
        )

    @classmethod
    def make_employee(cls, code):
        return Employee.objects.create(
            employee_code=code, first_name="An", last_name="Kiểm thử", full_name=code,
            date_of_birth=date(1990, 1, 1), gender="Other", national_id=code,
            company_email=f"{code.lower()}@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )

    @classmethod
    def make_user(cls, role_code, employee, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=employee, role=role
        )

    def make_contract(self, employee=None, contract_no="CON-VALID"):
        return Contract(
            employee=employee or self.employee, contract_type=self.contract_type,
            contract_no=contract_no, start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31), basic_salary="12000000",
        )


class ContractValidationTests(ContractTestBase):
    def test_rejects_end_date_before_start_date(self):
        contract = self.make_contract()
        contract.end_date = date(2024, 12, 31)
        with self.assertRaises(ValidationError):
            contract.full_clean()

    def test_allows_contract_without_end_date(self):
        contract = self.make_contract()
        contract.end_date = None
        contract.full_clean()


class ContractViewPermissionTests(ContractTestBase):
    def test_employee_cannot_read_another_employees_contract_from_hr_list(self):
        confidential_contract = self.make_contract(self.other_employee, "CON-PRIVATE-1")
        confidential_contract.save()
        user = self.make_user("EMPLOYEE", self.employee, "con-employee-reader")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:hr_contract_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            confidential_contract,
            list(response.context["contracts"]),
            "Nhân viên không được nhận hồ sơ hợp đồng của người khác trong context của trang HR.",
        )

    def test_employee_cannot_create_contract_by_direct_post(self):
        user = self.make_user("EMPLOYEE", self.employee, "con-employee-writer")
        self.client.force_login(user)

        response = self.client.post(reverse("portal:hr_contract_create"), {
            "employee": self.employee.pk,
            "contract_type": self.contract_type.pk,
            "contract_no": "CON-FORBIDDEN-1",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "basic_salary": "12000000",
        })

        self.assertRedirects(response, reverse("portal:hr_contract_list"))
        self.assertFalse(Contract.objects.filter(contract_no="CON-FORBIDDEN-1").exists())
