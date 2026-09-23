from datetime import date

from django.test import TestCase

from apps.hrm.models import Employee, EmployeePromotion, EmployeeTransfer
from apps.hrm.services import apply_due_employee_changes
from apps.organization.models import Department, Organization, Position


class EffectiveEmployeeChangeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="HR-EFFECT", organization_name="Test")
        cls.departments = [Department.objects.create(
            organization=org, department_code=f"E{i}", department_name=f"Department {i}",
        ) for i in range(3)]
        cls.positions = [Position.objects.create(
            position_code=f"EP{i}", position_name=f"Position {i}",
        ) for i in range(3)]
        cls.employee = Employee.objects.create(
            employee_code="EFFECT-1", first_name="An", last_name="Test", full_name="Test An",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="EFFECT-ID",
            company_email="effective@example.test", mobile_phone="0123456789",
            join_date=date(2020, 1, 1), department=cls.departments[0], position=cls.positions[0],
        )

    def test_future_transfer_does_not_change_current_department_early(self):
        EmployeeTransfer.objects.create(
            employee=self.employee, from_department=self.departments[0], to_department=self.departments[1],
            effective_date=date(2030, 6, 1),
        )
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.department, self.departments[0])
        apply_due_employee_changes(as_of=date(2030, 5, 31))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.department, self.departments[0])
        apply_due_employee_changes(as_of=date(2030, 6, 1))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.department, self.departments[1])

    def test_future_promotions_apply_in_effective_date_order(self):
        EmployeePromotion.objects.create(
            employee=self.employee, old_position=self.positions[0], new_position=self.positions[1],
            effective_date=date(2030, 6, 1),
        )
        EmployeePromotion.objects.create(
            employee=self.employee, old_position=self.positions[1], new_position=self.positions[2],
            effective_date=date(2030, 8, 1),
        )
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, self.positions[0])
        apply_due_employee_changes(as_of=date(2030, 7, 1))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, self.positions[1])
        apply_due_employee_changes(as_of=date(2030, 8, 1))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, self.positions[2])

    def test_past_effective_transfer_applies_when_saved(self):
        EmployeeTransfer.objects.create(
            employee=self.employee, from_department=self.departments[0], to_department=self.departments[2],
            effective_date=date(2020, 1, 1),
        )
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.department, self.departments[2])
