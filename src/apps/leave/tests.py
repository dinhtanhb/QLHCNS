"""Kiểm thử công thức nghỉ phép, quỹ phép năm và nghỉ bù.

Chạy:  python manage.py test apps.leave

Quy ước của Trung tâm đang áp dụng:
  - Ngày nghỉ phép chỉ đếm Thứ 2 → Thứ 6, đã trừ ngày lễ.
  - Đơn nghỉ vắt qua Thứ 7 / Chủ nhật thì hai ngày đó KHÔNG bị trừ phép.
  - Nghỉ bù được tính tự động từ bảng chấm công dự án: giờ làm vào
    Thứ 7 / Chủ nhật / ngày lễ quy đổi ra ngày (tối đa 1 ngày mỗi ngày làm),
    rồi làm tròn XUỐNG theo mức nửa ngày.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.attendance.models import Holiday, MonthlyAttendanceSummary, TimesheetEntry, WorkingCalendar
from apps.attendance.services import (
    compensatory_days_earned,
    get_hours_per_day,
    standard_working_days,
)
from apps.hrm.models import Employee
from apps.leave.models import LeaveBalance, LeaveRequest, LeaveType
from apps.organization.models import Department, Organization, Position

D = Decimal


class LeaveTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="ORG", organization_name="Trung tâm Thử Nghiệm")
        cls.department = Department.objects.create(
            department_code="IT", department_name="Công nghệ thông tin", organization=org
        )
        cls.position = Position.objects.create(position_code="DEV", position_name="Lập trình viên")
        cls.employee = Employee.objects.create(
            employee_code="NV001", first_name="A", last_name="Nguyễn Văn", full_name="Nguyễn Văn A",
            date_of_birth=date(1990, 1, 1), gender="Male", national_id="079090000001",
            company_email="nv001@example.com", mobile_phone="0900000001",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )
        WorkingCalendar.objects.create(
            calendar_year=2025, working_days_per_month=D("22"), working_hours_per_day=D("8"), is_default=True
        )
        # Dùng get_or_create vì loại nghỉ bù "CO" đã được migration tạo sẵn trong CSDL.
        cls.annual, _ = LeaveType.objects.get_or_create(
            leave_type_code="AL", defaults={"leave_type_name": "Phép năm", "is_paid": True}
        )
        cls.compensatory, _ = LeaveType.objects.get_or_create(
            leave_type_code="CO", defaults={"leave_type_name": "Nghỉ bù", "is_paid": True}
        )
        cls.unpaid, _ = LeaveType.objects.get_or_create(
            leave_type_code="UL", defaults={"leave_type_name": "Nghỉ không lương", "is_paid": False}
        )


# ------------------------------------------------------------------
# 1. ĐẾM NGÀY CÔNG CHUẨN
# ------------------------------------------------------------------
class StandardWorkingDaysTests(LeaveTestBase):

    def test_tron_mot_tuan_chi_tinh_nam_ngay(self):
        """02/06/2025 (T2) đến 08/06/2025 (CN) = 5 ngày công."""
        self.assertEqual(standard_working_days(date(2025, 6, 2), date(2025, 6, 8)), D("5"))

    def test_nghi_vat_qua_cuoi_tuan_khong_bi_tru_thu_bay_chu_nhat(self):
        """06/06 (T6) đến 09/06 (T2) = 2 ngày, không phải 4 ngày."""
        self.assertEqual(standard_working_days(date(2025, 6, 6), date(2025, 6, 9)), D("2"))

    def test_chi_chon_thu_bay_chu_nhat_thi_bang_khong(self):
        self.assertEqual(standard_working_days(date(2025, 6, 7), date(2025, 6, 8)), D("0"))

    def test_tru_ngay_le(self):
        """Tuần có 1 ngày lễ giữa tuần thì chỉ còn 4 ngày công."""
        Holiday.objects.create(
            holiday_code="QK2025", holiday_name="Quốc khánh", holiday_date=date(2025, 9, 2), is_active=True
        )
        self.assertEqual(standard_working_days(date(2025, 9, 1), date(2025, 9, 5)), D("4"))

    def test_ngay_le_tam_ngung_ap_dung_van_tinh_cong(self):
        Holiday.objects.create(
            holiday_code="TAM", holiday_name="Nghỉ thử", holiday_date=date(2025, 9, 3), is_active=False
        )
        self.assertEqual(standard_working_days(date(2025, 9, 1), date(2025, 9, 5)), D("5"))

    def test_mot_ngay_duy_nhat(self):
        self.assertEqual(standard_working_days(date(2025, 6, 2), date(2025, 6, 2)), D("1"))

    def test_ngay_ket_thuc_truoc_ngay_bat_dau(self):
        self.assertEqual(standard_working_days(date(2025, 6, 9), date(2025, 6, 2)), D("0"))

    def test_gio_lam_viec_moi_ngay_lay_theo_lich(self):
        self.assertEqual(get_hours_per_day(2025), D("8"))


# ------------------------------------------------------------------
# 2. NGHỈ BÙ TỰ ĐỘNG TỪ BẢNG CHẤM CÔNG
# ------------------------------------------------------------------
class CompensatoryDaysTests(LeaveTestBase):

    def _log(self, day, hours, approved=True):
        # Build each fixture through a pending month, then approve its complete entries.
        summary, _ = MonthlyAttendanceSummary.objects.get_or_create(employee=self.employee,
            year=day.year, month=day.month)
        if summary.status == "Approved":
            summary.status = "Pending"
            summary.save()
        TimesheetEntry.objects.create(employee=self.employee, work_date=day, hours=D(str(hours)))
        summary.status = "Approved" if approved else "Pending"
        summary.save()

    def test_lam_ca_ngay_thu_bay_duoc_mot_ngay_bu(self):
        self._log(date(2025, 6, 14), 8)  # Thứ 7
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("1"))

    def test_lam_nua_ngay_chu_nhat_duoc_nua_ngay_bu(self):
        self._log(date(2025, 6, 15), 4)  # Chủ nhật
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("0.5"))

    def test_lam_qua_gio_van_toi_da_mot_ngay_bu(self):
        self._log(date(2025, 6, 14), 12)
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("1"))

    def test_lam_ngay_thuong_khong_duoc_nghi_bu(self):
        self._log(date(2025, 6, 16), 8)  # Thứ 2
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("0"))

    def test_lam_ngay_le_duoc_nghi_bu(self):
        Holiday.objects.create(
            holiday_code="QK2025", holiday_name="Quốc khánh", holiday_date=date(2025, 9, 2), is_active=True
        )
        self._log(date(2025, 9, 2), 8)
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("1"))

    def test_lam_tron_xuong_theo_nua_ngay(self):
        """3 giờ = 0,375 ngày → làm tròn xuống còn 0 ngày."""
        self._log(date(2025, 6, 14), 3)
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("0"))

    def test_cong_don_nhieu_ngay_cuoi_tuan(self):
        self._log(date(2025, 6, 14), 8)   # T7 -> 1
        self._log(date(2025, 6, 15), 4)   # CN -> 0,5
        self._log(date(2025, 6, 21), 8)   # T7 -> 1
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("2.5"))

    def test_khong_tinh_gio_cua_nam_khac(self):
        self._log(date(2024, 6, 15), 8)
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("0"))

    def test_I3_gio_cuoi_tuan_chua_duoc_duyet_chua_duoc_tinh_nghi_bu(self):
        """Giờ cuối tuần chỉ chuyển thành nghỉ bù sau khi bảng công tháng được duyệt."""
        self._log(date(2025, 6, 14), 8, approved=False)
        summary = MonthlyAttendanceSummary.objects.get(employee=self.employee, year=2025, month=6)

        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("0"))

        summary.status = MonthlyAttendanceSummary.STATUS_APPROVED
        summary.save(update_fields=["status"])
        self.assertEqual(compensatory_days_earned(self.employee, 2025), D("1"))


# ------------------------------------------------------------------
# 3. QUỸ PHÉP NĂM
# ------------------------------------------------------------------
class LeaveBalanceTests(LeaveTestBase):

    def setUp(self):
        self.balance = LeaveBalance.objects.create(
            employee=self.employee, year=2025, allocated_days=D("12"), carried_over_days=D("2")
        )

    def _request(self, from_date, to_date, status="Approved", leave_type=None):
        req = LeaveRequest(
            employee=self.employee, leave_type=leave_type or self.annual,
            from_date=from_date, to_date=to_date, status=status,
        )
        req.total_days = req.compute_total_days()
        req.save()
        return req

    def test_con_lai_bang_cap_cong_chuyen_qua(self):
        self.assertEqual(self.balance.remaining_days, D("14"))
        self.assertEqual(self.balance.available_annual_days, D("14"))

    def test_don_da_duyet_tru_vao_quy(self):
        self._request(date(2025, 6, 2), date(2025, 6, 4), status="Approved")  # 3 ngày
        self.assertEqual(self.balance.used_days, D("3"))
        self.assertEqual(self.balance.remaining_days, D("11"))

    def test_don_cho_duyet_giu_cho_trong_quy(self):
        self._request(date(2025, 6, 2), date(2025, 6, 4), status="Pending")
        self.assertEqual(self.balance.used_days, D("0"))
        self.assertEqual(self.balance.pending_days, D("3"))
        self.assertEqual(self.balance.available_annual_days, D("11"))

    def test_don_bi_tu_choi_khong_tru_quy(self):
        self._request(date(2025, 6, 2), date(2025, 6, 4), status="Rejected")
        self.assertEqual(self.balance.available_annual_days, D("14"))

    def test_leave_spanning_new_year_is_split_between_each_year_balance(self):
        """I4 regression: ngày nghỉ được phân bổ vào đúng năm dương lịch của từng ngày."""
        from apps.leave.models import LeaveBalance
        LeaveBalance.objects.create(employee=self.employee, year=2026, allocated_days=D("3"))
        req = self._request(date(2025, 12, 29), date(2026, 1, 5))
        balance_2025 = LeaveBalance.objects.get(employee=self.employee, year=2025)
        balance_2026 = LeaveBalance.objects.get(employee=self.employee, year=2026)
        self.assertEqual(req.total_days, D("6"))
        self.assertEqual(balance_2025.used_days, D("3"))
        self.assertEqual(balance_2026.used_days, D("3"))

    def test_leave_request_requires_quota_in_every_calendar_year_it_uses(self):
        from apps.leave.models import LeaveBalance
        LeaveBalance.objects.create(employee=self.employee, year=2026, allocated_days=D("2"))
        with self.assertRaises(ValidationError):
            LeaveRequest(
                employee=self.employee, leave_type=self.annual,
                from_date=date(2025, 12, 29), to_date=date(2026, 1, 5), status="Pending",
            ).full_clean()

    def test_leave_days_by_month_splits_spanning_request(self):
        """I4 regression: bảng công tháng 1 không gộp ngày nghỉ của tháng 12."""
        from apps.portal.views import _leave_days_in_month
        req = self._request(date(2025, 12, 29), date(2026, 1, 5))
        self.assertEqual(_leave_days_in_month(self.employee, "AL", 2025, 12), D("3"))
        self.assertEqual(_leave_days_in_month(self.employee, "AL", 2026, 1), D("3"))


# ------------------------------------------------------------------
# 4. RÀNG BUỘC KHI GỬI ĐƠN
# ------------------------------------------------------------------
class LeaveRequestValidationTests(LeaveTestBase):

    def setUp(self):
        self.balance = LeaveBalance.objects.create(
            employee=self.employee, year=2025, allocated_days=D("5"), carried_over_days=D("0")
        )

    def _new(self, from_date, to_date, leave_type=None, status="Pending"):
        return LeaveRequest(
            employee=self.employee, leave_type=leave_type or self.annual,
            from_date=from_date, to_date=to_date, status=status,
        )

    def test_don_hop_le_tinh_dung_so_ngay(self):
        req = self._new(date(2025, 6, 6), date(2025, 6, 9))  # T6 -> T2
        req.full_clean()
        self.assertEqual(req.total_days, D("2"))

    def test_ngay_ket_thuc_truoc_ngay_bat_dau_bi_chan(self):
        with self.assertRaises(ValidationError):
            self._new(date(2025, 6, 9), date(2025, 6, 2)).full_clean()

    def test_chon_toan_cuoi_tuan_bi_chan(self):
        with self.assertRaises(ValidationError):
            self._new(date(2025, 6, 7), date(2025, 6, 8)).full_clean()

    def test_chan_don_trung_ngay(self):
        first = self._new(date(2025, 6, 2), date(2025, 6, 4))
        first.full_clean()
        first.save()
        with self.assertRaises(ValidationError):
            self._new(date(2025, 6, 3), date(2025, 6, 5)).full_clean()

    def test_don_da_huy_khong_chan_don_moi(self):
        cancelled = self._new(date(2025, 6, 2), date(2025, 6, 4), status="Cancelled")
        cancelled.total_days = cancelled.compute_total_days()
        cancelled.save()
        again = self._new(date(2025, 6, 2), date(2025, 6, 4))
        again.full_clean()  # không được báo lỗi

    def test_chan_nghi_vuot_quy_phep_nam(self):
        """Quỹ 5 ngày, xin nghỉ 10 ngày công (02/06 → 13/06)."""
        with self.assertRaises(ValidationError):
            self._new(date(2025, 6, 2), date(2025, 6, 13)).full_clean()

    def test_chua_khai_han_muc_thi_khong_cho_xin_phep_nam(self):
        LeaveBalance.objects.all().delete()
        with self.assertRaises(ValidationError):
            self._new(date(2025, 6, 2), date(2025, 6, 3)).full_clean()

    def test_nghi_khong_luong_khong_bi_gioi_han_quy(self):
        req = self._new(date(2025, 6, 2), date(2025, 6, 13), leave_type=self.unpaid)
        req.full_clean()
        self.assertEqual(req.total_days, D("10"))

    def test_chan_nghi_bu_vuot_so_ngay_tich_luy(self):
        """Chưa đi làm cuối tuần ngày nào mà xin nghỉ bù thì phải bị chặn."""
        with self.assertRaises(ValidationError):
            self._new(date(2025, 6, 2), date(2025, 6, 3), leave_type=self.compensatory).full_clean()

    def test_nghi_bu_trong_pham_vi_tich_luy_thi_duoc(self):
        TimesheetEntry.objects.create(employee=self.employee, work_date=date(2025, 6, 14), hours=D("8"))
        TimesheetEntry.objects.create(employee=self.employee, work_date=date(2025, 6, 21), hours=D("8"))
        MonthlyAttendanceSummary.objects.create(
            employee=self.employee, year=2025, month=6,
            status=MonthlyAttendanceSummary.STATUS_APPROVED,
        )
        req = self._new(date(2025, 6, 23), date(2025, 6, 24), leave_type=self.compensatory)
        req.full_clean()
        self.assertEqual(req.total_days, D("2"))

