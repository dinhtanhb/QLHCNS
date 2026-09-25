from datetime import date, timedelta, timedelta
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.activity.models import Activity
from apps.activity.services import (
    add_company_workdays,
    find_schedule_conflicts,
    send_activity_report_reminders,
)
from apps.attendance.models import Holiday
from apps.hrm.models import Employee
from apps.notification.models import Notification
from apps.office.models import OutgoingDocument
from apps.organization.models import Department, Organization, Position
from apps.project.models import Project
from apps.security.models import Role, User
from apps.task.models import Task


class ActivityTestDataMixin:
    def setUp(self):
        self.organization = Organization.objects.create(
            organization_code="ORG-ACT", organization_name="Tổ chức kiểm thử"
        )
        self.department = Department.objects.create(
            department_code="DEP-ACT", department_name="Chương trình",
            organization=self.organization,
        )
        self.position = Position.objects.create(
            position_code="POS-ACT", position_name="Cán bộ dự án"
        )
        self.cbda = self.make_employee("A")
        self.coordinator = self.make_employee("COORD")
        self.project = Project.objects.create(
            project_code="PRJ-ACT", project_name="Dự án thử", department=self.department
        )
        self.dispatch = OutgoingDocument.objects.create(
            outgoing_no="CV-ACT-001", outgoing_date=date(2026, 9, 25),
            recipient="Đối tác", subject="Kế hoạch hoạt động",
            signed_by=self.coordinator,
        )

    def make_employee(self, suffix):
        return Employee.objects.create(
            employee_code=f"EMP-ACT-{suffix}", first_name=suffix, last_name="Test",
            full_name=f"{suffix} Test", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=f"TESTID{suffix}", company_email=f"{suffix.lower()}@example.test",
            mobile_phone="0000000000", join_date=date(2020, 1, 1),
            department=self.department, position=self.position,
        )

    def make_activity(self, code="ACT-001", dispatch=None, lead=None):
        return Activity.objects.create(
            activity_code=code, activity_name=f"Hoạt động {code}", project=self.project,
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 1),
            lead_cbda=lead or self.cbda, coordinator=self.coordinator,
            outgoing_document=dispatch,
        )


