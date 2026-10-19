from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
from apps.task.tests import TaskModelTestBase


class TaskActCodeTests(TaskModelTestBase):
    def test_nullable_indexed_catalog_field(self):
        field = self.make_task()._meta.get_field("act_code")
        self.assertEqual((field.max_length, field.null, field.blank, field.db_index, field.db_column),
                         (50, True, True, True, "ActCode"))

    def test_catalog_and_administrative_values(self):
        for value in (None, next(iter(ACTIVITY_CODE_NAMES))):
            task = self.make_task(status="Todo", act_code=value)
            task.full_clean()
        with self.assertRaises(ValidationError) as error:
            self.make_task(status="Todo", act_code="REMOVED-CODE").full_clean()
        self.assertIn("act_code", error.exception.message_dict)

    def test_existing_historical_value_remains_editable(self):
        task = self.make_task(status="Todo", act_code="REMOVED-CODE")
        task.save()  # Historical value predates the current catalogue.
        task.task_name = "Updated historical task"
        task.full_clean()
        task.act_code = "ANOTHER-INVALID-CODE"
        with self.assertRaises(ValidationError):
            task.full_clean()


class TaskActCodeMigrationTests(TransactionTestCase):
    def test_apply_reverse_reapply_preserves_internal_codes(self):
        previous = [("task", "0003_task_completed_date")]
        target = [("task", "0005_backfill_act_code")]
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(previous)
            apps = executor.loader.project_state(previous).apps
            from datetime import date
            org = apps.get_model("organization", "Organization").objects.create(
                organization_code="MIG-ORG", organization_name="Synthetic")
            dept = apps.get_model("organization", "Department").objects.create(
                organization=org, department_code="MIG-DEPT", department_name="Synthetic")
            pos = apps.get_model("organization", "Position").objects.create(
                position_code="MIG-POS", position_name="Synthetic")
            employee = apps.get_model("hrm", "Employee").objects.create(
                employee_code="MIG-EMP", first_name="Synthetic", last_name="Test", full_name="Synthetic Test",
                date_of_birth=date(1990, 1, 1), gender="Other", national_id="MIG-EMP",
                company_email="migration@example.test", mobile_phone="0000000000",
                join_date=date(2020, 1, 1), department=dept, position=pos)
            code = next(iter(ACTIVITY_CODE_NAMES))
            codes = ("CV01", "ACT-5-REPORT", code, "46.9.REMOVED")
            old_task = apps.get_model("task", "Task")
            for value in codes:
                old_task.objects.create(task_code=value, task_name="Synthetic",
                                        assigned_by_employee=employee, assigned_to_employee=employee)
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            task = executor.loader.project_state(target).apps.get_model("task", "Task")
            self.assertEqual(dict(task.objects.values_list("task_code", "act_code")),
                             {value: code if value == code else None for value in codes})
            executor = MigrationExecutor(connection)
            executor.migrate(previous)
            old_task = executor.loader.project_state(previous).apps.get_model("task", "Task")
            self.assertEqual(set(old_task.objects.values_list("task_code", flat=True)), set(codes))
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            task = executor.loader.project_state(target).apps.get_model("task", "Task")
            self.assertEqual(task.objects.exclude(act_code=None).count(), 1)
        finally:
            MigrationExecutor(connection).migrate(target)
