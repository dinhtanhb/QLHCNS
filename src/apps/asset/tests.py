from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.asset.models import Asset, AssetAllocation, AssetType, InventoryLine, InventorySession
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position


class AssetSafetyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="ASORG", organization_name="Test")
        department = Department.objects.create(organization=org, department_code="ASD", department_name="Test")
        position = Position.objects.create(position_code="ASP", position_name="Test")
        cls.employees = [Employee.objects.create(
            employee_code=f"AS{i}", first_name=f"Employee {i}", last_name="Test",
            full_name=f"Employee {i}", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=f"ASID{i}", company_email=f"as{i}@example.test", mobile_phone="0123456789",
            join_date=date(2020, 1, 1), department=department, position=position,
        ) for i in range(1, 3)]
        asset_type = AssetType.objects.create(asset_type_code="AST", asset_type_name="Equipment")
        cls.asset = Asset.objects.create(asset_code="ASSET-1", asset_name="Laptop", asset_type=asset_type)

    def test_asset_cannot_be_assigned_to_two_employees_at_once(self):
        AssetAllocation.objects.create(
            asset=self.asset, employee=self.employees[0], assigned_date=date(2025, 1, 1),
        )
        with self.assertRaises(ValidationError):
            AssetAllocation.objects.create(
                asset=self.asset, employee=self.employees[1], assigned_date=date(2025, 2, 1),
            )
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, "InUse")
        self.assertEqual(AssetAllocation.objects.filter(asset=self.asset, return_date__isnull=True).count(), 1)

    def test_asset_can_be_reassigned_after_return(self):
        allocation = AssetAllocation.objects.create(
            asset=self.asset, employee=self.employees[0], assigned_date=date(2025, 1, 1),
        )
        allocation.return_date = date(2025, 1, 31)
        allocation.save()
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, "Available")
        AssetAllocation.objects.create(
            asset=self.asset, employee=self.employees[1], assigned_date=date(2025, 2, 1),
        )

    def test_inventory_session_cannot_complete_with_uncounted_lines(self):
        session = InventorySession.objects.create(
            session_name="Annual", office_name="Test", inventory_datetime="2025-01-01T09:00:00Z",
        )
        InventoryLine.objects.create(session=session, asset=self.asset)
        session.status = "Completed"
        with self.assertRaises(ValidationError):
            session.save()
        session.refresh_from_db()
        self.assertEqual(session.status, "Draft")

    def test_inventory_session_completes_after_all_lines_are_counted(self):
        session = InventorySession.objects.create(
            session_name="Annual", office_name="Test", inventory_datetime="2025-01-01T09:00:00Z",
        )
        line = InventoryLine.objects.create(session=session, asset=self.asset, is_counted=True)
        session.status = "Completed"
        session.save()
        self.assertEqual(session.status, "Completed")
        line.is_counted = False
        with self.assertRaises(ValidationError):
            line.save()
