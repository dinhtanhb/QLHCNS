"""Kiểm thử hồi quy cho module chấm công (`attendance`).

Trước đợt này app chỉ có file test rỗng (placeholder). Đây là module nuôi
dữ liệu trực tiếp vào lương (`Payroll.calculate()` dùng `actual_working_days`
tính từ `MonthlyAttendanceSummary`) và vào báo cáo BCC gửi nhà tài trợ (NGO),
nên rủi ro cao nhất nếu có lỗi. Test tập trung vào đúng luồng đã từng là lỗi
I3 (nhân viên tự khai số liệu ảnh hưởng lương mà không ai duyệt lại) — khóa
lại để không quay về hành vi cũ.

Chạy: python manage.py test apps.attendance
"""

from datetime import date
from hashlib import sha256

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.attendance.models import Attendance, MonthlyAttendanceSummary
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User


class AttendanceTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            organization_code="ATT-TEST", organization_name="Tổ chức kiểm thử chấm công"
        )
        cls.dept_a = Department.objects.create(
            department_code="ATT-A", department_name="Phòng A", organization=cls.organization
        )
        cls.dept_b = Department.objects.create(
            department_code="ATT-B", department_name="Phòng B", organization=cls.organization
        )
        cls.position = Position.objects.create(position_code="ATT-STAFF", position_name="Chuyên viên")

    @classmethod
    def make_employee(cls, code, department):
        return Employee.objects.create(
            employee_code=code, first_name="Nguyễn", last_name="Kiểm thử",
            full_name=f"Nhân viên {code}", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=sha256(code.encode("utf-8")).hexdigest()[:20],
            company_email=f"{code.lower()}@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=department, position=cls.position,
            employment_status="Active",
        )

    @classmethod
    def make_user(cls, role_code, employee, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(username=username, password="test-password", employee=employee, role=role)


class AttendanceUniqueConstraintTests(AttendanceTestBase):
    """Ràng buộc DB: 1 nhân viên chỉ có 1 bản ghi chấm công / ngày, 1 bảng tổng hợp / tháng.
    Nếu ai vô tình bỏ constraint này, dữ liệu chấm công có thể bị nhân đôi giờ công."""

    def test_khong_the_tao_2_ban_ghi_cham_cong_trung_ngay(self):
        emp = self.make_employee("EMP-A1", self.dept_a)
        Attendance.objects.create(employee=emp, attendance_date=date(2026, 10, 1), status="Present")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(employee=emp, attendance_date=date(2026, 10, 1), status="Late")

    def test_khong_the_tao_2_bang_tong_hop_trung_thang(self):
        emp = self.make_employee("EMP-A2", self.dept_a)
        MonthlyAttendanceSummary.objects.create(employee=emp, year=2026, month=10)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MonthlyAttendanceSummary.objects.create(employee=emp, year=2026, month=10)


class TimesheetSummaryApprovalWorkflowTests(AttendanceTestBase):
    """I3 (đã sửa): số ngày nghỉ nhân viên tự khai chỉ có hiệu lực với lương/báo cáo sau khi
    được duyệt; đã duyệt rồi thì nhân viên không tự sửa được nữa."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff = cls.make_employee("EMP-B1", cls.dept_a)
        cls.staff_user = cls.make_user("EMPLOYEE", cls.staff, "staff-ts")
        cls.dept_a_manager = cls.make_employee("EMP-B2", cls.dept_a)
        cls.dept_a.manager = cls.dept_a_manager
        cls.dept_a.save(update_fields=["manager"])
        cls.dept_a_manager_user = cls.make_user("DEPT_MANAGER", cls.dept_a_manager, "mgr-a-ts")
        cls.dept_b_manager = cls.make_employee("EMP-B3", cls.dept_b)
        cls.dept_b.manager = cls.dept_b_manager
        cls.dept_b.save(update_fields=["manager"])
        cls.dept_b_manager_user = cls.make_user("DEPT_MANAGER", cls.dept_b_manager, "mgr-b-ts")

    def _submit(self, client, **days):
        payload = {"year": "2026", "month": "10", **days}
        return client.post(reverse("portal:timesheet_summary_update"), payload, follow=True)

    def test_nhan_vien_tu_khai_duoc_khi_con_pending(self):
        client = self.client_class()
        client.force_login(self.staff_user)
        self._submit(client, sick_days="2")
        summary = MonthlyAttendanceSummary.objects.get(employee=self.staff, year=2026, month=10)
        self.assertEqual(summary.status, MonthlyAttendanceSummary.STATUS_PENDING)
        self.assertEqual(float(summary.sick_days), 2)

    def test_khong_the_tu_sua_sau_khi_da_duoc_duyet(self):
        summary = MonthlyAttendanceSummary.objects.create(
            employee=self.staff, year=2026, month=10,
            status=MonthlyAttendanceSummary.STATUS_APPROVED,
            sick_days=1, approved_by=self.dept_a_manager_user,
        )
        client = self.client_class()
        client.force_login(self.staff_user)
        self._submit(client, sick_days="10")
        summary.refresh_from_db()
        self.assertEqual(
            float(summary.sick_days), 1,
            "Bảng đã duyệt không được tự sửa — nếu số đổi thành 10, lỗ hổng I3 đã quay lại.",
        )
        self.assertEqual(summary.status, MonthlyAttendanceSummary.STATUS_APPROVED)

    def test_truong_phong_A_khong_duyet_duoc_nhan_vien_phong_B(self):
        staff_b = self.make_employee("EMP-B4", self.dept_b)
        summary_b = MonthlyAttendanceSummary.objects.create(employee=staff_b, year=2026, month=10, sick_days=1)
        client = self.client_class()
        client.force_login(self.dept_a_manager_user)
        client.post(reverse("portal:timesheet_summary_approve", args=[summary_b.pk]), follow=True)
        summary_b.refresh_from_db()
        self.assertEqual(
            summary_b.status, MonthlyAttendanceSummary.STATUS_PENDING,
            "Trưởng phòng A không có quyền duyệt bảng chấm công của phòng B khác.",
        )

    def test_truong_phong_duyet_dung_pham_vi_thi_thanh_cong(self):
        summary_a = MonthlyAttendanceSummary.objects.create(employee=self.staff, year=2026, month=10, sick_days=1)
        client = self.client_class()
        client.force_login(self.dept_a_manager_user)
        client.post(reverse("portal:timesheet_summary_approve", args=[summary_a.pk]), follow=True)
        summary_a.refresh_from_db()
        self.assertEqual(summary_a.status, MonthlyAttendanceSummary.STATUS_APPROVED)
        self.assertEqual(summary_a.approved_by, self.dept_a_manager_user)
        self.assertIsNotNone(summary_a.approved_at)

    def test_nhan_vien_thuong_khong_the_tu_duyet_bang_cua_minh(self):
        summary = MonthlyAttendanceSummary.objects.create(employee=self.staff, year=2026, month=10, sick_days=1)
        client = self.client_class()
        client.force_login(self.staff_user)
        client.post(reverse("portal:timesheet_summary_approve", args=[summary.pk]), follow=True)
        summary.refresh_from_db()
        self.assertEqual(summary.status, MonthlyAttendanceSummary.STATUS_PENDING)

    def test_sua_lai_sau_khi_mo_lai_dua_ve_pending_va_xoa_thong_tin_duyet_cu(self):
        summary = MonthlyAttendanceSummary.objects.create(
            employee=self.staff, year=2026, month=10,
            status=MonthlyAttendanceSummary.STATUS_APPROVED,
            sick_days=1, approved_by=self.dept_a_manager_user,
        )
        # Quản lý chủ động mở lại (giả lập bằng set Pending) để nhân viên sửa — sau khi
        # nhân viên sửa lại, phải quay về Pending và xóa vết duyệt cũ, tránh hiển thị
        # nhầm "đã duyệt" cho số liệu mới chưa ai xác nhận.
        summary.status = MonthlyAttendanceSummary.STATUS_PENDING
        summary.save(update_fields=["status"])
        client = self.client_class()
        client.force_login(self.staff_user)
        self._submit(client, sick_days="3")
        summary.refresh_from_db()
        self.assertEqual(summary.status, MonthlyAttendanceSummary.STATUS_PENDING)
        self.assertIsNone(summary.approved_by)
        self.assertIsNone(summary.approved_at)