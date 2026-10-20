"""Regression tests for recruitment separation and salary-scale visibility."""

import re
from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User


class RecruitmentAccountingNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            organization_code="NAV-20261008",
            organization_name="Navigation test",
        )
        cls.department = Department.objects.create(
            organization=cls.organization,
            department_code="NAV-20261008",
            department_name="Phòng kiểm thử điều hướng",
        )
        cls.position = Position.objects.create(
            position_code="NAV-20261008",
            position_name="Vị trí kiểm thử điều hướng",
        )

    def make_user(self, role_code, suffix):
        employee = Employee.objects.create(
            employee_code=f"NAV-{suffix}",
            first_name="Kiểm thử",
            last_name=suffix,
            full_name=f"Nhân viên {suffix}",
            date_of_birth=date(1990, 1, 1),
            gender="Other",
            national_id=f"NAV-ID-{suffix}"[:20],
            company_email=f"nav-{suffix.lower()}@example.test",
            mobile_phone="0900000000",
            join_date=date(2020, 1, 1),
            department=self.department,
            position=self.position,
            employment_status="Active",
        )
        role, _ = Role.objects.get_or_create(
            role_code=role_code,
            defaults={"role_name": role_code},
        )
        return User.objects.create_user(
            username=f"nav-{suffix.lower()}",
            password="test-password",
            employee=employee,
            role=role,
        )

    def test_recruitment_has_own_menu_process_and_forms(self):
        user = self.make_user("HR_MANAGER", "HRM")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:dashboard"))
        html = response.content.decode()

        self.assertContains(response, 'aria-controls="menu-tuyendung"')
        self.assertContains(response, reverse("portal:recruitment_hub"))
        self.assertContains(response, reverse("portal:recruitment_list"))
        self.assertContains(response, reverse("portal:hr_candidate_list"))
        self.assertContains(
            response,
            reverse("portal:hcns_catalog") + "?group=recruitment",
        )
        hr_menu = re.search(
            r'id="menu-nhansu".*?</div>\s*</div>', html, re.DOTALL
        ).group(0)
        self.assertNotIn("Đề xuất tuyển dụng", hr_menu)
        self.assertNotIn("Ứng viên", hr_menu)

    def test_recruitment_hub_respects_existing_role_permissions(self):
        allowed = ("HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER")
        denied = ("DIRECTOR", "FINANCE_OFFICER", "EMPLOYEE")

        for index, role_code in enumerate(allowed, start=1):
            with self.subTest(role=role_code):
                self.client.force_login(self.make_user(role_code, f"RA{index}"))
                response = self.client.get(reverse("portal:recruitment_hub"))
                self.assertEqual(response.status_code, 200)
                self.client.logout()

        for index, role_code in enumerate(denied, start=1):
            with self.subTest(role=role_code):
                self.client.force_login(self.make_user(role_code, f"RD{index}"))
                response = self.client.get(reverse("portal:recruitment_hub"))
                self.assertEqual(response.status_code, 403)
                self.client.logout()

    def test_salary_scale_is_only_available_to_finance_and_director_roles(self):
        allowed = ("FINANCE_OFFICER", "DIRECTOR")
        denied = (
            "HR_MANAGER",
            "HR_OFFICER",
            "SYS_ADMIN",
            "DEPT_MANAGER",
            "EMPLOYEE",
        )
        salary_url = reverse("portal:hcns_draft", args=("salary-scale",))

        for index, role_code in enumerate(allowed, start=1):
            with self.subTest(role=role_code):
                self.client.force_login(self.make_user(role_code, f"SA{index}"))
                self.assertEqual(self.client.get(salary_url).status_code, 200)
                dashboard = self.client.get(reverse("portal:dashboard"))
                self.assertContains(dashboard, 'aria-controls="menu-ketoan"')
                self.assertContains(dashboard, salary_url)
                catalog = self.client.get(
                    reverse("portal:hcns_catalog"), {"group": "salary"}
                )
                self.assertContains(catalog, "Thang bảng lương")
                self.client.logout()

        for index, role_code in enumerate(denied, start=1):
            with self.subTest(role=role_code):
                self.client.force_login(self.make_user(role_code, f"SD{index}"))
                self.assertEqual(self.client.get(salary_url).status_code, 403)
                dashboard = self.client.get(reverse("portal:dashboard"))
                self.assertNotContains(dashboard, salary_url)
                catalog = self.client.get(
                    reverse("portal:hcns_catalog"), {"group": "salary"}
                )
                self.assertNotContains(catalog, "Thang bảng lương")
                self.client.logout()

    def test_hr_menu_contains_decisions_and_role_scoped_approvals(self):
        expected = {
            "HR_MANAGER": ("Nhân viên &amp; hồ sơ", "Quyết định nhân sự", "Duyệt cập nhật hồ sơ", "Duyệt nghỉ phép", "Duyệt chấm công", "Duyệt tài liệu"),
            "HR_OFFICER": ("Nhân viên &amp; hồ sơ", "Quyết định nhân sự", "Duyệt cập nhật hồ sơ"),
            "DIRECTOR": ("Quyết định nhân sự", "Duyệt nghỉ phép", "Duyệt chấm công", "Duyệt tài liệu"),
            "DEPT_MANAGER": ("Duyệt nghỉ phép", "Duyệt chấm công"),
        }
        for index, (role_code, labels) in enumerate(expected.items(), start=1):
            with self.subTest(role=role_code):
                self.client.force_login(self.make_user(role_code, f"HRNAV{index}"))
                response = self.client.get(reverse("portal:dashboard"))
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertNotIn('aria-controls="menu-duyet"', html)
                menu = re.search(r'id="menu-nhansu".*?</div>', html, re.DOTALL)
                self.assertIsNotNone(menu)
                for label in labels:
                    self.assertIn(label, menu.group(0))
                self.assertNotIn("Duyệt đề xuất hoạt động", menu.group(0))
                project_menu = re.search(r'id="menu-hoatdongduan".*?</div>', html, re.DOTALL)
                if role_code == "DIRECTOR":
                    self.assertIsNotNone(project_menu)
                    self.assertIn("Duyệt đề xuất hoạt động", project_menu.group(0))
                elif project_menu:
                    self.assertNotIn("Duyệt đề xuất hoạt động", project_menu.group(0))
                decision_links = re.findall(
                    r'<a\b[^>]*href="' + re.escape(reverse("portal:personnel_decision_list")) + r'"[^>]*>',
                    html,
                )
                self.assertEqual(len(decision_links), 1)
                if role_code in ("DIRECTOR", "DEPT_MANAGER"):
                    self.assertNotIn("Nhân viên &amp; hồ sơ", menu.group(0))
                self.client.logout()

        self.client.force_login(self.make_user("EMPLOYEE", "HRNAV5"))
        response = self.client.get(reverse("portal:dashboard"))
        self.assertContains(response, 'aria-controls="menu-nhansu"')
        self.assertNotContains(response, 'aria-controls="menu-duyet"')
