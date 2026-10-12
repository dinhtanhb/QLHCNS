"""Homepage regressions: role/profile boundaries, links and presentation counts."""
from datetime import date
from hashlib import sha256

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.portal.home_presentation import home_presentation
from apps.security.models import Role, User
from apps.security.permissions import PERMISSION_MATRIX, has_permission


class HomeDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="HOME", organization_name="Tổ chức giả")
        cls.department = Department.objects.create(department_code="HOME", department_name="Phòng giả", organization=org)
        cls.position = Position.objects.create(position_code="HOME", position_name="Chuyên viên giả")

    def user(self, role_code, linked=False):
        name = "home-" + role_code.lower() + ("-linked" if linked else "-unlinked")
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        employee = None
        if linked:
            employee = Employee.objects.create(employee_code=name, first_name="Dữ liệu", last_name="Giả",
                full_name="Nhân viên giả", date_of_birth=date(1990, 1, 1), gender="Other",
                national_id=sha256(name.encode()).hexdigest()[:20], company_email=name+"@example.test",
                mobile_phone="0900000000", join_date=date(2020, 1, 1), department=self.department,
                position=self.position, employment_status="Active")
            employee.managed_departments.add(self.department)
        return User.objects.create(username=name, role=role, employee=employee)

    def test_role_and_profile_matrix_and_action_targets(self):
        roles = sorted({r for values in PERMISSION_MATRIX.values() for r in values})
        for role in roles:
            for linked in (False, True):
                with self.subTest(role=role, linked=linked):
                    user = self.user(role, linked)
                    self.client.force_login(user)
                    response = self.client.get(reverse("portal:dashboard"))
                    self.assertEqual(response.status_code, 200)
                    ctx = response.context
                    self.assertEqual(bool(ctx.get("is_management_view")), role in ("HR_MANAGER", "DIRECTOR"))
                    self.assertEqual(bool(ctx.get("is_manager_view")), role == "DEPT_MANAGER" and linked)
                    self.assertEqual(bool(ctx.get("show_project_activity_summary")), has_permission(user, "view_activity_dashboard"))
                    html = response.content.decode()
                    main = html.split('class="ui-page home-dashboard"', 1)[1]
                    self.assertEqual('id="profile-warning-title"' in main, not linked)
                    self.assertEqual(bool(ctx.get("profile_setup")), not linked and has_permission(user, "manage_hr"))
                    actions = {a["href"] for a in ctx["home_actions"]}
                    self.assertEqual(reverse("portal:leave_create") in actions, linked)
                    self.assertEqual(reverse("portal:task_create") in actions, linked and has_permission(user, "assign_task"))
                    self.assertEqual(reverse("portal:dispatch_create") in actions, linked and has_permission(user, "manage_office"))
                    queue_links = {c["href"] for c in ctx["home_queue"]}
                    self.assertEqual(reverse("portal:recruitment_list") in queue_links, role == "HR_MANAGER")
                    if not has_permission(user, "approve_document"):
                        self.assertNotIn(reverse("portal:document_approval_list"), queue_links)
                    # Every new destination opens directly; a permission redirect is not success.
                    hrefs = actions | queue_links | {c["href"] for g in ctx["home_groups"] for c in g["cards"] if c["href"]}
                    if ctx.get("profile_setup"):
                        hrefs.add(ctx["profile_setup"]["href"])
                    for href in hrefs:
                        self.assertEqual(self.client.get(href).status_code, 200, (role, linked, href))
                    self.assertNotIn('ui-kpi--warning', main)
                    self.assertNotIn('Chưa có dữ liệu', main)

    def test_only_staff_superuser_gets_editable_profile_link(self):
        for staff in (False, True):
            user = User.objects.create(username="home-super-"+str(staff), is_superuser=True, is_staff=staff)
            self.client.force_login(user)
            response = self.client.get(reverse("portal:dashboard"))
            link = response.context["profile_setup"]
            expected = reverse("admin:security_user_change", args=[user.pk]) if staff else reverse("portal:hr_employee_create")
            self.assertEqual(link["href"], expected)
            self.assertEqual(self.client.get(link["href"]).status_code, 200)

    def test_presentation_reuses_counts_without_queries_and_preserves_scopes(self):
        user = self.user("DIRECTOR")
        context = dict(is_management_view=True, total_employees=7, pending_leave_approvals=2,
                       pending_recruitment=3, pending_documents=4, open_tasks_company=5, assets_in_use=6)
        with self.assertNumQueries(0):
            result = home_presentation(user, context)
        cards = result["home_groups"][0]["cards"]
        self.assertEqual([c["value"] for c in cards], [7, 2, 3, 4, 5, 6])
        self.assertIsNone(cards[2]["href"])  # Director cannot open recruitment approval scope.
        self.assertIsNone(cards[4]["href"])  # No existing whole-centre task list.
        self.assertEqual(len(result["home_queue"]), 2)

    def test_kpi_zero_missing_positive_and_escape(self):
        zero = render_to_string("ui/kpi.html", {"label": "Chờ duyệt", "value": 0, "warning": True})
        self.assertIn('>0</strong>', zero)
        self.assertNotIn("Cần xử lý", zero)
        missing = render_to_string("ui/kpi.html", {"label": "Chờ duyệt", "value": None})
        self.assertIn("Chưa có dữ liệu", missing)
        positive = render_to_string("ui/kpi.html", {"label": "<script>", "value": 1234, "warning": True, "href": "/portal/leave/"})
        self.assertIn('ui-kpi--warning', positive)
        self.assertIn('Cần xử lý', positive)
        self.assertIn('1.234', positive)
        self.assertIn('&lt;script&gt;', positive)

    def test_department_summary_table_and_empty_states(self):
        user = self.user("HR_MANAGER", linked=True)
        self.client.force_login(user)
        one = self.client.get(reverse("portal:dashboard"))
        self.assertContains(one, 'home-dept-summary')
        self.assertNotContains(one, 'home-bar-track')
        other = Department.objects.create(department_code="HOME2", department_name="Phòng thứ hai", organization=self.department.organization)
        self.user("EMPLOYEE", linked=True).employee.__class__.objects.filter(employee_code="home-employee-linked").update(department=other)
        multiple = self.client.get(reverse("portal:dashboard"))
        self.assertContains(multiple, 'home-bar-track')
        self.assertContains(multiple, 'Xem bảng dữ liệu nhân sự')
        self.assertEqual([d['total'] for d in multiple.context['dept_counts']], sorted([d['total'] for d in multiple.context['dept_counts']], reverse=True))
        Employee.objects.update(employment_status="Inactive")
        empty = self.client.get(reverse("portal:dashboard"))
        self.assertContains(empty, 'Chưa có nhân viên đang làm việc để thống kê.')
