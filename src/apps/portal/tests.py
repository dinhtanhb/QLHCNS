from datetime import date
from decimal import Decimal
from hashlib import sha256
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.activity.models import Activity
from apps.asset.models import (
    Asset, AssetDisposalRequest, AssetType, InventoryLine, InventoryMember, InventorySession,
)
from apps.hrm.models import Employee
from apps.leave.models import LeaveApproval, LeaveRequest, LeaveType
from apps.organization.models import Department, Organization, Position
from apps.payroll.models import Payroll, PayrollPeriod, Payslip
from apps.payroll.models import EmployeeSalary
from apps.project.models import Project
from apps.security.models import Role, User
from apps.task.models import Task


class PortalSensitiveWorkflowTests(TestCase):
    """Regression checks for approval boundaries and confidential payslips."""

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            organization_code="PORTAL-TEST", organization_name="Tổ chức kiểm thử portal"
        )
        cls.department = Department.objects.create(
            department_code="PORTAL-TEST", department_name="Phòng kiểm thử",
            organization=cls.organization,
        )
        cls.employee_position = Position.objects.create(
            position_code="PORTAL-STAFF", position_name="Chuyên viên"
        )
        cls.director_position = Position.objects.create(
            position_code="PORTAL-DIRECTOR", position_name="Giám đốc"
        )

    def make_employee(self, code, position=None):
        return Employee.objects.create(
            employee_code=code,
            first_name="Nguyễn",
            last_name="Kiểm thử",
            full_name=f"Nhân viên {code}",
            date_of_birth=date(1990, 1, 1),
            gender="Other",
            national_id=sha256(code.encode("utf-8")).hexdigest()[:20],
            company_email=f"{code.lower()}@example.test",
            mobile_phone="0900000000",
            join_date=date(2020, 1, 1),
            department=self.department,
            position=position or self.employee_position,
            employment_status="Active",
        )

    def make_user(self, role_code, employee, username):
        role, _ = Role.objects.get_or_create(
            role_code=role_code, defaults={"role_name": role_code}
        )
        return User.objects.create_user(
            username=username, password="test-password", employee=employee, role=role
        )

    def make_leave_request(self, employee, suffix):
        leave_type, _ = LeaveType.objects.get_or_create(
            leave_type_code="PORTAL-ANNUAL",
            defaults={"leave_type_name": "Nghỉ kiểm thử", "is_paid": True},
        )
        return LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            from_date=date(2026, 11, 2),
            to_date=date(2026, 11, 2),
            reason=f"Kiểm thử {suffix}",
        )

    def test_department_manager_cannot_approve_own_leave_request(self):
        employee = self.make_employee("PORTAL-MGR")
        self.department.manager = employee
        self.department.save(update_fields=("manager",))
        user = self.make_user("DEPT_MANAGER", employee, "portal-dept-manager")
        leave_request = self.make_leave_request(employee, "self-approval")
        self.client.force_login(user)

        response = self.client.post(
            reverse("portal:leave_approve", args=(leave_request.pk,)),
            {"decision": "Approved"},
        )

        leave_request.refresh_from_db()
        self.assertRedirects(response, reverse("portal:leave_approval_list"))
        self.assertEqual(leave_request.status, "Pending")
        self.assertFalse(LeaveApproval.objects.filter(leave_request=leave_request).exists())

    def test_hr_manager_can_approve_own_leave_under_current_exception_rule(self):
        employee = self.make_employee("PORTAL-HR-MGR")
        user = self.make_user("HR_MANAGER", employee, "portal-hr-manager")
        leave_request = self.make_leave_request(employee, "hr-manager")
        self.client.force_login(user)

        response = self.client.post(
            reverse("portal:leave_approve", args=(leave_request.pk,)),
            {"decision": "Approved"},
        )

        leave_request.refresh_from_db()
        self.assertRedirects(response, reverse("portal:leave_approval_list"))
        self.assertEqual(leave_request.status, "Approved")
        self.assertTrue(LeaveApproval.objects.filter(
            leave_request=leave_request, approver=employee, decision="Approved"
        ).exists())

    def test_locked_payroll_period_is_not_recalculated(self):
        employee = self.make_employee("PORTAL-FINANCE-EMP")
        finance_user = self.make_user("FINANCE_OFFICER", employee, "portal-finance")
        period = PayrollPeriod.objects.create(
            payroll_month=10, payroll_year=2026,
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 31), status="Locked",
        )
        payroll = Payroll.objects.create(
            payroll_period=period, employee=employee, basic_salary=Decimal("12345678")
        )
        self.client.force_login(finance_user)

        with patch.object(Payroll, "calculate") as calculate:
            response = self.client.post(
                reverse("portal:finance_payroll_calculate_all", args=(period.pk,))
            )

        payroll.refresh_from_db()
        self.assertRedirects(response, reverse("portal:finance_payroll_run", args=(period.pk,)))
        calculate.assert_not_called()
        self.assertEqual(payroll.basic_salary, Decimal("12345678"))

    def test_hr_officer_cannot_approve_asset_disposal_by_direct_post(self):
        employee = self.make_employee("PORTAL-HR-OFFICER")
        hr_user = self.make_user("HR_OFFICER", employee, "portal-hr-officer")
        disposal = AssetDisposalRequest.objects.create(
            request_no="PORTAL-DISPOSAL-TEST",
            request_date=date(2026, 9, 25),
            location_name="Văn phòng kiểm thử",
            requested_by=employee,
        )
        self.client.force_login(hr_user)

        response = self.client.post(
            reverse("portal:disposal_request_detail", args=(disposal.pk,)),
            {"action": "approve"},
        )

        disposal.refresh_from_db()
        self.assertRedirects(response, reverse("portal:disposal_request_detail", args=(disposal.pk,)))
        self.assertEqual(disposal.status, "Pending")

    def test_employee_sees_only_issued_payslips_from_locked_periods(self):
        employee = self.make_employee("PORTAL-PAYSLIP-EMP")
        user = self.make_user("EMPLOYEE", employee, "portal-payslip-employee")
        locked_period = PayrollPeriod.objects.create(
            payroll_month=8, payroll_year=2026,
            start_date=date(2026, 8, 1), end_date=date(2026, 8, 31), status="Locked",
        )
        open_period = PayrollPeriod.objects.create(
            payroll_month=9, payroll_year=2026,
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 30), status="Open",
        )
        locked_payroll = Payroll.objects.create(payroll_period=locked_period, employee=employee)
        open_payroll = Payroll.objects.create(payroll_period=open_period, employee=employee)
        locked_payslip = Payslip.objects.create(payroll=locked_payroll)
        open_payslip = Payslip.objects.create(payroll=open_payroll)
        self.client.force_login(user)

        response = self.client.get(reverse("portal:payslip_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "08/2026")
        self.assertNotContains(response, "09/2026")
        self.assertEqual(list(response.context["payrolls"]), [locked_payroll])
        open_pdf = self.client.get(reverse("portal:payslip_pdf", args=(open_payslip.pk,)))
        self.assertEqual(open_pdf.status_code, 404)
        self.assertNotEqual(locked_payslip.pk, open_payslip.pk)

        dashboard = self.client.get(reverse("portal:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertNotContains(dashboard, "Lương kỳ gần nhất")
        self.assertNotIn("latest_payroll", dashboard.context)
        self.assertContains(dashboard, f'href="{reverse("portal:payslip_list")}"')

    def test_locking_payroll_issues_payslips_for_period_payrolls(self):
        employee = self.make_employee("PORTAL-PAYSLIP-ISSUE")
        finance_user = self.make_user("FINANCE_OFFICER", employee, "portal-payslip-issuer")
        period = PayrollPeriod.objects.create(
            payroll_month=10, payroll_year=2026,
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 31), status="Open",
        )
        payroll = Payroll.objects.create(
            payroll_period=period, employee=employee, basic_salary=Decimal("12345678")
        )
        self.client.force_login(finance_user)

        from apps.payroll.test_fixtures import create_calculation_rates
        create_calculation_rates()
        payroll.calculate()
        payroll.save()

        # Suppress notifications in this test; only verify the transactional payslip issuance.
        with patch("apps.portal.views.finance.notify"), patch("apps.portal.views.finance.notify_with_email_draft"):
            response = self.client.post(reverse("portal:finance_payroll_lock", args=(period.pk,)))

        period.refresh_from_db()
        self.assertRedirects(response, reverse("portal:finance_period_list"))
        self.assertEqual(period.status, "Locked")
        self.assertTrue(Payslip.objects.filter(payroll=payroll).exists())
        self.assertContains(self.client.get(reverse("portal:payslip_list")), "10/2026")

    def test_payroll_generation_includes_employee_leaving_during_the_period(self):
        """I6: người nghỉ giữa kỳ vẫn cần có dòng lương để chốt phần thời gian đã làm."""
        leaver = self.make_employee("PORTAL-PAYROLL-LEAVER")
        leaver.join_date = date(2020, 1, 1)
        leaver.leave_date = date(2025, 10, 15)
        leaver.employment_status = "Resigned"
        leaver.save(update_fields=("join_date", "leave_date", "employment_status"))
        finance_user = self.make_user("FINANCE_OFFICER", self.make_employee("PORTAL-PAYROLL-FINANCE"), "portal-payroll-finance-i6")
        period = PayrollPeriod.objects.create(
            payroll_month=10, payroll_year=2025,
            start_date=date(2025, 10, 1), end_date=date(2025, 10, 31), status="Open",
        )
        EmployeeSalary.objects.create(
            employee=leaver, current_basic_salary=Decimal("20000000"),
            effective_date=date(2020, 1, 1), end_date=date(2025, 10, 15), status="Ended",
        )
        self.client.force_login(finance_user)

        preview = self.client.get(reverse("portal:finance_payroll_run", args=(period.pk,)))
        missing_ids = set(preview.context["missing_employees"].values_list("pk", flat=True))
        self.assertIn(leaver.pk, missing_ids)

        self.client.post(reverse("portal:finance_payroll_generate", args=(period.pk,)))

        self.assertTrue(
            Payroll.objects.filter(payroll_period=period, employee=leaver).exists(),
            "Nhân viên có ngày nghỉ việc trong kỳ không được bỏ khỏi kỳ lương giữa tháng.",
        )
        completed_preview = self.client.get(reverse("portal:finance_payroll_run", args=(period.pk,)))
        completed_missing_ids = set(
            completed_preview.context["missing_employees"].values_list("pk", flat=True)
        )
        self.assertNotIn(leaver.pk, completed_missing_ids)
        self.client.post(reverse("portal:finance_payroll_generate", args=(period.pk,)))
        self.assertEqual(Payroll.objects.filter(payroll_period=period, employee=leaver).count(), 1)

    def test_payroll_generation_includes_employees_leaving_on_period_boundaries(self):
        period = PayrollPeriod.objects.create(
            payroll_month=10, payroll_year=2025,
            start_date=date(2025, 10, 1), end_date=date(2025, 10, 31), status="Open",
        )
        first_day_leaver = self.make_employee("PORTAL-PAYROLL-LEAVE-START")
        last_day_leaver = self.make_employee("PORTAL-PAYROLL-LEAVE-END")
        for employee, leave_date in (
            (first_day_leaver, period.start_date),
            (last_day_leaver, period.end_date),
        ):
            employee.leave_date = leave_date
            employee.employment_status = "Resigned"
            employee.save(update_fields=("leave_date", "employment_status"))
            EmployeeSalary.objects.create(
                employee=employee,
                current_basic_salary=Decimal("10000000"),
                effective_date=date(2025, 1, 1),
                end_date=leave_date,
                status="Ended",
            )

        finance_user = self.make_user(
            "FINANCE_OFFICER", self.make_employee("PORTAL-PAYROLL-FINANCE-BOUNDARY"),
            "portal-payroll-finance-boundary",
        )
        self.client.force_login(finance_user)

        self.client.post(reverse("portal:finance_payroll_generate", args=(period.pk,)))

        for employee in (first_day_leaver, last_day_leaver):
            with self.subTest(leave_date=employee.leave_date):
                self.assertTrue(Payroll.objects.filter(payroll_period=period, employee=employee).exists())

    def test_payroll_generation_excludes_employee_who_left_before_period(self):
        period = PayrollPeriod.objects.create(
            payroll_month=10, payroll_year=2025,
            start_date=date(2025, 10, 1), end_date=date(2025, 10, 31), status="Open",
        )
        former_employee = self.make_employee("PORTAL-PAYROLL-LEFT-BEFORE")
        former_employee.leave_date = date(2025, 9, 30)
        former_employee.employment_status = "Resigned"
        former_employee.save(update_fields=("leave_date", "employment_status"))
        finance_user = self.make_user(
            "FINANCE_OFFICER", self.make_employee("PORTAL-PAYROLL-FINANCE-PRIOR"),
            "portal-payroll-finance-prior",
        )
        self.client.force_login(finance_user)

        preview = self.client.get(reverse("portal:finance_payroll_run", args=(period.pk,)))
        missing_ids = set(preview.context["missing_employees"].values_list("pk", flat=True))
        self.assertNotIn(former_employee.pk, missing_ids)

        self.client.post(reverse("portal:finance_payroll_generate", args=(period.pk,)))

        self.assertFalse(Payroll.objects.filter(payroll_period=period, employee=former_employee).exists())

    def test_payroll_generation_keeps_active_employee_with_future_leave_date(self):
        period = PayrollPeriod.objects.create(
            payroll_month=10, payroll_year=2025,
            start_date=date(2025, 10, 1), end_date=date(2025, 10, 31), status="Open",
        )
        active_employee = self.make_employee("PORTAL-PAYROLL-FUTURE-LEAVE")
        active_employee.leave_date = date(2025, 11, 15)
        active_employee.save(update_fields=("leave_date",))
        EmployeeSalary.objects.create(
            employee=active_employee,
            current_basic_salary=Decimal("10000000"),
            effective_date=date(2025, 1, 1),
            status="Active",
        )
        finance_user = self.make_user(
            "FINANCE_OFFICER", self.make_employee("PORTAL-PAYROLL-FINANCE-FUTURE"),
            "portal-payroll-finance-future",
        )
        self.client.force_login(finance_user)

        self.client.post(reverse("portal:finance_payroll_generate", args=(period.pk,)))

        self.assertTrue(Payroll.objects.filter(payroll_period=period, employee=active_employee).exists())

    def test_payroll_generation_uses_salary_effective_at_period_start(self):
        """I7: mức lương hiệu lực từ 2026 không được dùng cho kỳ 12/2025."""
        employee = self.make_employee("PORTAL-PAYROLL-EFFECTIVE")
        EmployeeSalary.objects.create(
            employee=employee, current_basic_salary=Decimal("18000000"),
            effective_date=date(2024, 1, 1), end_date=date(2025, 12, 31), status="Ended",
        )
        EmployeeSalary.objects.create(
            employee=employee, current_basic_salary=Decimal("22000000"),
            effective_date=date(2026, 1, 1), status="Active",
        )
        finance_user = self.make_user("FINANCE_OFFICER", self.make_employee("PORTAL-PAYROLL-FINANCE-I7"), "portal-payroll-finance-i7b")
        period = PayrollPeriod.objects.create(
            payroll_month=12, payroll_year=2025,
            start_date=date(2025, 12, 1), end_date=date(2025, 12, 31), status="Open",
        )
        self.client.force_login(finance_user)

        self.client.post(reverse("portal:finance_payroll_generate", args=(period.pk,)))

        payroll = Payroll.objects.get(payroll_period=period, employee=employee)
        self.assertEqual(payroll.basic_salary, Decimal("18000000"))

    def test_inventory_completion_is_blocked_until_every_line_is_counted(self):
        employee = self.make_employee("PORTAL-INVENTORY-MANAGER")
        manager = self.make_user("HR_OFFICER", employee, "portal-inventory-manager")
        asset_type = AssetType.objects.create(
            asset_type_code="PORTAL-I11-TYPE", asset_type_name="Thiết bị kiểm thử I11",
        )
        asset = Asset.objects.create(
            asset_code="PORTAL-I11-ASSET", asset_name="Máy tính chưa kiểm đếm", asset_type=asset_type,
        )
        session = InventorySession.objects.create(
            session_name="I11 chưa đếm hết", office_name="Văn phòng kiểm thử",
            inventory_datetime="2026-09-27T09:00:00Z",
        )
        InventoryLine.objects.create(session=session, asset=asset, is_counted=False)
        self.client.force_login(manager)

        response = self.client.post(
            reverse("portal:inventory_session_complete", args=(session.pk,)),
            {"recommendation": "Không."},
        )

        session.refresh_from_db()
        self.assertRedirects(response, reverse("portal:inventory_session_detail", args=(session.pk,)))
        self.assertEqual(session.status, "Draft")

    def test_completed_inventory_line_cannot_be_changed_by_direct_post(self):
        employee = self.make_employee("PORTAL-INVENTORY-EDITOR")
        manager = self.make_user("HR_OFFICER", employee, "portal-inventory-editor")
        asset_type = AssetType.objects.create(
            asset_type_code="PORTAL-I11-TYPE-2", asset_type_name="Thiết bị kiểm thử I11-2",
        )
        asset = Asset.objects.create(
            asset_code="PORTAL-I11-ASSET-2", asset_name="Máy tính đã kiểm đếm", asset_type=asset_type,
        )
        session = InventorySession.objects.create(
            session_name="I11 đã hoàn tất", office_name="Văn phòng kiểm thử",
            inventory_datetime="2026-09-27T09:00:00Z",
        )
        line = InventoryLine.objects.create(
            session=session, asset=asset, is_counted=True, note="Ghi chú ban đầu",
        )
        session.status = "Completed"
        session.save()
        self.client.force_login(manager)

        response = self.client.post(
            reverse("portal:inventory_line_update", args=(line.pk,)),
            {"actual_condition": "Damaged", "note": "Sửa sau khi hoàn tất"},
        )

        line.refresh_from_db()
        self.assertRedirects(response, reverse("portal:inventory_session_detail", args=(session.pk,)))
        self.assertEqual(line.note, "Ghi chú ban đầu")
        self.assertEqual(line.actual_condition, "Normal")

    def test_org_chart_displays_manager_chain_and_search(self):
        manager = self.make_employee("PORTAL-CHART-MANAGER")
        report = self.make_employee("PORTAL-CHART-REPORT")
        report.manager = manager
        report.save(update_fields=("manager",))
        user = self.make_user("EMPLOYEE", report, "portal-chart-viewer")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:org_chart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="org-chart-search"')
        self.assertContains(response, 'id="org-chart-zoom-in"')
        self.assertContains(response, 'id="org-chart-zoom-out"')
        self.assertContains(response, 'id="org-chart-fit"')
        self.assertContains(response, "Báo cáo cho:")
        self.assertContains(response, manager.full_name)
        self.assertContains(response, report.full_name)
        self.assertEqual(response.context["employee_count"], 2)

    def test_project_task_menu_is_listed_under_project_activities(self):
        employee = self.make_employee("PORTAL-TASK-MENU")
        user = self.make_user("CBDA", employee, "portal-task-menu")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/home_dashboard.css?v=20261010-design")
        self.assertContains(response, "home-kpi-grid")
        task_link = f'href="{reverse("portal:task_list")}"'
        html = response.content.decode()
        self.assertEqual(html.count(task_link), 1)
        self.assertGreater(html.index(task_link), html.index('id="menu-hoatdongduan"'))
        self.assertContains(response, "Giao việc &amp; hoàn tất")
        self.assertNotContains(response, "Việc tôi đã giao")
        self.assertNotContains(response, "Quản lý checklist onboarding/offboarding")
        self.assertNotContains(response, "Checklist &amp; việc được giao")

        task_page = self.client.get(reverse("portal:task_list"))
        self.assertContains(task_page, "Theo dõi hoạt động")
        self.assertContains(task_page, "Việc của tôi")
        self.assertContains(task_page, "Việc tôi đã giao")
        self.assertNotContains(task_page, "+ Giao việc mới")

    def test_hr_checklist_menu_appears_only_under_hr_menu(self):
        employee = self.make_employee("PORTAL-HR-MENU")
        user = self.make_user("HR_OFFICER", employee, "portal-hr-menu")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Checklist tiếp nhận/nghỉ việc")
        self.assertContains(response, reverse("portal:lifecycle_case_list"))
        self.assertNotContains(response, "Checklist &amp; việc được giao")

    def test_employee_action_menu_has_working_native_dropdown_markup(self):
        employee = self.make_employee("PORTAL-ACTION-MENU")
        user = self.make_user("HR_OFFICER", employee, "portal-action-menu")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:hr_employee_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<details class=\"hr-action-menu relative inline-block\">")
        self.assertContains(response, reverse("portal:hr_employee_edit", args=(employee.pk,)))
        self.assertNotContains(response, "toggleMenu(")

    def test_hr_can_open_edit_employee_form_without_missing_initial_values(self):
        employee = self.make_employee("PORTAL-EDIT-FORM")
        user = self.make_user("HR_OFFICER", employee, "portal-edit-form")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:hr_employee_edit", args=(employee.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="employee_code"')
        self.assertContains(response, employee.employee_code)

    def test_task_list_can_switch_between_assigned_and_assigned_by_me(self):
        assigner = self.make_employee("PORTAL-TASK-LIST-ASSIGNER")
        assignee = self.make_employee("PORTAL-TASK-LIST-ASSIGNEE")
        other_assigner = self.make_employee("PORTAL-TASK-LIST-OTHER")
        user = self.make_user("HR_MANAGER", assigner, "portal-task-list-assigner")
        assigned_by_me = Task.objects.create(
            task_code="PORTAL-TASK-ASSIGNED-BY-ME",
            task_name="Task do tôi giao",
            assigned_by_employee=assigner,
            assigned_to_employee=assignee,
            due_date=date(2026, 10, 10),
            created_by=user,
        )
        assigned_by_other = Task.objects.create(
            task_code="PORTAL-TASK-ASSIGNED-BY-OTHER",
            task_name="Task người khác giao",
            assigned_by_employee=other_assigner,
            assigned_to_employee=assignee,
            due_date=date(2026, 10, 11),
            created_by=user,
        )
        self.client.force_login(user)

        own_work = self.client.get(reverse("portal:task_list"))
        self.assertEqual(own_work.status_code, 200)
        self.assertContains(own_work, "Việc của tôi")
        self.assertContains(own_work, "Việc tôi đã giao")
        self.assertContains(
            own_work,
            f'href="{reverse("portal:task_list")}?scope=assigned_by_me"',
        )
        self.assertEqual(list(own_work.context["tasks"]), [])

        assigned_work = self.client.get(reverse("portal:task_list"), {"scope": "assigned_by_me"})

        self.assertEqual(assigned_work.status_code, 200)
        self.assertEqual(assigned_work.context["task_scope_name"], "assigned_by_me")
        self.assertEqual(list(assigned_work.context["tasks"]), [assigned_by_me])
        self.assertNotIn(assigned_by_other, assigned_work.context["tasks"])

    def test_dept_manager_can_create_task_and_see_it_in_assigned_by_me_tab(self):
        manager = self.make_employee("PORTAL-DEPT-TASK-MANAGER")
        assignee = self.make_employee("PORTAL-DEPT-TASK-ASSIGNEE")
        self.department.manager = manager
        self.department.save(update_fields=("manager",))
        user = self.make_user("DEPT_MANAGER", manager, "portal-dept-task-manager")
        self.client.force_login(user)

        create_url = reverse("portal:task_create")
        form = self.client.get(create_url)
        self.assertEqual(form.status_code, 200)
        self.assertIn(assignee, form.context["candidates"])

        response = self.client.post(create_url, {
            "task_code": "PORTAL-DEPT-TASK-CREATED",
            "task_name": "Công việc trưởng phòng giao",
            "assigned_to_employee": str(assignee.pk),
            "department": str(self.department.pk),
            "priority": "Normal",
            "start_date": "2026-10-01",
            "due_date": "2026-10-10",
        })

        self.assertRedirects(response, reverse("portal:task_list"))
        task = Task.objects.get(task_code="PORTAL-DEPT-TASK-CREATED")
        self.assertEqual(task.assigned_by_employee, manager)
        self.assertEqual(task.assigned_to_employee, assignee)
        self.assertIsNone(task.activity_id)

        assigned_by_me = self.client.get(
            reverse("portal:task_list"), {"scope": "assigned_by_me"}
        )
        self.assertEqual(list(assigned_by_me.context["tasks"]), [task])
        detail = self.client.get(reverse("portal:task_detail", args=(task.pk,)))
        self.assertEqual(detail.status_code, 200)

    def test_dept_manager_cannot_assign_or_view_task_outside_managed_departments(self):
        manager = self.make_employee("PORTAL-DEPT-TASK-SCOPE-MANAGER")
        self.department.manager = manager
        self.department.save(update_fields=("manager",))
        other_department = Department.objects.create(
            department_code="PORTAL-DEPT-TASK-SCOPE-OTHER",
            department_name="Phòng ban ngoài phạm vi",
            organization=self.organization,
        )
        other_employee = self.make_employee("PORTAL-DEPT-TASK-SCOPE-EMPLOYEE")
        other_employee.department = other_department
        other_employee.save(update_fields=("department",))
        user = self.make_user("DEPT_MANAGER", manager, "portal-dept-task-scope-manager")
        existing_task = Task.objects.create(
            task_code="PORTAL-DEPT-TASK-OUTSIDE-EXISTING",
            task_name="Task thuộc phòng ban khác",
            assigned_by_employee=manager,
            assigned_to_employee=other_employee,
            department=other_department,
            due_date=date(2026, 10, 10),
            created_by=user,
        )
        self.client.force_login(user)

        detail = self.client.get(reverse("portal:task_detail", args=(existing_task.pk,)))
        self.assertRedirects(detail, reverse("portal:task_list"))

        create_url = reverse("portal:task_create")
        form = self.client.get(create_url)
        self.assertNotIn(other_employee, form.context["candidates"])
        response = self.client.post(create_url, {
            "task_code": "PORTAL-DEPT-TASK-OUTSIDE-POST",
            "task_name": "Không được giao sang phòng khác",
            "assigned_to_employee": str(other_employee.pk),
            "department": str(other_department.pk),
            "priority": "Normal",
            "start_date": "2026-10-01",
            "due_date": "2026-10-10",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Task.objects.filter(task_code="PORTAL-DEPT-TASK-OUTSIDE-POST").exists()
        )

    def test_hr_manager_can_create_and_view_task_across_departments(self):
        hr_employee = self.make_employee("PORTAL-HR-TASK-MANAGER")
        user = self.make_user("HR_MANAGER", hr_employee, "portal-hr-task-manager")
        other_department = Department.objects.create(
            department_code="PORTAL-HR-TASK-OTHER-DEPT",
            department_name="Phòng ban khác",
            organization=self.organization,
        )
        assignee = self.make_employee("PORTAL-HR-TASK-ASSIGNEE")
        assignee.department = other_department
        assignee.save(update_fields=("department",))
        self.client.force_login(user)

        create_url = reverse("portal:task_create")
        form = self.client.get(create_url)
        self.assertEqual(form.status_code, 200)
        self.assertIn(assignee, form.context["candidates"])

        response = self.client.post(create_url, {
            "task_code": "PORTAL-HR-TASK-CROSS-DEPT",
            "task_name": "Công việc HR giao cho phòng khác",
            "assigned_to_employee": str(assignee.pk),
            "department": str(other_department.pk),
            "priority": "Normal",
            "start_date": "2026-10-01",
            "due_date": "2026-10-10",
        })

        self.assertRedirects(response, reverse("portal:task_list"))
        task = Task.objects.get(task_code="PORTAL-HR-TASK-CROSS-DEPT")
        self.assertEqual(task.assigned_to_employee, assignee)
        self.assertEqual(task.department, other_department)
        self.assertIsNone(task.activity_id)
        assigned_by_me = self.client.get(
            reverse("portal:task_list"), {"scope": "assigned_by_me"}
        )
        self.assertEqual(list(assigned_by_me.context["tasks"]), [task])
        detail = self.client.get(reverse("portal:task_detail", args=(task.pk,)))
        self.assertEqual(detail.status_code, 200)

    def test_project_manager_sees_assigned_by_me_tab_and_project_scope(self):
        manager = self.make_employee("PORTAL-PROJECT-TASK-MANAGER")
        cbda = self.make_employee("PORTAL-PROJECT-TASK-CBDA")
        coordinator = self.make_employee("PORTAL-PROJECT-TASK-COORD")
        user = self.make_user("PROJECT_MANAGER", manager, "portal-project-task-manager")
        coordinator_user = self.make_user(
            "PROJECT_COORDINATOR", coordinator, "portal-project-task-coordinator"
        )
        project = Project.objects.create(
            project_code="PORTAL-PROJECT-TASK-PROJECT",
            project_name="Dự án kiểm thử vai trò quản lý",
            department=self.department,
        )
        activity = Activity.objects.create(
            activity_code="PORTAL-PROJECT-TASK-ACTIVITY",
            activity_name="Hoạt động giao cho CBDA",
            project=project,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
            lead_cbda=cbda,
            coordinator=coordinator,
        )
        project_task = Task.objects.create(
            task_code="PORTAL-PROJECT-TASK-REPORT",
            task_name="Task báo cáo trong phạm vi dự án",
            assigned_by_employee=coordinator,
            assigned_to_employee=cbda,
            activity=activity,
            due_date=date(2026, 10, 16),
            created_by=coordinator_user,
        )
        self.client.force_login(user)

        overview = self.client.get(reverse("portal:task_list"))
        self.assertEqual(overview.context["task_scope_name"], "activity_overview")
        self.assertEqual(list(overview.context["tasks"]), [project_task])
        self.assertContains(overview, "Theo dõi hoạt động")
        self.assertContains(overview, "Việc của tôi")
        self.assertContains(overview, "Việc tôi đã giao")

        my_tasks = self.client.get(
            reverse("portal:task_list"), {"scope": "assigned_to_me"}
        )
        self.assertEqual(list(my_tasks.context["tasks"]), [])
        assigned_by_me = self.client.get(
            reverse("portal:task_list"), {"scope": "assigned_by_me"}
        )
        self.assertEqual(list(assigned_by_me.context["tasks"]), [])

    def test_regular_employee_does_not_see_task_scope_tabs(self):
        employee = self.make_employee("PORTAL-TASK-REGULAR-EMPLOYEE")
        assigner = self.make_employee("PORTAL-TASK-REGULAR-ASSIGNER")
        user = self.make_user("EMPLOYEE", employee, "portal-task-regular-employee")
        task = Task.objects.create(
            task_code="PORTAL-TASK-REGULAR-OWN",
            task_name="Công việc cá nhân được giao",
            assigned_by_employee=assigner,
            assigned_to_employee=employee,
            due_date=date(2026, 10, 10),
            created_by=user,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("portal:task_list"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_view_task_scopes"])
        self.assertEqual(response.context["task_scope_name"], "assigned_to_me")
        self.assertEqual(list(response.context["tasks"]), [task])
        self.assertContains(response, "Công việc của tôi")
        self.assertNotContains(response, 'aria-label="Phạm vi công việc"')
        self.assertNotContains(response, "Việc tôi đã giao")
        self.assertNotContains(response, "+ Giao việc mới")
        self.assertNotContains(response, "CBDA phụ trách")
        self.assertNotContains(response, "Hoạt động")

    def test_director_sees_project_tasks_only_in_activity_overview_scope(self):
        director = self.make_employee("PORTAL-TASK-OVERVIEW-DIRECTOR")
        cbda = self.make_employee("PORTAL-TASK-OVERVIEW-CBDA")
        coordinator = self.make_employee("PORTAL-TASK-OVERVIEW-COORD")
        director_user = self.make_user(
            "DIRECTOR", director, "portal-task-activity-overview-director"
        )
        coordinator_user = self.make_user(
            "PROJECT_COORDINATOR", coordinator, "portal-task-activity-overview-coordinator"
        )
        project = Project.objects.create(
            project_code="PORTAL-TASK-OVERVIEW-PROJECT",
            project_name="Dự án kiểm thử phạm vi Task",
            department=self.department,
        )
        activity = Activity.objects.create(
            activity_code="PORTAL-TASK-OVERVIEW-ACTIVITY",
            activity_name="Hoạt động giao cho CBDA",
            project=project,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
            lead_cbda=cbda,
            coordinator=coordinator,
        )
        project_task = Task.objects.create(
            task_code="PORTAL-TASK-OVERVIEW-REPORT",
            task_name="Báo cáo của CBDA",
            assigned_by_employee=coordinator,
            assigned_to_employee=cbda,
            activity=activity,
            due_date=date(2026, 10, 16),
            created_by=coordinator_user,
        )
        self.client.force_login(director_user)

        default_scope = self.client.get(reverse("portal:task_list"))
        self.assertEqual(default_scope.context["task_scope_name"], "activity_overview")
        self.assertEqual(list(default_scope.context["tasks"]), [project_task])
        self.assertContains(default_scope, "Theo dõi hoạt động")
        self.assertContains(
            default_scope,
            f'href="{reverse("portal:task_list")}?scope=assigned_to_me"',
        )

        my_tasks = self.client.get(
            reverse("portal:task_list"), {"scope": "assigned_to_me"}
        )
        self.assertEqual(my_tasks.context["task_scope_name"], "assigned_to_me")
        self.assertEqual(list(my_tasks.context["tasks"]), [])

        assigned_by_me = self.client.get(
            reverse("portal:task_list"), {"scope": "assigned_by_me"}
        )
        self.assertEqual(list(assigned_by_me.context["tasks"]), [])

    def test_task_assigner_can_view_own_task_but_unrelated_employee_cannot(self):
        assigner = self.make_employee("PORTAL-TASK-VIEW-ASSIGNER")
        assignee = self.make_employee("PORTAL-TASK-VIEW-ASSIGNEE")
        unrelated = self.make_employee("PORTAL-TASK-VIEW-UNRELATED")
        assigner_user = self.make_user("DIRECTOR", assigner, "portal-task-view-director")
        unrelated_user = self.make_user("EMPLOYEE", unrelated, "portal-task-view-unrelated")
        task = Task.objects.create(
            task_code="PORTAL-TASK-ASSIGNER-VIEW",
            task_name="Task người giao cần xem lại",
            assigned_by_employee=assigner,
            assigned_to_employee=assignee,
            due_date=date(2026, 10, 12),
            created_by=assigner_user,
        )

        self.client.force_login(assigner_user)
        assigner_response = self.client.get(reverse("portal:task_detail", args=(task.pk,)))
        self.assertEqual(assigner_response.status_code, 200)
        self.assertContains(assigner_response, task.task_name)

        self.client.force_login(unrelated_user)
        unrelated_response = self.client.get(reverse("portal:task_detail", args=(task.pk,)))
        self.assertRedirects(unrelated_response, reverse("portal:task_list"))

    def test_edit_employee_with_deactivated_department_keeps_department_unless_explicitly_changed(self):
        inactive_department = Department.objects.create(
            department_code="PORTAL-INACTIVE-DEPT",
            department_name="Phòng ban đã ngừng hoạt động",
            organization=self.organization,
        )
        employee = self.make_employee("PORTAL-INACTIVE-DEPT-EMP")
        employee.department = inactive_department
        employee.save(update_fields=("department",))
        inactive_department.is_active = False
        inactive_department.save(update_fields=("is_active",))
        hr_employee = self.make_employee("PORTAL-INACTIVE-DEPT-HR")
        hr_user = self.make_user("HR_OFFICER", hr_employee, "portal-inactive-dept-hr")
        self.client.force_login(hr_user)
        edit_url = reverse("portal:hr_employee_edit", args=(employee.pk,))

        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(inactive_department, list(response.context["departments"]))
        self.assertContains(
            response,
            f'<option value="{inactive_department.pk}" selected>{inactive_department.department_name}</option>',
        )
        self.assertContains(response, "Phòng ban hiện tại đã ngừng hoạt động")

        response = self.client.post(edit_url, {
            "employee_code": employee.employee_code,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "full_name": employee.full_name,
            "date_of_birth": "1990-01-01",
            "gender": employee.gender,
            "national_id": employee.national_id,
            "tax_code": employee.tax_code or "",
            "social_insurance_no": employee.social_insurance_no or "",
            "company_email": employee.company_email,
            "personal_email": employee.personal_email or "",
            "mobile_phone": "0987654321",
            "address": employee.address or "",
            "join_date": "2020-01-01",
            "leave_date": "",
            "department": str(inactive_department.pk),
            "position": str(employee.position_id),
            "job_title": "",
            "manager": "",
            "employment_status": employee.employment_status,
        })

        self.assertRedirects(response, reverse("portal:hr_employee_detail", args=(employee.pk,)))
        employee.refresh_from_db()
        self.assertEqual(employee.department_id, inactive_department.pk)
        self.assertEqual(employee.mobile_phone, "0987654321")

    def test_task_completed_on_start_day_displays_actual_completion_date(self):
        employee = self.make_employee("PORTAL-TASK-SAME-DAY")
        user = self.make_user("EMPLOYEE", employee, "portal-task-same-day")
        work_date = date(2026, 9, 26)
        task = Task.objects.create(
            task_code="PORTAL-TASK-SAME-DAY",
            task_name="Công việc hoàn thành trong ngày",
            assigned_by_employee=employee,
            assigned_to_employee=employee,
            start_date=work_date,
            due_date=work_date,
            status="Todo",
            created_by=user,
        )
        self.client.force_login(user)

        with patch("apps.portal.views.tasks_kpi.timezone.localdate", return_value=work_date):
            response = self.client.post(
                reverse("portal:task_detail", args=(task.pk,)),
                {"action": "update_status", "status": "Done"},
            )

        task.refresh_from_db()
        self.assertRedirects(response, reverse("portal:task_detail", args=(task.pk,)))
        self.assertEqual(task.start_date, work_date)
        self.assertEqual(task.due_date, work_date)
        self.assertEqual(task.completed_date, work_date)

        detail = self.client.get(reverse("portal:task_detail", args=(task.pk,)))
        self.assertContains(detail, "Ngày bắt đầu:")
        self.assertContains(detail, "Ngày hoàn thành thực tế:")
        self.assertContains(detail, "26/09/2026")
        listing = self.client.get(reverse("portal:task_list"))
        self.assertContains(listing, "26/09/2026")

        with patch("apps.portal.views.tasks_kpi.timezone.localdate", return_value=date(2026, 9, 27)):
            self.client.post(
                reverse("portal:task_detail", args=(task.pk,)),
                {"action": "update_status", "status": "InProgress"},
            )
        task.refresh_from_db()
        self.assertIsNone(task.completed_date)

    def test_task_start_date_defaults_to_today(self):
        employee = self.make_employee("PORTAL-TASK-DEFAULT")
        user = self.make_user("HR_MANAGER", employee, "portal-task-default")
        self.client.force_login(user)

        with patch("apps.portal.views.tasks_kpi.timezone.localdate", return_value=date(2026, 9, 26)):
            response = self.client.get(reverse("portal:task_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="start_date" value="2026-09-26"')

    def test_asset_menu_and_pages_are_hidden_from_staff_outside_allowed_roles(self):
        for role_code in ("EMPLOYEE", "CBDA", "DEPT_MANAGER", "PROJECT_MANAGER"):
            employee = self.make_employee(f"PORTAL-ASSET-DENIED-{role_code}")
            user = self.make_user(role_code, employee, f"portal-asset-denied-{role_code.lower()}")
            self.client.force_login(user)

            dashboard = self.client.get(reverse("portal:dashboard"))
            self.assertEqual(dashboard.status_code, 200)
            for route_name in (
                "asset_list", "asset_admin_list", "inventory_session_list", "disposal_request_list",
            ):
                asset_url = reverse(f"portal:{route_name}")
                self.assertNotContains(dashboard, asset_url)
                response = self.client.get(asset_url)
                self.assertRedirects(response, reverse("portal:dashboard"))

    def test_asset_viewers_can_read_pages_but_only_hr_can_manage(self):
        asset_type = AssetType.objects.create(
            asset_type_code="PORTAL-ASSET-READ", asset_type_name="Thiết bị kiểm thử",
        )
        asset = Asset.objects.create(
            asset_code="PORTAL-ASSET-READ-1", asset_name="Máy tính kiểm thử", asset_type=asset_type,
        )
        session = InventorySession.objects.create(
            session_name="Kiểm kê kiểm thử", office_name="Văn phòng kiểm thử",
            inventory_datetime="2026-09-27T09:00:00Z",
        )
        inventory_line = InventoryLine.objects.create(session=session, asset=asset)
        requester = self.make_employee("PORTAL-ASSET-REQUESTER")
        disposal = AssetDisposalRequest.objects.create(
            request_no="PORTAL-ASSET-DISPOSAL", request_date=date(2026, 9, 27),
            location_name="Văn phòng kiểm thử", requested_by=requester,
        )

        for role_code in ("DIRECTOR", "FINANCE_OFFICER", "PROJECT_COORDINATOR"):
            employee = self.make_employee(f"PORTAL-ASSET-VIEW-{role_code}")
            user = self.make_user(role_code, employee, f"portal-asset-view-{role_code.lower()}")
            self.client.force_login(user)

            dashboard = self.client.get(reverse("portal:dashboard"))
            self.assertContains(dashboard, reverse("portal:asset_admin_list"))
            self.assertContains(dashboard, reverse("portal:inventory_session_list"))
            self.assertContains(dashboard, reverse("portal:disposal_request_list"))
            for route_name, args in (
                ("asset_list", ()),
                ("asset_admin_list", ()),
                ("inventory_session_list", ()),
                ("inventory_session_detail", (session.pk,)),
                ("disposal_request_list", ()),
                ("disposal_request_detail", (disposal.pk,)),
            ):
                response = self.client.get(reverse(f"portal:{route_name}", args=args))
                self.assertEqual(response.status_code, 200, f"{role_code}: {route_name}")

            asset_page = self.client.get(reverse("portal:asset_admin_list"))
            self.assertNotContains(asset_page, "Thêm tài sản mới")
            inventory_page = self.client.get(reverse("portal:inventory_session_list"))
            self.assertNotContains(inventory_page, "Tạo đợt kiểm kê mới")
            inventory_detail = self.client.get(
                reverse("portal:inventory_session_detail", args=(session.pk,))
            )
            self.assertNotContains(inventory_detail, 'name="action" value="add_member"')
            self.assertNotContains(
                inventory_detail,
                reverse("portal:inventory_line_update", args=(inventory_line.pk,)),
            )
            disposal_page = self.client.get(reverse("portal:disposal_request_list"))
            self.assertNotContains(disposal_page, "Tạo đề nghị mới")
            disposal_detail = self.client.get(
                reverse("portal:disposal_request_detail", args=(disposal.pk,))
            )
            self.assertNotContains(disposal_detail, 'name="action" value="add_member"')
            self.assertNotContains(disposal_detail, 'name="action" value="add_item"')

    def test_asset_viewer_cannot_write_by_posting_directly(self):
        employee = self.make_employee("PORTAL-ASSET-VIEWER-POST")
        user = self.make_user("FINANCE_OFFICER", employee, "portal-asset-viewer-post")
        asset_type = AssetType.objects.create(
            asset_type_code="PORTAL-ASSET-POST", asset_type_name="Thiết bị kiểm thử POST",
        )
        session = InventorySession.objects.create(
            session_name="Kiểm kê POST", office_name="Văn phòng kiểm thử",
            inventory_datetime="2026-09-27T09:00:00Z",
        )
        requester = self.make_employee("PORTAL-ASSET-POST-REQUESTER")
        disposal = AssetDisposalRequest.objects.create(
            request_no="PORTAL-ASSET-POST-DISPOSAL", request_date=date(2026, 9, 27),
            location_name="Văn phòng kiểm thử", requested_by=requester,
        )
        self.client.force_login(user)

        self.client.post(reverse("portal:asset_admin_create"), {
            "asset_code": "PORTAL-ASSET-FORGED", "asset_name": "Không được tạo",
            "asset_type": asset_type.pk,
        })
        self.client.post(reverse("portal:inventory_session_create"), {
            "session_name": "Không được tạo", "office_name": "Kiểm thử",
            "inventory_datetime": "2026-09-27T10:00",
        })
        self.client.post(reverse("portal:inventory_session_detail", args=(session.pk,)), {
            "action": "add_member", "employee": employee.pk, "role": "Member",
        })
        self.client.post(reverse("portal:disposal_request_detail", args=(disposal.pk,)), {
            "action": "add_member", "employee": employee.pk,
        })

        self.assertFalse(Asset.objects.filter(asset_code="PORTAL-ASSET-FORGED").exists())
        self.assertFalse(InventorySession.objects.filter(session_name="Không được tạo").exists())
        self.assertFalse(InventoryMember.objects.filter(session=session).exists())
        self.assertFalse(disposal.members.exists())

    def test_hr_retains_asset_management_access(self):
        employee = self.make_employee("PORTAL-ASSET-HR-MANAGER")
        user = self.make_user("HR_OFFICER", employee, "portal-asset-hr-manager")
        self.client.force_login(user)

        asset_page = self.client.get(reverse("portal:asset_admin_list"))
        inventory_page = self.client.get(reverse("portal:inventory_session_list"))
        disposal_page = self.client.get(reverse("portal:disposal_request_list"))

        self.assertContains(asset_page, "Thêm tài sản mới")
        self.assertContains(inventory_page, "Tạo đợt kiểm kê mới")
        self.assertContains(disposal_page, "Tạo đề nghị mới")

