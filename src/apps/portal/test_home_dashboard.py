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
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from django.db import connection, IntegrityError, transaction
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from apps.contract.models import Contract, ContractType
from apps.leave.models import LeaveRequest, LeaveType
from apps.planning.models import HeadcountPlan
from apps.portal.dashboard_data import dashboard_snapshot, capacity_rows
from apps.portal.selectors import approvable_leave_requests


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
            if role_code == "DEPT_MANAGER":
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
                    main = html.split('class="home-dashboard"', 1)[1]
                    self.assertEqual('id="profile-warning-title"' in main, not linked)
                    self.assertEqual(bool(ctx.get("profile_setup")), not linked and has_permission(user, "manage_hr"))
                    actions = {a["href"] for a in ctx["home_actions"]}
                    self.assertEqual(reverse("portal:leave_create") in actions, linked)
                    self.assertEqual(reverse("portal:task_create") in actions, linked and has_permission(user, "assign_task"))
                    self.assertEqual(reverse("portal:dispatch_create") in actions, linked and has_permission(user, "manage_office"))
                    queue_links = {c["href"] for c in ctx["home_queue"]}
                    self.assertNotIn(reverse("portal:recruitment_list"), queue_links)  # Outside phase-one shared selectors.
                    if not has_permission(user, "approve_document"):
                        self.assertNotIn(reverse("portal:document_approval_list"), queue_links)
                    # Every new destination opens directly; a permission redirect is not success.
                    hrefs = actions | queue_links | {c["href"] for g in ctx["home_groups"] for c in g["cards"] if c["href"]}
                    if ctx.get("profile_setup"):
                        hrefs.add(ctx["profile_setup"]["href"])
                    for href in hrefs:
                        self.assertEqual(self.client.get(href).status_code, 200, (role, linked, href))
                    self.assertNotIn('ui-kpi--warning', main)
                    if any(card['value'] is None for group in ctx['home_groups'] for card in group['cards']):
                        self.assertContains(response, 'Chưa có dữ liệu')

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
        response = self.client.get(reverse("portal:dashboard"))
        self.assertContains(response, 'id="dashboard-headcount"')
        self.assertContains(response, 'Chưa nhập kế hoạch')
        self.assertContains(response, 'Xem bảng dữ liệu định biên')
        Employee.objects.update(employment_status="Resigned")
        empty = self.client.get(reverse("portal:dashboard"))
        self.assertEqual(empty.context["total_employees"], 0)
        self.assertEqual(empty.context["dashboard_snapshot"]["sections"]["headcount"]["rows"][0]["actual"], 0)


