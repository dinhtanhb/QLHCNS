"""Kiểm thử tự động cho công thức tính lương — Bảo hiểm & Thuế TNCN.

Chạy toàn bộ:      python manage.py test apps.payroll
Chạy 1 nhóm:       python manage.py test apps.payroll.tests.InsuranceCalculationTests

Mọi con số kỳ vọng trong file này đều được tính tay theo quy định hiện hành:
  - BHXH 8% + BHYT 1,5% + BHTN 1% do người lao động đóng
  - Trần đóng BHXH/BHYT = 20 x lương cơ sở (2.340.000) = 46.800.000
  - Trần đóng BHTN      = 20 x lương tối thiểu vùng I (4.960.000) = 99.200.000
  - Giảm trừ bản thân 11.000.000, mỗi người phụ thuộc 4.400.000
  - Biểu thuế lũy tiến 7 bậc: 5/10/15/20/25/30/35%

Nếu sau này sửa công thức mà làm sai, các bài kiểm thử dưới đây sẽ báo đỏ ngay.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.payroll.models import (
    EmployeeDependent,
    InsuranceRateConfig,
    Payroll,
    PayrollPeriod,
    PersonalIncomeTaxBracket,
    TaxDeductionConfig,
)

D = Decimal


# ------------------------------------------------------------------
# Dữ liệu nền dùng chung cho mọi bài kiểm thử
# ------------------------------------------------------------------
class PayrollTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="ORG", organization_name="Công ty TNHH Thử Nghiệm")
        cls.department = Department.objects.create(
            department_code="IT", department_name="Công nghệ thông tin", organization=org
        )
        cls.position = Position.objects.create(position_code="DEV", position_name="Lập trình viên")
        cls.employee = cls._create_employee("NV001")

        cls.period = PayrollPeriod.objects.create(
            payroll_month=1, payroll_year=2025,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
            status="Open",
        )

        cls.insurance_cfg = InsuranceRateConfig.objects.create(
            effective_from=date(2024, 7, 1),
            employee_social_insurance_rate=D("8"),
            employee_health_insurance_rate=D("1.5"),
            employee_unemployment_insurance_rate=D("1"),
            employer_social_insurance_rate=D("17.5"),
            employer_health_insurance_rate=D("3"),
            employer_unemployment_insurance_rate=D("1"),
            base_salary_reference=D("2340000"),
            regional_minimum_wage=D("4960000"),
        )
        TaxDeductionConfig.objects.create(
            effective_from=date(2020, 7, 1),
            self_deduction_monthly=D("11000000"),
            dependent_deduction_monthly=D("4400000"),
        )
        brackets = [
            (1, "0", "5000000", "5"),
            (2, "5000000", "10000000", "10"),
            (3, "10000000", "18000000", "15"),
            (4, "18000000", "32000000", "20"),
            (5, "32000000", "52000000", "25"),
            (6, "52000000", "80000000", "30"),
            (7, "80000000", None, "35"),
        ]
        for no, lo, hi, rate in brackets:
            PersonalIncomeTaxBracket.objects.create(
                effective_from=date(2020, 7, 1),
                bracket_no=no,
                income_from_monthly=D(lo),
                income_to_monthly=D(hi) if hi else None,
                tax_rate=D(rate),
            )

    @classmethod
    def _create_employee(cls, code):
        return Employee.objects.create(
            employee_code=code,
            first_name="A", last_name="Nguyễn Văn", full_name=f"Nhân viên {code}",
            date_of_birth=date(1990, 1, 1), gender="Male",
            national_id=f"0790{code}",
            company_email=f"{code.lower()}@example.com",
            mobile_phone="0900000000",
            join_date=date(2020, 1, 1),
            department=cls.department, position=cls.position,
            employment_status="Active",
        )

    def make_payroll(self, employee=None, **kwargs):
        """Tạo bảng lương (chưa lưu) rồi gọi calculate()."""
        payroll = Payroll(
            payroll_period=self.period,
            employee=employee or self.employee,
            **kwargs,
        )
        payroll.calculate()
        return payroll


# ------------------------------------------------------------------
# 1. BẢO HIỂM
# ------------------------------------------------------------------
class PayrollConfigurationReuseTests(PayrollTestBase):
    def test_reusing_configuration_preserves_results_and_avoids_reloading(self):
        reference = self.make_payroll(basic_salary=D('20000000'), allowance=D('2000000'))
        with self.assertNumQueries(4):
            configuration = Payroll.load_calculation_configuration(self.period.start_date)
        for _ in range(2):
            payroll = Payroll(payroll_period=self.period, employee=self.employee,
                              basic_salary=D('20000000'), allowance=D('2000000'))
            with self.assertNumQueries(4):
                payroll.calculate(configuration=configuration)
            for field in ('gross_income', 'insurance_amount', 'tax_amount', 'net_income', 'actual_working_days'):
                self.assertEqual(getattr(payroll, field), getattr(reference, field))

    def test_configuration_from_different_period_is_rejected(self):
        configuration = Payroll.load_calculation_configuration(date(2024, 12, 1))
        payroll = Payroll(payroll_period=self.period, employee=self.employee, basic_salary=D('20000000'))
        with self.assertRaises(ValidationError):
            payroll.calculate(configuration=configuration)


class InsuranceCalculationTests(PayrollTestBase):

    def test_bao_hiem_muc_luong_thong_thuong(self):
        """Lương 10 triệu: bảo hiểm = 10.000.000 x 10,5% = 1.050.000."""
        p = self.make_payroll(basic_salary=D("10000000"))
        self.assertEqual(p.insurance_amount, D("1050000"))

    def test_khong_tinh_bao_hiem_tren_tien_tang_ca(self):
        """Tăng ca KHÔNG phải căn cứ đóng bảo hiểm."""
        p = self.make_payroll(basic_salary=D("20000000"), overtime_amount=D("5000000"))
        self.assertEqual(p.gross_income, D("25000000"))
        self.assertEqual(p.insurance_amount, D("2100000"))  # chỉ trên 20 triệu

    def test_khong_tinh_bao_hiem_tren_phu_cap(self):
        """Phụ cấp tính vào Gross nhưng không vào căn cứ đóng bảo hiểm."""
        p = self.make_payroll(basic_salary=D("20000000"), allowance=D("3000000"))
        self.assertEqual(p.gross_income, D("23000000"))
        self.assertEqual(p.insurance_amount, D("2100000"))

    def test_uu_tien_luong_dong_bao_hiem_khai_rieng(self):
        """Khi khai 'Lương đóng bảo hiểm' riêng thì lấy số đó, không lấy lương cơ bản."""
        p = self.make_payroll(basic_salary=D("20000000"), insurance_salary=D("15000000"))
        self.assertEqual(p.insurance_amount, D("1575000"))  # 15tr x 10,5%

    def test_tran_dong_bhxh_bhyt(self):
        """Lương 60 triệu vượt trần 46,8 triệu của BHXH/BHYT, nhưng BHTN vẫn tính trên 60 triệu.

        46.800.000 x 9,5% = 4.446.000  +  60.000.000 x 1% = 600.000  =>  5.046.000
        (Nếu tính sai, không áp trần, sẽ ra 6.300.000)
        """
        p = self.make_payroll(basic_salary=D("60000000"))
        self.assertEqual(p.insurance_amount, D("5046000"))
        self.assertNotEqual(p.insurance_amount, D("6300000"))

    def test_tran_dong_bhtn(self):
        """Lương 120 triệu vượt cả hai trần.

        46.800.000 x 9,5% = 4.446.000  +  99.200.000 x 1% = 992.000  =>  5.438.000
        """
        p = self.make_payroll(basic_salary=D("120000000"))
        self.assertEqual(p.insurance_amount, D("5438000"))

    def test_property_tran_dong(self):
        self.assertEqual(self.insurance_cfg.social_health_cap, D("46800000"))
        self.assertEqual(self.insurance_cfg.unemployment_cap, D("99200000"))
        self.assertEqual(self.insurance_cfg.total_employee_rate, D("10.5"))


# ------------------------------------------------------------------
# 2. THUẾ THU NHẬP CÁ NHÂN
# ------------------------------------------------------------------
class PersonalIncomeTaxTests(PayrollTestBase):

    def test_thu_nhap_thap_khong_phai_nop_thue(self):
        """Lương 10 triệu: sau bảo hiểm và giảm trừ 11 triệu thì còn âm => thuế = 0."""
        p = self.make_payroll(basic_salary=D("10000000"))
        self.assertEqual(p.tax_amount, D("0"))
        self.assertEqual(p.net_income, D("8950000"))

    def test_thue_luy_tien_ba_bac_dau(self):
        """Lương 30 triệu.

        Thu nhập tính thuế = 30.000.000 - 3.150.000 - 11.000.000 = 15.850.000
        Thuế = 5tr x 5% + 5tr x 10% + 5,85tr x 15% = 250.000 + 500.000 + 877.500 = 1.627.500
        """
        p = self.make_payroll(basic_salary=D("30000000"))
        self.assertEqual(p.tax_amount, D("1627500"))
        self.assertEqual(p.net_income, D("25222500"))

    def test_thue_bac_cao_nhat_35_phan_tram(self):
        """Lương 150 triệu — chạm bậc 7.

        Bảo hiểm 5.438.000 => thu nhập tính thuế 133.562.000 => thuế 36.896.700
        """
        p = self.make_payroll(basic_salary=D("150000000"))
        self.assertEqual(p.tax_amount, D("36896700"))
        self.assertEqual(p.net_income, D("107665300"))

    def test_giam_tru_nguoi_phu_thuoc(self):
        """Lương 30 triệu, 2 người phụ thuộc: giảm trừ thêm 8,8 triệu."""
        for i in range(2):
            EmployeeDependent.objects.create(
                employee=self.employee, full_name=f"Con {i}", relationship="Con",
                registered_from=date(2024, 1, 1), is_active=True,
            )
        p = self.make_payroll(basic_salary=D("30000000"))
        self.assertEqual(p.tax_amount, D("455000"))

    def test_bo_qua_nguoi_phu_thuoc_het_hieu_luc(self):
        """Người phụ thuộc đã hết hạn đăng ký thì không được giảm trừ."""
        EmployeeDependent.objects.create(
            employee=self.employee, full_name="Con đã hết hạn", relationship="Con",
            registered_from=date(2023, 1, 1), registered_to=date(2024, 12, 31), is_active=True,
        )
        p = self.make_payroll(basic_salary=D("30000000"))
        self.assertEqual(p.tax_amount, D("1627500"))  # bằng đúng trường hợp không có người phụ thuộc

    def test_tien_tang_ca_mien_thue(self):
        """Phần tăng ca trả cao hơn giờ thường được miễn thuế TNCN.

        Gross 26tr, miễn 2tr, bảo hiểm 2,1tr => tính thuế 10,9tr => thuế 885.000
        """
        p = self.make_payroll(
            basic_salary=D("20000000"), overtime_amount=D("6000000"),
            overtime_tax_exempt_amount=D("2000000"),
        )
        self.assertEqual(p.tax_amount, D("885000"))

    def test_mien_thue_khong_vuot_qua_tien_tang_ca(self):
        """Khai miễn thuế lớn hơn tiền tăng ca thực tế thì chỉ được miễn tối đa bằng tiền tăng ca."""
        p_khai_lo = self.make_payroll(
            basic_salary=D("20000000"), overtime_amount=D("2000000"),
            overtime_tax_exempt_amount=D("99000000"),
        )
        p_khai_dung = self.make_payroll(
            basic_salary=D("20000000"), overtime_amount=D("2000000"),
            overtime_tax_exempt_amount=D("2000000"),
        )
        self.assertEqual(p_khai_lo.tax_amount, p_khai_dung.tax_amount)


# ------------------------------------------------------------------
# 3. THỰC LÃNH & KHẤU TRỪ KHÁC
# ------------------------------------------------------------------
class NetIncomeTests(PayrollTestBase):

    def test_net_bang_gross_tru_het_cac_khoan(self):
        p = self.make_payroll(
            basic_salary=D("30000000"), allowance=D("2000000"), deduction_amount=D("500000")
        )
        self.assertEqual(p.gross_income, D("32000000"))
        self.assertEqual(
            p.net_income,
            p.gross_income - p.insurance_amount - p.tax_amount - p.deduction_amount,
        )

    def test_luong_bang_khong(self):
        p = self.make_payroll(basic_salary=D("0"))
        self.assertEqual(p.gross_income, D("0"))
        self.assertEqual(p.insurance_amount, D("0"))
        self.assertEqual(p.tax_amount, D("0"))
        self.assertEqual(p.net_income, D("0"))


# ------------------------------------------------------------------
# 4. RÀNG BUỘC NGHIỆP VỤ
# ------------------------------------------------------------------
class PayrollGuardTests(PayrollTestBase):

    def test_khong_duoc_sua_bang_luong_cua_ky_da_khoa(self):
        p = self.make_payroll(basic_salary=D("10000000"))
        p.save()
        self.period.status = "Locked"
        self.period.save(update_fields=["status"])
        p.refresh_from_db()
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_bao_loi_khi_thieu_cau_hinh(self):
        """Kỳ lương nằm ngoài khoảng hiệu lực của cấu hình => phải báo lỗi rõ ràng."""
        old_period = PayrollPeriod.objects.create(
            payroll_month=1, payroll_year=2019,
            start_date=date(2019, 1, 1), end_date=date(2019, 1, 31),
        )
        p = Payroll(payroll_period=old_period, employee=self.employee, basic_salary=D("10000000"))
        with self.assertRaises(ValidationError):
            p.calculate()

    def test_moi_nhan_vien_chi_co_mot_bang_luong_moi_ky(self):
        from django.db import IntegrityError, transaction
        self.make_payroll(basic_salary=D("10000000")).save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payroll.objects.create(
                    payroll_period=self.period, employee=self.employee, basic_salary=D("1000000")
                )

    def test_khong_duoc_tao_moi_bang_luong_cho_ky_da_khoa(self):
        """C2 (bug đã sửa): trước đây `clean()` có `and self.pk` nên chỉ chặn SỬA, không chặn
        TẠO MỚI dòng Payroll cho kỳ đã Locked — full_clean() phải raise ngay khi tạo mới."""
        self.period.status = "Locked"
        self.period.save(update_fields=["status"])
        p = Payroll(payroll_period=self.period, employee=self.employee, basic_salary=D("10000000"))
        with self.assertRaises(ValidationError):
            p.full_clean()


# ------------------------------------------------------------------
# 5. C1 — KHÔNG ĐƯỢC TRỘN 2 THẾ HỆ BẬC THUẾ KHI THẾ HỆ CŨ CHƯA ĐÓNG effective_to
# ------------------------------------------------------------------
class TaxBracketGenerationTests(PayrollTestBase):
    """Regression test cho bug C1: nếu ai đó khai 1 bậc thuế của thế hệ mới (effective_from mới)
    mà QUÊN đóng effective_to của thế hệ cũ, calculate() KHÔNG được phép cộng dồn cả 2 thế hệ.

    `setUpTestData` (PayrollTestBase) đã tạo sẵn thế hệ thuế 7 bậc, effective_from=2020-07-01,
    effective_to=NULL (chưa đóng) — đúng kịch bản thực tế gây lỗi.
    """

    def test_chi_lay_dung_1_the_he_bac_thue_theo_effective_from_moi_nhat(self):
        # Thêm 1 bậc thuế của thế hệ MỚI (hiệu lực từ 2026-01-01) — CỐ TÌNH không đóng
        # effective_to của thế hệ cũ, y hệt kịch bản gây bug C1 trong thực tế.
        PersonalIncomeTaxBracket.objects.create(
            effective_from=date(2026, 1, 1),
            bracket_no=1,
            income_from_monthly=D("0"),
            income_to_monthly=None,
            tax_rate=D("2"),
        )
        new_period = PayrollPeriod.objects.create(
            payroll_month=3, payroll_year=2026,
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31),
            status="Open",
        )
        p = Payroll(payroll_period=new_period, employee=self.employee, basic_salary=D("50000000"))
        p.calculate()
        # Thế hệ mới CHỈ có đúng 1 bậc (2% không giới hạn) — nếu calculate() lẫn cả 7 bậc cũ vào,
        # thuế sẽ áp theo biểu lũy tiến 7 bậc (sai). Nếu đúng, thuế phải được tính theo ĐÚNG 1 bậc
        # 2% của thế hệ mới trên toàn bộ thu nhập chịu thuế.
        taxable = p.gross_income - p.insurance_amount - D("11000000")  # không có người phụ thuộc
        expected_tax = (taxable * D("2") / D("100")).quantize(D("1"))
        self.assertEqual(p.tax_amount, expected_tax)


class PartialMonthSalaryTests(PayrollTestBase):
    """I6 regressions: calculate() prorates salary to actual employment workdays."""

    def _assert_prorated_for_employment_window(self, **employee_dates):
        from apps.attendance.services import standard_working_days

        for field, value in employee_dates.items():
            setattr(self.employee, field, value)
        self.employee.save(update_fields=list(employee_dates))

        payroll = Payroll(
            payroll_period=self.period, employee=self.employee,
            basic_salary=D("23000000"), allowance=D("2000000"),
        )
        payroll.calculate()

        standard_days = standard_working_days(self.period.start_date, self.period.end_date)
        present_from = max(self.period.start_date, self.employee.join_date)
        present_to = min(
            self.period.end_date,
            self.employee.leave_date or self.period.end_date,
        )
        present_days = standard_working_days(present_from, present_to)
        ratio = present_days / standard_days
        expected_gross = (
            (D("23000000") * ratio).quantize(D("1"), rounding=ROUND_HALF_UP)
            + (D("2000000") * ratio).quantize(D("1"), rounding=ROUND_HALF_UP)
        )
        self.assertEqual(payroll.actual_working_days, present_days)
        self.assertEqual(payroll.gross_income, expected_gross)
        self.assertLess(payroll.gross_income, D("25000000"))

    def test_new_hire_mid_month_receives_prorated_salary(self):
        self._assert_prorated_for_employment_window(join_date=date(2025, 1, 15))

    def test_employee_leaving_mid_month_receives_prorated_salary(self):
        self._assert_prorated_for_employment_window(leave_date=date(2025, 1, 15))
