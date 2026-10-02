from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.project.models import Project


class ProjectModelTests(TestCase):
    def test_project_code_is_unique(self):
        Project.objects.create(project_code="PRJ-TEST", project_name="Dự án kiểm thử")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Project.objects.create(project_code="PRJ-TEST", project_name="Dự án trùng")


# `apps.project` currently defines a model/admin only and has no portal URL or
# CRUD view. Project-activity routes belong to `apps.activity` and have their
# own permission module; do not invent a Project CRUD policy for this test app.
