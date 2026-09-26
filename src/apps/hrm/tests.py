from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from apps.hrm.models import Employee, EmployeePromotion, EmployeeTransfer, EmployeeProfileChangeRequest
from apps.hrm.services import apply_due_employee_changes
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User
from apps.notification.models import Notification


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


class EmployeeProfileChangeRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="PROFILE-ORG", organization_name="Profile tests")
        cls.department = Department.objects.create(
            organization=org, department_code="PROFILE-DEPT", department_name="Profile team"
        )
        cls.position = Position.objects.create(position_code="PROFILE-POS", position_name="Officer")

    def make_employee(self, suffix):
        return Employee.objects.create(
            employee_code=f"PROFILE-{suffix}", first_name="Test", last_name=suffix,
            full_name=f"Test {suffix}", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=f"PROFILE-ID-{suffix}", company_email=f"{suffix.lower()}@example.test",
            personal_email=f"{suffix.lower()}@personal.test", mobile_phone="0123456789",
            address="Old address", join_date=date(2020, 1, 1), department=self.department,
            position=self.position, employment_status="Active",
        )

    def make_user(self, employee, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(username=username, password="test-password", employee=employee, role=role)

    def test_raw_post_cannot_change_fields_outside_whitelist(self):
        employee = self.make_employee("WHITELIST")
        user = self.make_user(employee, "EMPLOYEE", "profile-whitelist")
        self.client.force_login(user)

        response = self.client.post(reverse("portal:profile_change_request_create"), {
            "field_name": "salary", "new_value": "1", "reason": "test",
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(EmployeeProfileChangeRequest.objects.exists())

    def test_employee_cannot_view_another_employees_requests_or_attachment(self):
        owner = self.make_employee("OWNER")
        other = self.make_employee("OTHER")
        request_item = EmployeeProfileChangeRequest.objects.create(
            employee=owner, field_name="address", old_value="Old address", new_value="New address",
            submitted_snapshot="Old address",
        )
        self.client.force_login(self.make_user(other, "EMPLOYEE", "profile-other"))

        list_response = self.client.get(reverse("portal:profile_change_request_list"))
        response = self.client.get(reverse("portal:profile_change_request_attachment", args=(request_item.pk,)))

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, owner.full_name)
        self.assertEqual(response.status_code, 404)

    def test_approval_is_blocked_if_value_changed_after_submission(self):
        employee = self.make_employee("SNAPSHOT")
        request_item = EmployeeProfileChangeRequest.objects.create(
            employee=employee, field_name="address", old_value="Old address", new_value="New address",
            submitted_snapshot="Old address",
        )
        employee.address = "HR updated address"
        employee.save(update_fields=("address",))
        self.client.force_login(self.make_user(self.make_employee("REVIEWER"), "HR_MANAGER", "profile-reviewer"))

        response = self.client.post(reverse("portal:profile_change_request_decide", args=(request_item.pk,)), {
            "decision": "approve",
        })

        request_item.refresh_from_db()
        employee.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request_item.status, "Pending")
        self.assertEqual(employee.address, "HR updated address")

    def test_approval_updates_only_whitelisted_field_and_notifies_employee(self):
        employee = self.make_employee("APPROVE")
        request_item = EmployeeProfileChangeRequest.objects.create(
            employee=employee, field_name="mobile_phone", old_value="0123456789",
            new_value="0987654321", submitted_snapshot="0123456789",
        )
        reviewer_employee = self.make_employee("HR")
        reviewer = self.make_user(reviewer_employee, "HR_OFFICER", "profile-hr-officer")
        self.client.force_login(reviewer)

        response = self.client.post(reverse("portal:profile_change_request_decide", args=(request_item.pk,)), {
            "decision": "approve", "note": "Verified",
        })

        request_item.refresh_from_db()
        employee.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request_item.status, "Approved")
        self.assertEqual(employee.mobile_phone, "0987654321")
        self.assertEqual(employee.address, "Old address")
        self.assertTrue(Notification.objects.filter(employee=employee, notification_type="profile-change").exists())

    def test_org_chart_hides_inactive_employees_and_handles_cycles(self):
        first = self.make_employee("TREE1")
        second = self.make_employee("TREE2")
        inactive = self.make_employee("TREE3")
        first.manager = second
        first.save(update_fields=("manager",))
        second.manager = first
        second.save(update_fields=("manager",))
        inactive.employment_status = "Resigned"
        inactive.save(update_fields=("employment_status",))
        self.client.force_login(self.make_user(first, "EMPLOYEE", "profile-tree"))

        response = self.client.get(reverse("portal:org_chart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first.full_name)
        self.assertContains(response, second.full_name)
        self.assertNotContains(response, inactive.full_name)
        self.assertNotContains(response, first.mobile_phone)
