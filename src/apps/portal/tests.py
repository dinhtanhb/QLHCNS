from datetime import date
from decimal import Decimal
from hashlib import sha256
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.asset.models import AssetDisposalRequest
from apps.hrm.models import Employee
from apps.leave.models import LeaveApproval, LeaveRequest, LeaveType
from apps.organization.models import Department, Organization, Position
from apps.payroll.models import Payroll, PayrollPeriod, Payslip
from apps.security.models import Role, User


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
        task_link = f'href="{reverse("portal:task_list")}"'
        html = response.content.decode()
        self.assertEqual(html.count(task_link), 1)
        self.assertGreater(html.index(task_link), html.index('id="menu-hoatdongduan"'))
        self.assertContains(response, "Giao việc &amp; hoàn tất")
        self.assertNotContains(response, "Quản lý checklist onboarding/offboarding")
        self.assertNotContains(response, "Checklist &amp; việc được giao")

    def test_hr_checklist_menu_appears_only_under_hr_menu(self):
        employee = self.make_employee("PORTAL-HR-MENU")
        user = self.make_user("HR_OFFICER", employee, "portal-hr-menu")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quản lý checklist onboarding/offboarding")
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