class ActivityWorkflowTests(ActivityTestDataMixin, TestCase):
    def test_overlapping_cbda_schedule_is_detected_but_can_be_reviewed(self):
        first = self.make_activity("ACT-OVERLAP-1")
        second = self.make_activity("ACT-OVERLAP-2")

        second.full_clean()
        conflicts = find_schedule_conflicts(
            self.cbda.pk, second.start_date, second.end_date, exclude_activity_id=second.pk
        )

        self.assertEqual([activity.pk for activity in conflicts], [first.pk])

    def test_report_deadline_counts_company_workdays_and_holidays(self):
        Holiday.objects.create(
            holiday_code="HOL-ACT-01", holiday_name="Ngày nghỉ thử",
            holiday_date=date(2026, 10, 2),
        )

        # 25/09/2026 is Friday. 10 workdays after it, skipping weekends and
        # the configured holiday, lands on Monday 12/10/2026.
        self.assertEqual(
            add_company_workdays(date(2026, 9, 25), 10),
            date(2026, 10, 12),
        )

    def test_linking_issued_dispatch_creates_one_assigned_report_task(self):
        activity = self.make_activity(dispatch=self.dispatch)

        task = Task.objects.get(activity=activity)
        self.assertEqual(task.assigned_to_employee, self.cbda)
        self.assertEqual(task.assigned_by_employee, self.coordinator)
        self.assertEqual(task.due_date, date(2026, 10, 9))
        self.assertEqual(task.status, "Todo")
        self.assertEqual(Notification.objects.filter(employee=self.cbda).count(), 1)

        activity.purpose = "Cập nhật thông tin"
        activity.save()
        self.assertEqual(Task.objects.filter(activity=activity).count(), 1)
        self.assertEqual(Notification.objects.filter(employee=self.cbda).count(), 1)

    def test_linking_dispatch_after_activity_creation_creates_task(self):
        activity = self.make_activity()
        self.assertFalse(Task.objects.filter(activity=activity).exists())

        activity.outgoing_document = self.dispatch
        activity.save()

        self.assertTrue(Task.objects.filter(activity=activity).exists())

    def test_activity_task_cannot_be_completed_without_report_file(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        task.status = "Done"

        with self.assertRaises(ValidationError):
            task.full_clean()

        task.report_file = SimpleUploadedFile("bao-cao.pdf", b"test report", content_type="application/pdf")
        task.full_clean()

    def test_reminders_are_sent_once_per_workday_and_skipped_on_weekends(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        task.due_date = date(2026, 9, 30)
        task.save()

        today = date.today()
        task.due_date = add_company_workdays(today, 1)
        task.save()

        first_run = send_activity_report_reminders(today=today)
        repeated_run = send_activity_report_reminders(today=today)
        weekend = today + timedelta(days=(5 - today.weekday()) % 7)
        weekend_run = send_activity_report_reminders(today=weekend)

        self.assertEqual(first_run, 1)
        self.assertEqual(repeated_run, 0)
        self.assertEqual(weekend_run, 0)
        self.assertEqual(
            Notification.objects.filter(
                employee=self.cbda, notification_type="ActivityReportReminder"
            ).count(),
            1,
        )


class ActivityDashboardPermissionTests(ActivityTestDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.other_cbda = self.make_employee("B")
        self.own_activity = self.make_activity("ACT-OWN")
        self.other_activity = self.make_activity("ACT-OTHER", lead=self.other_cbda)
        self.cbda_role, _ = Role.objects.get_or_create(
            role_code="CBDA", defaults={"role_name": "Cán bộ dự án"}
        )

    def create_user(self, username, employee, role):
        user = User.objects.create_user(username=username, password="test-password")
        user.employee = employee
        user.role = role
        user.save(update_fields=["employee", "role"])
        return user

    def test_cbda_sees_only_own_project_activities(self):
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.login(username="cbda_a", password="test-password")

        response = self.client.get(reverse("portal:activity_dashboard"), {"month": "2026-10"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_activity.activity_code)
        self.assertNotContains(response, self.other_activity.activity_code)

    def test_cbda_cannot_open_another_employees_activity_task(self):
        task = Task.objects.create(
            task_code="TASK-ACT-OTHER", task_name="Báo cáo riêng",
            assigned_by_employee=self.coordinator, assigned_to_employee=self.other_cbda,
            start_date=date(2026, 9, 25), due_date=date(2026, 10, 9),
            activity=self.other_activity,
        )
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.login(username="cbda_a", password="test-password")

        response = self.client.get(reverse("portal:task_detail", args=[task.pk]))

        self.assertEqual(response.status_code, 302)

    def test_task_requires_report_before_completion_and_accepts_report_upload(self):
        activity = self.make_activity("ACT-REPORT", dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.login(username="cbda_a", password="test-password")

        response = self.client.post(
            reverse("portal:task_detail", args=[task.pk]),
            {"action": "update_status", "status": "Done"},
        )
        task.refresh_from_db()
        self.assertEqual(task.status, "Todo")

        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root, M365_STORAGE_ENABLED=False
        ):
            response = self.client.post(
                reverse("portal:task_detail", args=[task.pk]),
                {
                    "action": "upload_activity_report",
                    "report_file": SimpleUploadedFile(
                        "bao-cao.pdf", b"test report", content_type="application/pdf"
                    ),
                },
            )
            task.refresh_from_db()
            self.assertTrue(task.report_file)

        self.client.post(
            reverse("portal:task_detail", args=[task.pk]),
            {"action": "update_status", "status": "Done"},
        )
        task.refresh_from_db()
        self.assertEqual(task.status, "Done")