class PhaseOneSmokeTests(TestCase):
    user = HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        HomeDashboardTests.setUpTestData.__func__(cls)
    def test_phase_one_blocks_and_money_gate(self):
        user = self.user("HR_MANAGER")
        self.client.force_login(user)
        response = self.client.get(reverse("portal:dashboard"))
        self.assertContains(response, 'id="dashboard-status"')
        self.assertNotContains(response, 'id="dashboard-contracts"')  # R2 hides empty contract cards.
        self.assertContains(response, 'id="dashboard-headcount"')
        self.assertNotContains(response, 'id="dashboard-contract-types"')
        self.assertIn('contracts',response.context['dashboard_snapshot']['sections'])
        self.assertIn("dashboard_snapshot", response.context)
        self.assertNotIn("payroll", response.context["dashboard_snapshot"])

    def test_role_blocks_profiles_staff_superuser_and_no_hidden_queries(self):
        for role in ("EMPLOYEE", "DEPT_MANAGER", "HR_OFFICER", "HR_MANAGER", "DIRECTOR", "FINANCE_OFFICER", "SYS_ADMIN", "SUPER_ADMIN"):
            for linked in (False, True):
                with self.subTest(role=role, linked=linked):
                    user = self.user(role, linked)
                    # Cache role/employee before testing data-only query gates.
                    user.role; user.employee
                    with CaptureQueriesContext(connection) as captured:
                        snapshot = dashboard_snapshot(user, user.employee)
                    self.assertEqual("contracts" in snapshot["sections"], role in ("HR_MANAGER", "HR_OFFICER"))
                    self.assertEqual("headcount" in snapshot["sections"], role in ("HR_MANAGER", "DIRECTOR"))
                    keys = {item["key"] for item in snapshot["metrics"]}
                    self.assertEqual("approved" in keys, role in ("HR_MANAGER", "DIRECTOR"))
                    self.assertEqual("managed" in keys, role in ("HR_MANAGER", "HR_OFFICER", "DIRECTOR") or role == "DEPT_MANAGER" and linked)
                    sql = " ".join(q["sql"].lower() for q in captured)
                    self.assertNotIn("tblpayroll", sql)
                    self.assertNotIn("tblsalary", sql)
                    if not has_permission(user, "manage_hr"):
                        self.assertNotIn("tblcontract", sql)
                    if not has_permission(user, "view_reports"):
                        self.assertNotIn("tblheadcountplan", sql)
                    self.client.force_login(user)
                    response = self.client.get(reverse("portal:dashboard"))
                    self.assertEqual('id="dashboard-contracts"' in response.content.decode(), role in ("HR_MANAGER", "HR_OFFICER"))
                    self.assertEqual('id="dashboard-headcount"' in response.content.decode(), role in ("HR_MANAGER", "DIRECTOR"))
                    self.assertEqual('Nghỉ được duyệt trong ngày' in response.content.decode(), role in ("HR_MANAGER", "DIRECTOR"))
                    for value in ("gross_income", "basic_salary", "national_id", "allowance"):
                        self.assertNotIn(value, str(snapshot))
        for superuser, staff in ((True, False), (True, True), (False, True)):
            user = User.objects.create(username=f"gate-{superuser}-{staff}", is_superuser=superuser, is_staff=staff)
            result = dashboard_snapshot(user)
            self.assertEqual("contracts" in result["sections"], superuser)
            self.assertNotIn("payroll", result)

    def test_status_distinct_with_multiple_leaves_and_zero_states(self):
        manager = self.user("HR_MANAGER", True)
        employee = self.user("EMPLOYEE", True).employee
        for status in ("Probation", "OnLeave", "Resigned"):
            helper = self.user(status, True)
            Employee.objects.filter(pk=helper.employee_id).update(employment_status=status)
        lt = LeaveType.objects.create(leave_type_code="PH1", leave_type_name="Nghỉ giả")
        today = timezone.localdate()
        for status in ("Approved", "Approved", "Pending", "Rejected", "Cancelled"):
            LeaveRequest.objects.create(employee=employee, leave_type=lt, from_date=today, to_date=today, status=status)
        LeaveRequest.objects.create(employee=manager.employee, leave_type=lt, from_date=today-timedelta(days=2), to_date=today, status="Approved")
        result = dashboard_snapshot(manager, manager.employee)
        values = {m["key"]:m["value"] for m in result["metrics"]}
        self.assertEqual(values, dict(managed=4, active=2, approved=2, probation=1))
        # Exclude deleted parent records, even when leaves themselves are live.
        Employee.objects.filter(pk=employee.pk).update(is_deleted=True)
        self.assertEqual(dashboard_snapshot(manager, manager.employee)["sections"]["status"]["counts"]["approved"], 1)
        Employee.objects.all().update(employment_status="Resigned")
        self.assertEqual(dashboard_snapshot(manager)["metrics"][0]["value"], 0)
        # Approved is independent of current employee status, not attendance.
        self.assertEqual(dashboard_snapshot(manager)["sections"]["status"]["counts"]["approved"], 1)

    def test_contract_edges_multiple_effective_types_and_no_salary_fields(self):
        user = self.user("HR_OFFICER", True)
        today = timezone.localdate()
        kinds = [ContractType.objects.create(contract_type_code=f"K{i}",contract_type_name=f"Loại {i}") for i in range(2)]
        for i, days in enumerate((None, 0, 7, 8, 30, 31, 60, 61, -1)):
            Contract.objects.create(employee=user.employee, contract_type=kinds[i%2], contract_no=f"EDGE-{i}", start_date=today-timedelta(days=90), end_date=today+timedelta(days=days) if days is not None else None, status="Active", basic_salary=1234567)
        for i,status in enumerate(("Expired", "Terminated", "Draft")):
            Contract.objects.create(employee=user.employee, contract_type=kinds[0], contract_no=f"INACTIVE-{i}",start_date=today,end_date=today,status=status,basic_salary=0)
        Contract.objects.create(employee=user.employee,contract_type=kinds[0],contract_no="FUTURE",start_date=today+timedelta(days=1),end_date=today+timedelta(days=5),status="Active",basic_salary=0)
        section = dashboard_snapshot(user)["sections"]["contracts"]
        self.assertEqual(section["total"], 8)
        self.assertEqual(section["upcoming_count"], 6)
        self.assertEqual(section["overdue_count"], 1)
        self.assertEqual(len(section["upcoming_rows"]), 5)
        self.assertEqual([r["badge"] for r in section["upcoming_rows"]], ["today", "urgent", "soon", "soon", "later"])
        self.assertNotIn("basic_salary", str(section))
        self.assertIsNone(section["href"])
        self.client.force_login(user)
        html=self.client.get(reverse("portal:dashboard")).content.decode()
        self.assertIn('class="home-type-list dashboard-type-labels"',html)
        self.assertIn("Hết hạn hôm nay",html)
        self.assertIn("Quá hạn cần rà soát",html)
        kinds[1].delete()
        self.assertEqual(len(dashboard_snapshot(user)["sections"]["contracts"]["types"]), 1)
        self.assertNotIn('class="dashboard-donut"',self.client.get(reverse("portal:dashboard")).content.decode())

    def test_headcount_missing_zero_exceeding_duplicate_and_deleted_department(self):
        user=self.user("HR_MANAGER", True)
        today=timezone.localdate()
        missing=dashboard_snapshot(user)["sections"]["headcount"]
        self.assertEqual(missing["state"],"unconfigured")
        self.assertIsNone(missing["rows"][0]["ratio"])
        plan=HeadcountPlan.objects.create(year=today.year,department=self.department,planned_headcount=0)
        self.assertEqual(dashboard_snapshot(user)["sections"]["headcount"]["rows"][0]["note"],"Kế hoạch 0; không tính tỷ lệ")
        plan.planned_headcount=1;plan.save()
        self.user("EMPLOYEE",True)
        self.assertEqual(dashboard_snapshot(user)["sections"]["headcount"]["rows"][0]["ratio"],200)
        with self.assertRaises(IntegrityError), transaction.atomic():
            HeadcountPlan.objects.create(year=today.year,department=self.department,planned_headcount=2)
        duplicate=capacity_rows([dict(id=1,department_name="Giả",actual=3)], [SimpleNamespace(department_id=1,planned_headcount=10),SimpleNamespace(department_id=1,planned_headcount=20)])
        self.assertEqual(duplicate["state"],"partial")
        self.assertIsNone(duplicate["rows"][0]["planned"])
        null=capacity_rows([dict(id=None,department_name="Chưa xác định",actual=1)],[])
        self.assertEqual(null["rows"][0]["actual"],1)
        self.department.delete()
        self.assertEqual(dashboard_snapshot(user)["sections"]["headcount"]["rows"],[])
        self.assertEqual(dashboard_snapshot(user)["metrics"][0]["value"],0)

    def test_queue_same_selector_approval_regression_and_no_direct_approve(self):
        user=self.user("DEPT_MANAGER", True)
        other=self.user("EMPLOYEE", True)
        lt=LeaveType.objects.create(leave_type_code="QUEUE",leave_type_name="Nghỉ giả")
        today=timezone.localdate()
        leave=LeaveRequest.objects.create(employee=user.employee,leave_type=lt,from_date=today,to_date=today,status="Pending")
        LeaveRequest.objects.create(employee=other.employee,leave_type=lt,from_date=today,to_date=today,status="Approved")
        self.client.force_login(user)
        page=self.client.get(reverse("portal:leave_approval_list"))
        self.assertEqual(list(page.context["requests"].values_list("pk",flat=True)),list(approvable_leave_requests(user).values_list("pk",flat=True)))
        snapshot=dashboard_snapshot(user,user.employee)
        self.assertEqual(snapshot["sections"]["queue"]["rows"][0]["value"],1)
        html=self.client.get(reverse("portal:dashboard")).content.decode().split('class="home-dashboard"',1)[1]
        self.assertNotIn('method="post"',html)
        response=self.client.post(reverse("portal:leave_approve",args=[leave.pk]),{"decision":"Approved"})
        self.assertEqual(response.status_code,302)
        leave.refresh_from_db();self.assertEqual(leave.status,"Pending")
        # A deleted parent is a pre-existing selector gap: suppress only new queue.
        other.employee.delete()
        LeaveRequest.objects.create(employee=other.employee,leave_type=lt,from_date=today,to_date=today,status="Pending")
        self.assertEqual(dashboard_snapshot(user,user.employee)["sections"]["queue"]["state"],"ready")

    def test_service_has_no_writes_fixed_date_and_query_growth(self):
        user=self.user("HR_MANAGER",True)
        user.role;user.employee
        with CaptureQueriesContext(connection) as before:
            result=dashboard_snapshot(user,user.employee)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT","UPDATE","DELETE")) for q in before))
        for i in range(100):
            Department.objects.create(department_code=f"LOAD-{i}",department_name=f"Phòng giả {i}",organization=self.department.organization)
        # Bulk-create synthetic employees; no runtime database touched.
        employees=[]
        for i in range(1000):
            employees.append(Employee(employee_code=f"LOAD-E-{i}",first_name="Giả",last_name="Thử",full_name="Nhân viên giả",date_of_birth=date(1990,1,1),gender="Other",national_id=f"SYNTHETIC-{i}",company_email=f"load-{i}@example.test",mobile_phone="0900000000",join_date=date(2020,1,1),department=self.department,position=self.position,employment_status="Active"))
        Employee.objects.bulk_create(employees)
        with self.assertNumQueries(len(before)):
            dashboard_snapshot(user,user.employee)
        self.client.force_login(user);self.client.get(reverse("portal:dashboard"))
        with CaptureQueriesContext(connection) as queries:
            response=self.client.get(reverse("portal:dashboard"),{"as_of":"1990-01-01","year":"1990"})
        self.assertEqual(response.context["dashboard_snapshot"]["operational_date"],timezone.localdate())
        self.assertLessEqual(sum(q["sql"].lstrip().upper().startswith("SELECT") for q in queries),24)  # D2-8 approved ceiling.
        # Existing idle-session middleware writes only its authentication session.
        writes=[q["sql"] for q in queries if q["sql"].lstrip().upper().startswith(("INSERT","UPDATE","DELETE"))]
        self.assertTrue(all("django_session" in sql.lower() for sql in writes))

    def test_error_state_without_exposing_diagnostics(self):
        from django.db import DatabaseError
        user=self.user("HR_OFFICER")
        with patch("apps.portal.dashboard_data._contracts",side_effect=DatabaseError("secret SQL")):
            result=dashboard_snapshot(user)
        self.assertEqual(result["sections"]["contracts"]["state"],"error")
        self.assertNotIn("secret SQL",str(result))

    def test_inactive_manager_and_anonymous_do_not_query(self):
        from django.contrib.auth.models import AnonymousUser
        manager = self.user("DEPT_MANAGER", True)
        manager.is_active = False
        for user in (manager, AnonymousUser()):
            with self.assertNumQueries(0):
                result = dashboard_snapshot(user, getattr(user, "employee", None))
            self.assertEqual(result["metrics"], [])
            self.assertEqual(result["sections"], {})
        manager.is_active = True
        Employee.objects.filter(pk=manager.employee_id).update(is_deleted=True)
        manager.employee.is_deleted = True
        with self.assertNumQueries(0):
            result = dashboard_snapshot(manager, manager.employee)
        self.assertEqual(result["sections"], {})
