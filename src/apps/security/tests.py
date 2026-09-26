"""Kiểm thử phân quyền: ma trận quyền và chặn truy cập trái phép.

Chạy:  python manage.py test apps.security

Mục đích: mỗi khi sửa file apps/security/permissions.py, bộ test này bảo đảm
không vô tình "nới tay" cho nhân viên thường vào những nơi không được phép.
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.document.models import DispatchBook, OfficialDispatch
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User
from apps.security.permissions import (
    DEPT_MANAGER,
    DIRECTOR,
    EMPLOYEE,
    FINANCE_OFFICER,
    HR_MANAGER,
    HR_OFFICER,
    PERMISSION_MATRIX,
    PROJECT_COORDINATOR,
    PROJECT_MANAGER,
    CBDA,
    STAFF_ALSO_ALLOWED,
    SYS_ADMIN,
    has_permission,
    permission_flags,
)


# ==================================================================
# PHẦN 1 — MA TRẬN QUYỀN (chạy rất nhanh, không đụng giao diện)
# ==================================================================
class PermissionMatrixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.roles = {
            code: Role.objects.get_or_create(role_code=code, defaults={"role_name": code})[0]
            for code in (
                EMPLOYEE, DEPT_MANAGER, HR_MANAGER, HR_OFFICER, DIRECTOR,
                FINANCE_OFFICER, SYS_ADMIN, PROJECT_MANAGER, PROJECT_COORDINATOR, CBDA,
            )
        }
        cls.users = {
            code: User.objects.create_user(username=f"u_{code}", password="x", role=role)
            for code, role in cls.roles.items()
        }
        cls.superuser = User.objects.create_superuser(username="admin", password="x", email="a@a.com")
        cls.no_role = User.objects.create_user(username="chua_gan_vai_tro", password="x")

    # ---------- Nhân viên thường ----------
    def test_nhan_vien_thuong_chi_co_quyen_tu_phuc_vu(self):
        user = self.users[EMPLOYEE]
        for permission in PERMISSION_MATRIX:
            expected_self_service = permission in {
                "submit_profile_change_request",
            }
            self.assertEqual(
                has_permission(user, permission), expected_self_service,
                f"Unexpected employee permission '{permission}'",
            )
        self.assertFalse(has_permission(user, "approve_profile_change_request"))
        self.assertFalse(has_permission(user, "manage_lifecycle_case"))

    def test_tai_khoan_chua_gan_vai_tro_khong_co_quyen_nao(self):
        for permission in PERMISSION_MATRIX:
            self.assertFalse(has_permission(self.no_role, permission))

    # ---------- Trung tâm báo cáo ----------
    def test_trung_tam_bao_cao(self):
        for code in (DIRECTOR, HR_MANAGER, HR_OFFICER, FINANCE_OFFICER, SYS_ADMIN):
            self.assertTrue(has_permission(self.users[code], "view_report_center"), code)
        for code in (EMPLOYEE, DEPT_MANAGER):
            self.assertFalse(has_permission(self.users[code], "view_report_center"), code)

    def test_co_is_staff_khong_du_de_vao_trung_tam_bao_cao(self):
        """Lỗi cũ: cứ tick 'Staff status' là vào được /reports/. Không được phép tái diễn."""
        user = self.users[EMPLOYEE]
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        self.assertFalse(has_permission(user, "view_report_center"))
        self.assertNotIn("view_report_center", STAFF_ALSO_ALLOWED)

    # ---------- Văn thư ----------
    def test_cong_van_den_chi_danh_cho_nhan_su_va_quan_tri(self):
        for code in (HR_MANAGER, HR_OFFICER, SYS_ADMIN):
            self.assertTrue(has_permission(self.users[code], "manage_office"), code)
        for code in (EMPLOYEE, DEPT_MANAGER, DIRECTOR, FINANCE_OFFICER):
            self.assertFalse(has_permission(self.users[code], "manage_office"), code)

    def test_cong_van_di_moi_vai_tro_tru_nhan_vien(self):
        for code in (
            DEPT_MANAGER, DIRECTOR, HR_MANAGER, HR_OFFICER, FINANCE_OFFICER,
            SYS_ADMIN, PROJECT_MANAGER, PROJECT_COORDINATOR,
        ):
            self.assertTrue(has_permission(self.users[code], "access_outgoing_document"), code)
        self.assertFalse(has_permission(self.users[EMPLOYEE], "access_outgoing_document"))

    # ---------- Nghỉ phép ----------
    def test_duyet_nghi_phep_toan_cong_ty(self):
        for code in (HR_MANAGER, DIRECTOR):
            self.assertTrue(has_permission(self.users[code], "approve_leave_all_departments"), code)
        self.assertTrue(has_permission(self.users[DEPT_MANAGER], "approve_leave"))
        self.assertFalse(has_permission(self.users[DEPT_MANAGER], "approve_leave_all_departments"))
        self.assertFalse(has_permission(self.users[EMPLOYEE], "approve_leave"))

    def test_lifecycle_checklists_are_limited_to_hr_and_system_admin(self):
        for code in (DIRECTOR, PROJECT_MANAGER, PROJECT_COORDINATOR, CBDA):
            self.assertFalse(has_permission(self.users[code], "view_own_lifecycle_items"), code)
            self.assertFalse(has_permission(self.users[code], "manage_lifecycle_case"), code)
        for code in (HR_OFFICER, HR_MANAGER):
            self.assertTrue(has_permission(self.users[code], "view_own_lifecycle_items"), code)
        for code in (EMPLOYEE, SYS_ADMIN):
            self.assertFalse(has_permission(self.users[code], "view_own_lifecycle_items"), code)

    # ---------- Superuser ----------
    def test_superuser_co_moi_quyen(self):
        for permission in PERMISSION_MATRIX:
            self.assertTrue(has_permission(self.superuser, permission))

    def test_permission_flags_tra_ve_du_co_cho_giao_dien(self):
        flags = permission_flags(self.users[EMPLOYEE])
        self.assertEqual(set(flags), {f"can_{name}" for name in PERMISSION_MATRIX})
        enabled = {name for name, allowed in flags.items() if allowed}
        self.assertEqual(enabled, {"can_submit_profile_change_request"})


# ==================================================================
# PHẦN 2 — CHẶN TRUY CẬP THỰC TẾ TRÊN GIAO DIỆN
# ==================================================================
class AccessControlViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="ORG", organization_name="Công ty Thử Nghiệm")
        cls.dept_it = Department.objects.create(
            department_code="IT", department_name="Công nghệ thông tin", organization=org
        )
        cls.dept_hc = Department.objects.create(
            department_code="HC", department_name="Hành chính", organization=org
        )
        position = Position.objects.create(position_code="NV", position_name="Nhân viên")

        def make_employee(code, dept):
            return Employee.objects.create(
                employee_code=code, first_name="A", last_name="Nguyễn", full_name=f"Nhân viên {code}",
                date_of_birth=date(1990, 1, 1), gender="Male", national_id=f"0790{code}",
                company_email=f"{code.lower()}@example.com", mobile_phone="0900000000",
                join_date=date(2020, 1, 1), department=dept, position=position,
            )

        cls.emp_it = make_employee("NV001", cls.dept_it)
        cls.emp_hr = make_employee("NV002", cls.dept_hc)

        role_employee = Role.objects.create(role_code=EMPLOYEE, role_name="Nhân viên")
        role_hr = Role.objects.create(role_code=HR_MANAGER, role_name="Trưởng phòng Nhân sự")

        cls.user_employee = User.objects.create_user(
            username="nhanvien", password="matkhau123", role=role_employee, employee=cls.emp_it
        )
        cls.user_hr = User.objects.create_user(
            username="nhansu", password="matkhau123", role=role_hr, employee=cls.emp_hr
        )

        book = DispatchBook.objects.create(
            book_code="S01", book_name="Sổ công văn đến 2025", book_type="Incoming", year=2025
        )
        cls.dispatch_it = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=book, dispatch_no="01/CV",
            title="Công văn của phòng IT", issuing_organization="Sở A",
            issue_date=date(2025, 1, 2), received_or_sent_date=date(2025, 1, 3),
            department=cls.dept_it,
        )
        cls.dispatch_khac = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=book, dispatch_no="02/CV",
            title="Công văn của phòng Hành chính", issuing_organization="Sở B",
            issue_date=date(2025, 1, 4), received_or_sent_date=date(2025, 1, 5),
            department=cls.dept_hc,
        )

    def login_employee(self):
        self.client.login(username="nhanvien", password="matkhau123")

    def login_hr(self):
        self.client.login(username="nhansu", password="matkhau123")

    # ---------- Trung tâm báo cáo ----------
    def test_nhan_vien_bi_chan_vao_trung_tam_bao_cao(self):
        self.login_employee()
        response = self.client.get("/reports/")
        self.assertEqual(response.status_code, 403)  # bị từ chối truy cập

    def test_nhan_su_vao_duoc_trung_tam_bao_cao(self):
        self.login_hr()
        self.assertEqual(self.client.get("/reports/").status_code, 200)

    # ---------- Chi tiết công văn (lỗ hổng IDOR) ----------
    def test_xem_duoc_cong_van_cua_phong_minh(self):
        self.login_employee()
        url = reverse("portal:dispatch_detail", args=[self.dispatch_it.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_khong_xem_duoc_cong_van_cua_phong_khac(self):
        """Đổi số trên URL phải ra 404, không được lộ nội dung."""
        self.login_employee()
        url = reverse("portal:dispatch_detail", args=[self.dispatch_khac.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_nhan_su_xem_duoc_moi_cong_van(self):
        self.login_hr()
        for dispatch in (self.dispatch_it, self.dispatch_khac):
            url = reverse("portal:dispatch_detail", args=[dispatch.pk])
            self.assertEqual(self.client.get(url).status_code, 200)

    # ---------- Công văn ----------
    def test_nhan_vien_khong_tao_duoc_cong_van(self):
        self.login_employee()
        self.client.post(reverse("portal:dispatch_create"), {
            "dispatch_type": "Incoming", "dispatch_no": "CVD-001",
            "issue_date": "2025-01-10", "received_or_sent_date": "2025-01-10",
            "title": "Thử tạo trái phép", "issuing_organization": "Sở A",
        })
        self.assertFalse(OfficialDispatch.objects.filter(dispatch_no="CVD-001").exists())

    def test_nhan_su_tao_duoc_cong_van(self):
        self.login_hr()
        self.client.post(reverse("portal:dispatch_create"), {
            "dispatch_type": "Incoming", "dispatch_no": "CVD-002",
            "issue_date": "2025-01-10", "received_or_sent_date": "2025-01-10",
            "title": "Công văn hợp lệ", "issuing_organization": "Sở A",
        })
        self.assertTrue(OfficialDispatch.objects.filter(dispatch_no="CVD-002").exists())

    def test_moi_nhan_vien_deu_xem_duoc_so_cong_van(self):
        self.login_employee()
        self.assertEqual(self.client.get(reverse("portal:dispatch_list")).status_code, 200)

    # ---------- Chưa đăng nhập ----------
    def test_chua_dang_nhap_bi_day_ve_trang_dang_nhap(self):
        for url in ("/reports/", reverse("portal:dispatch_create"), reverse("portal:dispatch_list")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("login", response["Location"])
