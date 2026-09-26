from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.asset.models import Asset, AssetAllocation, AssetType
from apps.hrm.models import Employee
from apps.lifecycle.models import ChecklistTemplate, ChecklistTemplateItem, EmployeeLifecycleCase, LifecycleChecklistItem
from apps.lifecycle.services import open_onboarding_case, send_lifecycle_reminders
from apps.notification.models import Notification
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User


class LifecycleWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(organization_code="LIFE-ORG", organization_name="Lifecycle tests")
        cls.department = Department.objects.create(
            organization=organization, department_code="LIFE-DEPT", department_name="Lifecycle"
        )
        cls.position = Position.objects.create(position_code="LIFE-POS", position_name="Officer")

    def make_employee(self, suffix):
        return Employee.objects.create(
            employee_code=f"LIFE-{suffix}", first_name="Test", last_name=suffix,
            full_name=f"Lifecycle {suffix}", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=f"LIFE-ID-{suffix}", company_email=f"{suffix.lower()}@example.test",
            mobile_phone="0123456789", join_date=date(2020, 1, 1), department=self.department,
            position=self.position, employment_status="Active",
        )

    def make_user(self, employee, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(username=username, password="test-password", employee=employee, role=role)

    def make_template(self, code="ONBOARDING", role_code="HR_OFFICER", requires_asset_return=False):
        template = ChecklistTemplate.objects.create(
            template_code=code, template_name="Onboarding template", template_type="Onboarding"
        )
        item = ChecklistTemplateItem.objects.create(
            template=template, sequence=1, item_name="Prepare equipment",
            responsible_role_code=role_code, due_offset_days=2,
            requires_asset_return=requires_asset_return,
        )
        return template, item

    def test_open_onboarding_case_snapshots_template_items(self):
        employee = self.make_employee("SNAPSHOT")
        template, template_item = self.make_template()

        case, created = open_onboarding_case(employee, template)
        item = case.items.get()

        self.assertTrue(created)
        self.assertEqual(item.item_name, template_item.item_name)
        self.assertEqual(item.due_date, employee.join_date.replace(day=3))

    def test_template_edits_do_not_change_existing_checklist_snapshot(self):
        employee = self.make_employee("TEMPLATE")
        template, template_item = self.make_template()
        case, _ = open_onboarding_case(employee, template)
        template_item.item_name = "Changed template item"
        template_item.due_offset_days = 50
        template_item.save(update_fields=("item_name", "due_offset_days"))

        item = case.items.get()
        self.assertEqual(item.item_name, "Prepare equipment")
        self.assertEqual(item.due_date, date(2020, 1, 3))

    def test_duplicate_trigger_is_idempotent(self):
        employee = self.make_employee("DUPLICATE")
        template, _ = self.make_template(code="ONBOARDING-DUP")

        first, created_first = open_onboarding_case(employee, template)
        second, created_second = open_onboarding_case(employee, template)

        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(EmployeeLifecycleCase.objects.filter(employee=employee).count(), 1)
        self.assertEqual(LifecycleChecklistItem.objects.filter(case=first).count(), 1)

    def test_non_hr_user_cannot_access_assigned_hr_checklist(self):
        employee = self.make_employee("OWNER")
        other_employee = self.make_employee("OTHER")
        assignee = self.make_user(self.make_employee("ASSIGNEE"), "EMPLOYEE", "lifecycle-assignee")
        template, template_item = self.make_template(code="ASSIGN-TPL", role_code="EMPLOYEE")
        case, _ = open_onboarding_case(employee, template)
        item = case.items.get()
        item.assigned_to_user = assignee
        item.save(update_fields=("assigned_to_user",))
        other_template, _ = self.make_template(code="OTHER-TPL")
        other_case, _ = open_onboarding_case(other_employee, other_template)
        self.client.force_login(assignee)

        listing = self.client.get(reverse("portal:lifecycle_case_list"))
        own_detail = self.client.get(reverse("portal:lifecycle_case_detail", args=(case.pk,)))
        forbidden = self.client.get(reverse("portal:lifecycle_case_detail", args=(other_case.pk,)))
        completed = self.client.post(reverse("portal:lifecycle_item_update", args=(item.pk,)), {"action": "done"})

        item.refresh_from_db()
        case.refresh_from_db()
        self.assertEqual(listing.status_code, 403)
        self.assertEqual(own_detail.status_code, 403)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(completed.status_code, 403)
        self.assertEqual(item.status, "Pending")
        self.assertEqual(case.status, "Open")

    def test_project_roles_cannot_access_assigned_hr_checklists(self):
        case_employee = self.make_employee("COORD-TGT")
        coordinator_employee = self.make_employee("COORD-ASG")
        coordinator = self.make_user(
            coordinator_employee, "PROJECT_COORDINATOR", "lifecycle-coordinator"
        )
        unrelated = self.make_user(
            self.make_employee("COORD-OTH"), "PROJECT_MANAGER", "lifecycle-unrelated"
        )
        template, _ = self.make_template(code="COORD-TPL", role_code="PROJECT_COORDINATOR")
        case, _ = open_onboarding_case(case_employee, template)
        item = case.items.get()
        item.assigned_to_user = coordinator
        item.save(update_fields=("assigned_to_user",))

        self.client.force_login(coordinator)
        listing = self.client.get(reverse("portal:lifecycle_case_list"))
        detail = self.client.get(reverse("portal:lifecycle_case_detail", args=(case.pk,)))
        self.assertEqual(listing.status_code, 403)
        self.assertEqual(detail.status_code, 403)

        self.client.force_login(unrelated)
        unrelated_listing = self.client.get(reverse("portal:lifecycle_case_list"))
        unrelated_detail = self.client.get(reverse("portal:lifecycle_case_detail", args=(case.pk,)))
        self.assertEqual(unrelated_listing.status_code, 403)
        self.assertEqual(unrelated_detail.status_code, 403)

    def test_hr_can_link_existing_asset_return_without_deleting_allocation_history(self):
        employee = self.make_employee("OFFBOARD")
        template, _ = self.make_template(code="ASSET-TPL", role_code="HR_OFFICER", requires_asset_return=True)
        case, _ = open_onboarding_case(employee, template)
        item = case.items.get()
        hr_employee = self.make_employee("ASSET-HR")
        hr_user = self.make_user(hr_employee, "HR_OFFICER", "lifecycle-asset-hr")
        asset_type = AssetType.objects.create(asset_type_code="LIFE-LAPTOP", asset_type_name="Laptop")
        asset = Asset.objects.create(asset_code="LIFE-ASSET-1", asset_name="Test laptop", asset_type=asset_type)
        allocation = AssetAllocation.objects.create(
            asset=asset, employee=employee, assigned_date=date(2020, 1, 3), return_date=date(2026, 2, 1)
        )
        self.client.force_login(hr_user)

        response = self.client.post(reverse("portal:lifecycle_item_update", args=(item.pk,)), {
            "action": "done", "asset_allocation_id": allocation.pk,
        })

        item.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(item.asset_allocation_id, allocation.pk)
        self.assertTrue(AssetAllocation.objects.filter(pk=allocation.pk).exists())

    def test_hr_cannot_assign_checklist_step_to_non_hr_user(self):
        employee = self.make_employee("ASG-T")
        template, _ = self.make_template(code="ASSIGN-EMPLOYEE-TPL", role_code="EMPLOYEE")
        case, _ = open_onboarding_case(employee, template)
        item = case.items.get()
        non_hr = self.make_user(self.make_employee("ASG-N"), "EMPLOYEE", "lifecycle-non-hr")
        hr_user = self.make_user(self.make_employee("ASG-H"), "HR_OFFICER", "lifecycle-hr-assign")
        self.client.force_login(hr_user)

        response = self.client.post(
            reverse("portal:lifecycle_item_assign", args=(item.pk,)),
            {"assigned_to_user_id": non_hr.pk},
        )

        item.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(item.assigned_to_user_id)

    def test_overdue_reminder_is_deduplicated_each_day_and_shows_on_dashboard(self):
        employee = self.make_employee("REMIND")
        hr_employee = self.make_employee("REMIND-HR")
        assignee = self.make_user(hr_employee, "HR_OFFICER", "lifecycle-remind")
        template, _ = self.make_template(code="REMINDER-TPL")
        case, _ = open_onboarding_case(employee, template)
        item = case.items.get()
        item.assigned_to_user = assignee
        item.due_date = date(2020, 1, 2)
        item.save(update_fields=("assigned_to_user", "due_date"))

        first = send_lifecycle_reminders(today=date(2026, 9, 26))
        duplicate = send_lifecycle_reminders(today=date(2026, 9, 26))
        next_day = send_lifecycle_reminders(today=date(2026, 9, 27))
        dashboard = self.client.get(reverse("portal:dashboard"))

        self.assertEqual((first, duplicate, next_day), (1, 0, 1))
        self.assertEqual(Notification.objects.filter(employee=hr_employee, notification_type="LifecycleOverdue").count(), 2)
        self.assertEqual(dashboard.status_code, 302)  # Anonymous users must sign in.
        self.client.force_login(assignee)
        dashboard = self.client.get(reverse("portal:dashboard"))
        self.assertContains(dashboard, "Checklist onboarding/offboarding quá hạn")
