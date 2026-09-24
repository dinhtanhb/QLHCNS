"""Ma trận phân quyền của toàn hệ thống — khai báo DUY NHẤT tại đây.

Trước đây quyền được viết rải rác ở hai nơi (apps/portal/views.py và
apps/portal/context_processors.py) với danh sách vai trò lặp lại, nên sửa một
chỗ mà quên chỗ kia là menu và trang thực tế lệch nhau.

Muốn thay đổi ai được làm gì, CHỈ sửa bảng PERMISSION_MATRIX bên dưới.
"""

# ------------------------------------------------------------------
# Mã vai trò (khớp với Role.role_code trong CSDL)
# ------------------------------------------------------------------
SUPER_ADMIN = "SUPER_ADMIN"
SYS_ADMIN = "SYS_ADMIN"
DIRECTOR = "DIRECTOR"
HR_MANAGER = "HR_MANAGER"
HR_OFFICER = "HR_OFFICER"
DEPT_MANAGER = "DEPT_MANAGER"
FINANCE_OFFICER = "FINANCE_OFFICER"
EMPLOYEE = "EMPLOYEE"

# ------------------------------------------------------------------
# AI ĐƯỢC LÀM GÌ — bảng duy nhất, sửa ở đây là áp dụng toàn hệ thống
# ------------------------------------------------------------------
PERMISSION_MATRIX = {
    # Nghỉ phép
    "approve_leave": (HR_MANAGER, DEPT_MANAGER, DIRECTOR),
    # Duyệt đơn của MỌI phòng ban (vai trò khác chỉ duyệt trong phòng mình quản lý)
    "approve_leave_all_departments": (HR_MANAGER, DIRECTOR),
    # I3: duyệt Tổng hợp chấm công tháng (số ngày ốm/thai sản/nghỉ bù/phép năm/không lương
    # nhân viên tự khai) trước khi số liệu này được payroll và báo cáo BCC sử dụng.
    "approve_timesheet": (HR_MANAGER, DEPT_MANAGER, DIRECTOR),
    "approve_timesheet_all_departments": (HR_MANAGER, DIRECTOR),
    # Công việc
    "assign_task": (HR_MANAGER, DEPT_MANAGER),
    # KPI
    "score_kpi": (HR_MANAGER, DEPT_MANAGER),
    # Tài liệu & công văn
    "approve_document": (HR_MANAGER, DIRECTOR),
    # Tuyển dụng
    "request_recruitment": (DEPT_MANAGER, HR_MANAGER),
    "approve_recruitment": (HR_MANAGER,),
    # Lịch làm việc, ngày lễ
    "manage_calendar": (HR_MANAGER, SYS_ADMIN),
    # Sự kiện
    "create_event": (HR_MANAGER, DEPT_MANAGER),
    # Báo cáo trong cổng thông tin
    "view_reports": (HR_MANAGER, DIRECTOR),
    # Nhân sự
    "manage_hr": (HR_MANAGER, HR_OFFICER),
    "view_all_employees": (HR_MANAGER, HR_OFFICER, DIRECTOR),
    # Tài chính, bảng lương
    "manage_finance": (FINANCE_OFFICER,),
    # Văn thư: công văn đến, phân công xử lý — chỉ Nhân sự và Quản trị hệ thống
    "manage_office": (HR_MANAGER, HR_OFFICER, SYS_ADMIN),
    # Sổ công văn đi — mọi vai trò TRỪ nhân viên thường
    "access_outgoing_document": (
        SUPER_ADMIN, SYS_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER,
        DEPT_MANAGER, FINANCE_OFFICER,
    ),
    # Duyệt đặt phòng họp/đặt xe/đề nghị VPP — dùng chung quyền với "manage_office"
    "approve_office_request": (HR_MANAGER, HR_OFFICER, SYS_ADMIN),
    # Đề nghị & duyệt mua sắm
    "request_procurement": (HR_MANAGER, HR_OFFICER, DEPT_MANAGER, FINANCE_OFFICER, SYS_ADMIN),
    "approve_procurement": (FINANCE_OFFICER, DIRECTOR),
    # Tài sản, kiểm kê, thanh lý
    "manage_asset": (HR_MANAGER, HR_OFFICER, SYS_ADMIN),
    # Trung tâm Báo cáo (/reports/) — chỉ Ban giám đốc, Nhân sự, Kế toán và Quản trị
    "view_report_center": (SUPER_ADMIN, SYS_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER, FINANCE_OFFICER),
    # Hiện menu quản trị
    "view_admin_menu": (SUPER_ADMIN, SYS_ADMIN, HR_MANAGER, DIRECTOR),
}

# Những quyền mà tài khoản có cờ "nhân viên quản trị" (is_staff) cũng được dùng.
# Chỉ để cờ is_staff ở đây với menu quản trị, vì is_staff là điều kiện Django dùng
# để cho vào trang /admin/. Các quyền nghiệp vụ KHÔNG dựa vào is_staff, phải khai
# rõ vai trò trong PERMISSION_MATRIX ở trên.
STAFF_ALSO_ALLOWED = {"view_admin_menu"}


# ------------------------------------------------------------------
# Hàm tra cứu
# ------------------------------------------------------------------
def get_role_code(user):
    """Mã vai trò của tài khoản, None nếu chưa gán vai trò."""
    role = getattr(user, "role", None)
    return role.role_code if role else None


def get_role_name(user):
    role = getattr(user, "role", None)
    if role:
        return role.role_name
    if getattr(user, "is_superuser", False):
        return "Quản trị viên cấp cao"
    if getattr(user, "is_staff", False):
        return "Quản trị viên"
    return "Nhân viên"


def has_permission(user, permission):
    """Tài khoản có quyền này không. Superuser luôn có mọi quyền."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if permission in STAFF_ALSO_ALLOWED and getattr(user, "is_staff", False):
        return True
    return get_role_code(user) in PERMISSION_MATRIX.get(permission, ())


def permission_flags(user):
    """Toàn bộ quyền dưới dạng can_<tên quyền> để dùng trong template."""
    return {f"can_{name}": has_permission(user, name) for name in PERMISSION_MATRIX}
