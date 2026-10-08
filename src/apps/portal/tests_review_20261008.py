"""Regression tests for the confirmed Group A findings from the 2026-10-08 review."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
import io
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import close_old_connections, connection
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.urls import reverse

from apps.contract.models import Contract, ContractAppendix, ContractType
from apps.document.models import DispatchBook, DispatchTracking, OfficialDispatch
from apps.hrm.models import Employee
from apps.leave.models import LeaveBalance, LeaveRequest, LeaveType
from apps.lifecycle.models import (
    ChecklistTemplate,
    ChecklistTemplateItem,
    EmployeeLifecycleCase,
    LifecycleChecklistItem,
)
from apps.organization.models import Department, Organization, Position
from apps.payroll.models import EmployeeSalary, Payroll, PayrollPeriod
from apps.security.models import Role, User


class Review20261008Fixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            organization_code="REVIEW-20261008", organization_name="Review 2026-10-08"
        )
        cls.department = Department.objects.create(
            organization=cls.organization,
            department_code="REVIEW-20261008",
            department_name="Phòng review",
        )
        cls.position = Position.objects.create(
            position_code="REVIEW-20261008", position_name="Chuyên viên review"
        )

    def make_employee(self, code, *, join_date=date(2020, 1, 1)):
        return Employee.objects.create(
            employee_code=code,
            first_name="Kiểm thử",
            last_name=code,
            full_name=f"Nhân viên {code}",
            date_of_birth=date(1990, 1, 1),
            gender="Other",
            national_id=f"ID-{code}"[:20],
            company_email=f"{code.lower()}@example.test",
            mobile_phone="0900000000",
            join_date=join_date,
            department=self.department,
            position=self.position,
            employment_status="Active",
        )

    def make_user(self, role_code, employee, username, *, is_staff=False):
        role, _ = Role.objects.get_or_create(
            role_code=role_code, defaults={"role_name": role_code}
        )
        return User.objects.create_user(
            username=username,
            password="test-password",
            employee=employee,
            role=role,
            is_staff=is_staff,
        )

    def employee_form_data(self, suffix, *, employee_code="VH0001"):
        return {
            "employee_code": employee_code,
            "first_name": "Nhân viên",
            "last_name": suffix,
            "full_name": f"Nhân viên {suffix}",
            "date_of_birth": "1990-01-01",
            "gender": "Other",
            "national_id": f"NEW-ID-{suffix}"[:20],
            "tax_code": "",
            "social_insurance_no": "",
            "personal_email": "",
            "company_email": f"new-{suffix.lower()}@example.test",
            "mobile_phone": "0900000000",
            "address": "",
            "join_date": "2026-10-01",
            "leave_date": "",
            "department": str(self.department.pk),
            "position": str(self.position.pk),
            "job_title": "",
            "manager": "",
            "employment_status": "Active",
        }


class GroupAReviewFixTests(Review20261008Fixtures):
    def test_f02_dispatch_management_uses_manage_office_role_matrix(self):
        assignee = self.make_employee("F02-ASSIGNED")
        book = DispatchBook.objects.create(
            book_code="F02-OUT-2026",
            book_name="Sổ công văn F02",
            book_type="Outgoing",
            year=2026,
        )
        dispatch = OfficialDispatch.objects.create(
            dispatch_type="Outgoing",
            dispatch_book=book,
            dispatch_no="F02-001",
            title="Kiểm tra quyền công văn",
            issuing_organization="Đơn vị kiểm thử",
            issue_date=date(2026, 10, 8),
            received_or_sent_date=date(2026, 10, 8),
            department=self.department,
            assigned_to=assignee,
        )
        expectations = {
            "HR_MANAGER": True,
            "HR_OFFICER": True,
            "SYS_ADMIN": True,
            "DEPT_MANAGER": False,
            "DIRECTOR": False,
            "EMPLOYEE": False,
        }

        for index, (role_code, can_manage) in enumerate(expectations.items(), start=1):
            with self.subTest(role=role_code):
                employee = self.make_employee(f"F02-{index}")
                user = self.make_user(
                    role_code,
                    employee,
                    f"f02-{role_code.lower()}",
                    is_staff=role_code == "EMPLOYEE",
                )
                self.client.force_login(user)
                listing = self.client.get(reverse("portal:dispatch_list"))
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(listing.context["is_management"], can_manage)

                before = DispatchTracking.objects.filter(dispatch=dispatch).count()
                self.client.post(
                    reverse("portal:dispatch_detail", args=(dispatch.pk,)),
                    {"comment": f"Cập nhật {role_code}", "new_status": "Processing"},
                )
                self.assertEqual(
                    DispatchTracking.objects.filter(dispatch=dispatch).count(),
                    before + (1 if can_manage else 0),
                )
                create_page = self.client.get(reverse("portal:dispatch_create"))
                self.assertEqual(create_page.status_code, 200 if can_manage else 302)
                dispatch.status = "Pending"
                dispatch.save(update_fields=("status",))
                self.client.logout()

    def test_f06_payroll_generation_skips_and_lists_employee_without_effective_salary(self):
        finance_employee = self.make_employee("F06-FIN")
        finance_user = self.make_user("FINANCE_OFFICER", finance_employee, "f06-finance")
        missing_salary = self.make_employee("F06-MISSING")
        period = PayrollPeriod.objects.create(
            payroll_month=10,
            payroll_year=2026,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
        )
        EmployeeSalary.objects.create(
            employee=finance_employee,
            current_basic_salary=Decimal("12000000"),
            effective_date=date(2026, 1, 1),
            status="Active",
        )
        self.client.force_login(finance_user)

        response = self.client.post(
            reverse("portal:finance_payroll_generate", args=(period.pk,)), follow=True
        )

        self.assertTrue(Payroll.objects.filter(payroll_period=period, employee=finance_employee).exists())
        self.assertFalse(Payroll.objects.filter(payroll_period=period, employee=missing_salary).exists())
        self.assertContains(response, missing_salary.employee_code)
        preview = self.client.get(reverse("portal:finance_payroll_run", args=(period.pk,)))
        self.assertIn(missing_salary, list(preview.context["missing_salary_employees"]))

    def test_f06_payroll_period_with_zero_basic_salary_cannot_be_locked(self):
        finance_employee = self.make_employee("F06-ZERO-FIN")
        finance_user = self.make_user("FINANCE_OFFICER", finance_employee, "f06-zero-finance")
        period = PayrollPeriod.objects.create(
            payroll_month=11,
            payroll_year=2026,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 30),
        )
        payroll = Payroll.objects.create(
            payroll_period=period,
            employee=finance_employee,
            basic_salary=Decimal("0"),
        )
        self.client.force_login(finance_user)

        with patch.object(Payroll, "validate_calculated"):
            response = self.client.post(
                reverse("portal:finance_payroll_lock", args=(period.pk,)), follow=True
            )

        period.refresh_from_db()
        self.assertEqual(period.status, "Open")
        self.assertContains(response, "lương cơ bản bằng 0")
        self.assertFalse(hasattr(payroll, "payslip"))

    def test_f07_leave_creation_locks_employee_and_rejects_sequential_duplicate(self):
        employee = self.make_employee("F07-LEAVE")
        user = self.make_user("EMPLOYEE", employee, "f07-employee")
        leave_type = LeaveType.objects.create(
            leave_type_code="AL", leave_type_name="Phép năm F07", is_paid=True
        )
        LeaveBalance.objects.create(employee=employee, year=2026, allocated_days=12)
        payload = {
            "leave_type": str(leave_type.pk),
            "from_date": "2026-10-12",
            "to_date": "2026-10-13",
            "reason": "Kiểm tra gửi trùng",
        }
        self.client.force_login(user)

        original_lock = Employee.objects.select_for_update
        with patch(
            "apps.portal.views.attendance.Employee.objects.select_for_update",
            wraps=original_lock,
        ) as lock_employee:
            first = self.client.post(reverse("portal:leave_create"), payload)
        second = self.client.post(reverse("portal:leave_create"), payload)

        self.assertEqual(first.status_code, 302)
        lock_employee.assert_called_once_with()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(LeaveRequest.objects.filter(employee=employee).count(), 1)

    def test_f10_generated_employee_code_retries_after_sequential_collision(self):
        hr_employee = self.make_employee("F10-HR")
        hr_user = self.make_user("HR_MANAGER", hr_employee, "f10-hr")
        self.client.force_login(hr_user)

        first = self.client.post(
            reverse("portal:hr_employee_create"), self.employee_form_data("ONE")
        )
        second = self.client.post(
            reverse("portal:hr_employee_create"), self.employee_form_data("TWO")
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertTrue(Employee.objects.filter(employee_code="VH0001").exists())
        self.assertTrue(Employee.objects.filter(employee_code="VH0002").exists())

    def test_f11_lifecycle_update_locks_item_and_case_and_is_idempotent(self):
        employee = self.make_employee("F11-CASE")
        hr_employee = self.make_employee("F11-HR")
        hr_user = self.make_user("HR_OFFICER", hr_employee, "f11-hr")
        template = ChecklistTemplate.objects.create(
            template_code="F11-TPL", template_name="F11", template_type="Onboarding"
        )
        template_item = ChecklistTemplateItem.objects.create(
            template=template,
            sequence=1,
            item_name="Hoàn tất F11",
            responsible_role_code="HR_OFFICER",
        )
        case = EmployeeLifecycleCase.objects.create(
            employee=employee,
            template=template,
            case_type="Onboarding",
            effective_date=date(2026, 10, 8),
            triggering_event_ref="F11-CASE",
        )
        item = LifecycleChecklistItem.objects.create(
            case=case,
            template_item=template_item,
            item_name=template_item.item_name,
            responsible_role_code="HR_OFFICER",
            assigned_to_user=hr_user,
        )
        self.client.force_login(hr_user)

        item_lock = LifecycleChecklistItem.objects.select_for_update
        case_lock = EmployeeLifecycleCase.objects.select_for_update
        with patch(
            "apps.lifecycle.views.LifecycleChecklistItem.objects.select_for_update",
            wraps=item_lock,
        ) as lock_item, patch(
            "apps.lifecycle.views.EmployeeLifecycleCase.objects.select_for_update",
            wraps=case_lock,
        ) as lock_case:
            first = self.client.post(
                reverse("portal:lifecycle_item_update", args=(item.pk,)), {"action": "done"}
            )

        case.refresh_from_db()
        item.refresh_from_db()
        completed_at = item.completed_at
        second = self.client.post(
            reverse("portal:lifecycle_item_update", args=(item.pk,)), {"action": "done"}
        )
        item.refresh_from_db()
        case.refresh_from_db()

        self.assertEqual(first.status_code, 302)
        lock_item.assert_called_once_with()
        lock_case.assert_called_once_with()
        self.assertEqual(second.status_code, 403)
        self.assertEqual(item.completed_at, completed_at)
        self.assertEqual(case.status, "Completed")

    def test_f15_contract_renewal_uses_latest_active_contract_only(self):
        employee = self.make_employee("F15-EMP")
        hr_user = self.make_user("HR_MANAGER", self.make_employee("F15-HR"), "f15-hr")
        contract_type = ContractType.objects.create(
            contract_type_code="F15-TYPE", contract_type_name="Hợp đồng F15"
        )
        active = Contract.objects.create(
            employee=employee,
            contract_type=contract_type,
            contract_no="F15-ACTIVE",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 12, 31),
            basic_salary=Decimal("10000000"),
            status="Active",
        )
        terminated = Contract.objects.create(
            employee=employee,
            contract_type=contract_type,
            contract_no="F15-TERMINATED",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            basic_salary=Decimal("11000000"),
            status="Terminated",
        )
        self.client.force_login(hr_user)

        response = self.client.post(
            reverse("portal:hr_contract_renew", args=(employee.pk,)),
            {"new_end_date": "2027-12-31", "appendix_no": "F15-APPENDIX"},
        )

        active.refresh_from_db()
        terminated.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(active.end_date, date(2027, 12, 31))
        self.assertEqual(terminated.end_date, date(2026, 6, 30))
        self.assertTrue(ContractAppendix.objects.filter(contract=active).exists())
        self.assertFalse(ContractAppendix.objects.filter(contract=terminated).exists())

    def test_f16_dispatch_export_validates_type_and_names_internal_directive(self):
        employee = self.make_employee("F16-HR")
        user = self.make_user("HR_OFFICER", employee, "f16-hr")
        self.client.force_login(user)

        with patch(
            "apps.reporting.views.generate_dispatch_book_excel",
            return_value=io.BytesIO(b"xlsx"),
        ) as generate:
            invalid = self.client.get(
                reverse("reporting:export_dispatches"), {"type": "Invalid", "year": "2026"}
            )
            internal = self.client.get(
                reverse("reporting:export_dispatches"),
                {"type": "InternalDirective", "year": "2026"},
            )

        self.assertEqual(generate.call_args_list[0].kwargs["dispatch_type"], "Incoming")
        self.assertIn("2026-den", invalid["Content-Disposition"])
        self.assertEqual(generate.call_args_list[1].kwargs["dispatch_type"], "InternalDirective")
        self.assertIn("2026-noi-bo", internal["Content-Disposition"])


@skipUnless(connection.vendor == "microsoft", "Requires SQL Server row locking.")
class ConcurrentGroupAReviewFixTests(TransactionTestCase):
    """Exercise the two race-condition fixes against real SQL Server locks."""

    def setUp(self):
        self.organization = Organization.objects.create(
            organization_code="REVIEW-CONCURRENT-A",
            organization_name="Review concurrent Group A",
        )
        self.department = Department.objects.create(
            organization=self.organization,
            department_code="REVIEW-CONCURRENT-A",
            department_name="Phòng review đồng thời",
        )
        self.position = Position.objects.create(
            position_code="REVIEW-CONCURRENT-A",
            position_name="Chuyên viên review đồng thời",
        )

    def make_employee(self, code):
        return Employee.objects.create(
            employee_code=code,
            first_name="Kiểm thử",
            last_name=code,
            full_name=f"Nhân viên {code}",
            date_of_birth=date(1990, 1, 1),
            gender="Other",
            national_id=f"ID-{code}"[:20],
            company_email=f"{code.lower()}@example.test",
            mobile_phone="0900000000",
            join_date=date(2020, 1, 1),
            department=self.department,
            position=self.position,
            employment_status="Active",
        )

    def make_user(self, role_code, employee, username):
        role, _ = Role.objects.get_or_create(
            role_code=role_code, defaults={"role_name": role_code}
        )
        return User.objects.create_user(
            username=username,
            password="test-password",
            employee=employee,
            role=role,
        )

    def request(self, path, payload, user_pk):
        request = RequestFactory().post(path, payload)
        request.user = User.objects.get(pk=user_pk)
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_f07_two_simultaneous_leave_submissions_create_one_request(self):
        from apps.portal.views.attendance import leave_create

        employee = self.make_employee("F07-CONCURRENT")
        user = self.make_user("EMPLOYEE", employee, "f07-concurrent")
        leave_type = LeaveType.objects.create(
            leave_type_code="AL", leave_type_name="Phép năm F07 đồng thời", is_paid=True
        )
        LeaveBalance.objects.create(employee=employee, year=2026, allocated_days=12)
        payload = {
            "leave_type": str(leave_type.pk),
            "from_date": "2026-10-12",
            "to_date": "2026-10-13",
            "reason": "Kiểm tra gửi đồng thời",
        }
        barrier = Barrier(2)

        def submit(_index):
            close_old_connections()
            try:
                request = self.request(
                    reverse("portal:leave_create"), payload, user.pk
                )
                barrier.wait(timeout=10)
                return leave_create(request).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit, (1, 2)))

        self.assertEqual(sorted(statuses), [200, 302])
        self.assertEqual(LeaveRequest.objects.filter(employee=employee).count(), 1)

    def test_f10_two_simultaneous_generated_codes_are_unique(self):
        from apps.portal.views.hr import hr_employee_create

        hr_employee = self.make_employee("F10-CONCURRENT-HR")
        user = self.make_user("HR_MANAGER", hr_employee, "f10-concurrent")
        barrier = Barrier(2)

        def submit(index):
            close_old_connections()
            try:
                payload = {
                    "employee_code": "VH0001",
                    "first_name": "Nhân viên",
                    "last_name": f"CONCURRENT-{index}",
                    "full_name": f"Nhân viên đồng thời {index}",
                    "date_of_birth": "1990-01-01",
                    "gender": "Other",
                    "national_id": f"NEW-CONCURRENT-{index}",
                    "tax_code": "",
                    "social_insurance_no": "",
                    "personal_email": "",
                    "company_email": f"concurrent-{index}@example.test",
                    "mobile_phone": "0900000000",
                    "address": "",
                    "join_date": "2026-10-01",
                    "leave_date": "",
                    "department": str(self.department.pk),
                    "position": str(self.position.pk),
                    "job_title": "",
                    "manager": "",
                    "employment_status": "Active",
                }
                request = self.request(
                    reverse("portal:hr_employee_create"), payload, user.pk
                )
                barrier.wait(timeout=10)
                return hr_employee_create(request).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit, (1, 2)))

        self.assertEqual(statuses, [302, 302])
        self.assertEqual(
            set(
                Employee.objects.filter(employee_code__startswith="VH").values_list(
                    "employee_code", flat=True
                )
            ),
            {"VH0001", "VH0002"},
        )
