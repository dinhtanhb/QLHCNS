"""Phương án B: cột phải bảng điều khiển (lịch hôm nay, dự án đang chạy) và dải số liệu thứ hai."""
from datetime import date, datetime, time, timedelta
from hashlib import sha256

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.planning.models import Event
from apps.project.models import Project
from apps.portal.dashboard_data import RAIL_LIMIT, dashboard_snapshot
from apps.security.models import Role, User


class DashboardRailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="RAIL", organization_name="Tổ chức giả")
        cls.department = Department.objects.create(
            department_code="RAIL", department_name="Phòng giả", organization=org)
        cls.other_department = Department.objects.create(
            department_code="RAIL-OTHER", department_name="Phòng khác", organization=org)
        cls.position = Position.objects.create(position_code="RAIL", position_name="Chuyên viên giả")

    def setUp(self):
        self.today = timezone.localdate()
        self.zone = timezone.get_current_timezone()

    def make_user(self, role_code, *, linked=True, department=None):
        name = "rail-" + role_code.lower() + ("-linked" if linked else "-unlinked")
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        employee = None
        if linked:
            employee = Employee.objects.create(
                employee_code=name, first_name="Dữ liệu", last_name="Giả", full_name="Nhân viên giả",
                date_of_birth=date(1990, 1, 1), gender="Other",
                national_id=sha256(name.encode()).hexdigest()[:20], company_email=name + "@example.test",
                mobile_phone="0900000000", join_date=date(2020, 1, 1),
                department=department or self.department, position=self.position,
                employment_status="Active")
        return User.objects.create(username=name, role=role, employee=employee)

    def make_event(self, title, at, department=None, day_offset=0):
        start = timezone.make_aware(datetime.combine(self.today + timedelta(days=day_offset), at), self.zone)
        return Event.objects.create(
            title=title, event_type="Meeting", department=department,
            start_time=start, end_time=start + timedelta(hours=1), location="Phòng giả")

    def agenda(self, user):
        return dashboard_snapshot(user, getattr(user, "employee", None))["sections"]["agenda"]

    def test_agenda_shows_company_and_own_department_only(self):
        self.make_event("Họp toàn Trung tâm", time(8, 30))
        self.make_event("Họp phòng mình", time(10, 0), department=self.department)
        self.make_event("Họp phòng khác", time(14, 0), department=self.other_department)

        linked = self.agenda(self.make_user("EMPLOYEE"))
        self.assertEqual([row["title"] for row in linked["rows"]], ["Họp toàn Trung tâm", "Họp phòng mình"])

        # Tài khoản chưa gắn hồ sơ chỉ thấy sự kiện toàn Trung tâm.
        unlinked = self.agenda(self.make_user("HR_MANAGER", linked=False))
        self.assertEqual([row["title"] for row in unlinked["rows"]], ["Họp toàn Trung tâm"])

    def test_agenda_ignores_other_days_and_flags_truncation(self):
        self.make_event("Hôm qua", time(9, 0), day_offset=-1)
        self.make_event("Mai", time(9, 0), day_offset=1)
        for index in range(RAIL_LIMIT + 2):
            self.make_event(f"Hôm nay {index}", time(8 + index, 0))
        block = self.agenda(self.make_user("EMPLOYEE"))
        self.assertEqual(len(block["rows"]), RAIL_LIMIT)
        self.assertTrue(block["more"])
        self.assertTrue(all(row["title"].startswith("Hôm nay") for row in block["rows"]))

    def test_agenda_empty_state_is_still_rendered(self):
        block = self.agenda(self.make_user("EMPLOYEE"))
        self.assertEqual(block["state"], "empty")
        self.assertEqual(block["rows"], [])
        self.assertFalse(block["more"])

    def test_running_projects_requires_activity_permission(self):
        Project.objects.create(project_code="RAIL-P1", project_name="Dự án đang chạy",
                               start_date=self.today - timedelta(days=10))
        director = self.make_user("DIRECTOR")
        self.assertIn("running_projects", dashboard_snapshot(director, director.employee)["sections"])
        employee = self.make_user("EMPLOYEE")
        self.assertNotIn("running_projects", dashboard_snapshot(employee, employee.employee)["sections"])

    def test_running_projects_excludes_closed_and_finished(self):
        Project.objects.create(project_code="RAIL-OPEN", project_name="Còn chạy",
                               start_date=self.today - timedelta(days=5))
        Project.objects.create(project_code="RAIL-DONE", project_name="Đã xong",
                               start_date=self.today - timedelta(days=30),
                               end_date=self.today - timedelta(days=1))
        Project.objects.create(project_code="RAIL-OFF", project_name="Tạm dừng", is_active=False)
        Project.objects.create(project_code="RAIL-LATER", project_name="Chưa bắt đầu",
                               start_date=self.today + timedelta(days=5))
        director = self.make_user("DIRECTOR")
        rows = dashboard_snapshot(director, director.employee)["sections"]["running_projects"]["rows"]
        self.assertEqual([row["project_code"] for row in rows], ["RAIL-OPEN"])

    def test_dashboard_renders_rail_and_secondary_band(self):
        self.make_event("Họp giao ban", time(8, 30))
        user = self.make_user("HR_MANAGER")
        self.client.force_login(user)
        html = self.client.get(reverse("portal:dashboard")).content.decode()
        self.assertIn('id="dashboard-agenda"', html)
        self.assertIn("Họp giao ban", html)
        # Cột phải và luồng nội dung là hai cột của cùng một lưới.
        self.assertIn('class="home-dashboard-body"', html)
        self.assertIn('class="home-dashboard-stream"', html)

    def test_secondary_band_does_not_repeat_kpi_labels(self):
        user = self.make_user("HR_MANAGER")
        self.client.force_login(user)
        response = self.client.get(reverse("portal:dashboard"))
        layout = response.context["dashboard_layout"]
        kpi_labels = {item["label"] for item in layout["main"]}
        secondary_labels = [item["label"] for item in layout["secondary"]]
        self.assertEqual(len(secondary_labels), len(set(secondary_labels)))
        self.assertFalse(kpi_labels & set(secondary_labels))
        # Dải chỉ hiện khi có ít nhất hai chỉ số, tránh một dải một ô.
        html = response.content.decode()
        self.assertEqual('id="dashboard-secondary"' in html, len(secondary_labels) >= 2)
