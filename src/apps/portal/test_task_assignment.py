from django.test import TestCase
from django.urls import reverse
from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
from apps.portal import test_home_dashboard as home_fixtures
from apps.task.models import Task


class TaskAssignmentTests(TestCase):
    user = home_fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        home_fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.manager = self.user("HR_MANAGER", True)
        self.assignee = self.user("EMPLOYEE", True)
        self.client.force_login(self.manager)
        self.url = reverse("portal:task_create")
        self.payload = {"act_code": next(iter(ACTIVITY_CODE_NAMES)), "task_name": "Forged title",
                        "assigned_to_employee": str(self.assignee.employee_id), "description": "Retained description"}

    def test_same_actcode_three_times_has_unique_internal_codes(self):
        for _ in range(3):
            self.assertRedirects(self.client.post(self.url, self.payload), reverse("portal:task_list"))
        tasks = Task.objects.filter(act_code=self.payload["act_code"])
        self.assertEqual(tasks.count(), 3)
        self.assertEqual(len(set(tasks.values_list("task_code", flat=True))), 3)
        self.assertTrue(all(t.task_code.startswith("CV-") and t.task_name == ACTIVITY_CODE_NAMES[t.act_code] for t in tasks))

    def test_other_needs_name_and_retains_input_then_saves_null(self):
        self.payload.update(act_code="__OTHER__", task_name="")
        self.assertContains(self.client.post(self.url, self.payload), "Retained description")
        self.assertFalse(Task.objects.exists())
        self.payload["task_name"] = "A" * 301
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 200)
        self.assertFalse(Task.objects.exists())
        self.payload["task_name"] = "Administrative assignment"
        self.assertRedirects(self.client.post(self.url, self.payload), reverse("portal:task_list"))
        task = Task.objects.get()
        self.assertIsNone(task.act_code)
        self.assertEqual(task.task_name, self.payload["task_name"])

    def test_unknown_catalog_rejected_and_choice_kept_on_error(self):
        self.payload["act_code"] = "INVALID"
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 200)
        self.assertFalse(Task.objects.exists())
        self.payload.update(act_code=next(iter(ACTIVITY_CODE_NAMES)), priority="INVALID")
        page = self.client.post(self.url, self.payload)
        self.assertContains(page, 'value="'+self.payload["act_code"]+'" selected')
        self.assertContains(page, "Retained description")

    def test_catalog_shown_below_name_and_internal_code_in_success(self):
        response = self.client.post(self.url, self.payload, follow=True)
        task = Task.objects.get()
        self.assertContains(response, task.task_code)
        self.assertContains(self.client.get(reverse("portal:task_list"), {"scope": "assigned_by_me"}), "ActCode "+task.act_code)
        self.assertContains(self.client.get(reverse("portal:task_detail", args=[task.pk])), "ActCode "+task.act_code)

    def test_native_form_supports_no_js_and_has_no_inline_executable_script(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="act_code"')
        self.assertNotContains(response, 'name="task_code"')
        self.assertNotContains(response, "function fillName()")
        self.assertNotContains(response, 'readonly id="task_create-task_name"')
