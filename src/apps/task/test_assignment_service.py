from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections
from django.test import TransactionTestCase

from apps.task.models import Task
from apps.task.tests import TaskModelTestBase


class TaskCodeAllocationTests(TaskModelTestBase):
    def test_internal_sequence_ignores_legacy_codes_and_reserves_deleted(self):
        from apps.task.services import create_manual_task
        for code in ("CV01", "ACT-5-REPORT", "46.9.3.1", "CV-2026-0007"):
            self.make_task(task_code=code, status="Todo").save()
        Task.objects.filter(task_code="CV-2026-0007").delete()
        task = create_manual_task(year=2026, task_name="Synthetic", assigned_by_employee=self.employee,
                                  assigned_to_employee=self.employee)
        self.assertEqual(task.task_code, "CV-2026-0008")
        self.assertEqual(set(Task.objects.values_list("task_code", flat=True)),
                         {"CV01", "ACT-5-REPORT", "46.9.3.1", "CV-2026-0008"})


class ConcurrentTaskCodeTests(TransactionTestCase):
    def test_two_creators_receive_distinct_codes(self):
        from apps.task.services import create_manual_task
        TaskModelTestBase.setUpTestData.__func__(TaskModelTestBase)
        employee_id = TaskModelTestBase.employee.pk
        barrier = Barrier(2)

        def create():
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return create_manual_task(year=2026, task_name="Concurrent synthetic",
                                          assigned_by_employee_id=employee_id,
                                          assigned_to_employee_id=employee_id).task_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: create(), range(2)))
        self.assertEqual(set(results), {"CV-2026-0001", "CV-2026-0002"})
