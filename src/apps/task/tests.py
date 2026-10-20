from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.activity.models import Activity
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.project.models import Project
from apps.task.models import Task


class TaskModelTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="TSK-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="TSK-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="TSK-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="TSK-EMP", first_name="An", last_name="Kiểm thử", full_name="TSK-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="TSK-EMP",
            company_email="tsk-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )
        project = Project.objects.create(project_code="TSK-PRJ", project_name="Dự án kiểm thử")
        cls.activity = Activity.objects.create(
            activity_code="TSK-ACT", activity_name="Hoạt động kiểm thử", project=project,
            start_date=date(2026, 9, 1), end_date=date(2026, 10, 31), lead_cbda=cls.employee,
        )

    def make_task(self, **kwargs):
        values = {
            "task_code": "TSK-REPORT-1", "task_name": "Nộp báo cáo",
            "assigned_by_employee": self.employee, "assigned_to_employee": self.employee,
            "department": self.department, "activity": self.activity,
            "status": "Done", "start_date": date(2026, 10, 1), "due_date": date(2026, 11, 13),
        }
        values.update(kwargs)
        return Task(**values)


class TaskModelValidationTests(TaskModelTestBase):
    def test_activity_report_task_cannot_be_completed_without_report_file(self):
        task = self.make_task()
        with self.assertRaises(ValidationError) as error:
            task.full_clean()
        self.assertIn("report_file", error.exception.message_dict)

    def test_activity_report_task_cannot_be_completed_before_activity_ends(self):
        task = self.make_task(report_file=SimpleUploadedFile("report.pdf", b"%PDF-test"))
        with patch("apps.task.models.timezone.localdate", return_value=date(2026, 9, 27)):
            with self.assertRaises(ValidationError) as error:
                task.full_clean()
        self.assertIn("status", error.exception.message_dict)

    def test_activity_report_file_rejects_executable_upload(self):
        field = Task._meta.get_field("report_file")
        with self.assertRaises(ValidationError):
            field.validators[0](SimpleUploadedFile("virus.exe", b"not executable"))

    def test_task_code_is_unique(self):
        task = self.make_task(status="Todo")
        task.save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_task(status="Todo").save()


from apps.security.models import Role, User
from apps.task.admin import TaskAdmin
from apps.task.permissions import visible_tasks_for
from django.contrib.admin.sites import AdminSite


class MockRequest:
    def __init__(self, user):
        self.user = user
        self.GET = {}


class TaskAdminScopeTests(TaskModelTestBase):
    def test_project_manager_staff_cannot_view_or_edit_unrelated_hr_task(self):
        hr_role, _ = Role.objects.get_or_create(role_code="HR_MANAGER", defaults={"role_name": "HR"})
        pm_role, _ = Role.objects.get_or_create(role_code="PROJECT_MANAGER", defaults={"role_name": "PM"})

        hr_employee = Employee.objects.create(
            employee_code="TSK-HR-EMP", first_name="HR", last_name="Specialist", full_name="TSK-HR-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="TSK-HR-EMP",
            company_email="tsk-hr@example.test", mobile_phone="0900000001",
            join_date=date(2020, 1, 1), department=self.department, position=self.position,
        )
        pm_employee = Employee.objects.create(
            employee_code="TSK-PM-EMP", first_name="PM", last_name="Leader", full_name="TSK-PM-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="TSK-PM-EMP",
            company_email="tsk-pm@example.test", mobile_phone="0900000002",
            join_date=date(2020, 1, 1), department=self.department, position=self.position,
        )

        pm_user = User.objects.create_user(
            username="pm-staff-user", password="password", employee=pm_employee, role=pm_role,
            is_staff=True,
        )

        hr_task = Task.objects.create(
            task_code="TSK-HR-CONFIDENTIAL",
            task_name="Đánh giá kỷ luật phòng HR",
            description="Thông tin bảo mật nội bộ HR",
            assigned_by_employee=hr_employee,
            assigned_to_employee=hr_employee,
            department=self.department,
            status="Todo",
            activity=None,
        )

        act_task = Task.objects.create(
            task_code="TSK-ACT-VISIBLE",
            task_name="Báo cáo tiến độ hoạt động",
            assigned_by_employee=pm_employee,
            assigned_to_employee=self.employee,
            department=self.department,
            status="Todo",
            activity=self.activity,
        )

        visible = visible_tasks_for(pm_user)
        self.assertIn(act_task, visible)
        self.assertNotIn(hr_task, visible)

        admin = TaskAdmin(Task, AdminSite())
        request = MockRequest(pm_user)
        qs = admin.get_queryset(request)
        self.assertIn(act_task, qs)
        self.assertNotIn(hr_task, qs)

        self.assertTrue(admin.has_view_permission(request, act_task))
        self.assertFalse(admin.has_view_permission(request, hr_task))
        self.assertFalse(admin.has_change_permission(request, hr_task))
