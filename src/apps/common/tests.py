from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.common.uploads import build_upload_path
from apps.organization.models import Department, Organization


class SoftDeleteTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            organization_code="SOFT", organization_name="Soft-delete test",
        )
        self.department = Department.objects.create(
            organization=organization, department_code="SOFT-D", department_name="Test department",
        )

    def test_soft_deleted_records_are_hidden_but_recoverable(self):
        pk = self.department.pk
        count, _ = self.department.delete()
        self.assertEqual(count, 1)
        self.assertFalse(Department.objects.filter(pk=pk).exists())
        deleted = Department.all_objects.get(pk=pk)
        self.assertTrue(deleted.is_deleted)
        self.assertEqual(Department.all_objects.filter(is_deleted=True).restore(), 1)
        self.assertTrue(Department.objects.filter(pk=pk).exists())

    def test_queryset_delete_is_soft_and_hard_delete_is_explicit(self):
        pk = self.department.pk
        self.assertEqual(Department.objects.filter(pk=pk).delete()[0], 1)
        self.assertTrue(Department.all_objects.filter(pk=pk, is_deleted=True).exists())
        self.assertEqual(Department.all_objects.filter(pk=pk).hard_delete()[0], 1)
        self.assertFalse(Department.all_objects.filter(pk=pk).exists())


class UploadPathTests(TestCase):
    @patch("apps.common.uploads.timezone.localdate", return_value=date(2027, 1, 1))
    def test_upload_path_uses_configured_local_date(self, localdate):
        path = build_upload_path("documents", "Biên bản.pdf")

        self.assertTrue(path.startswith("documents/2027/01/bien-ban-"))
        self.assertTrue(path.endswith(".pdf"))
        localdate.assert_called_once_with()
