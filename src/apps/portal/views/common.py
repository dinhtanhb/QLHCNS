from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from apps.security.permissions import get_role_code
from django.contrib import messages
from apps.hrm.models import Employee
import logging
logger = logging.getLogger(__name__)




def _paginate(request, queryset, per_page=20, param="page"):
    """Phân trang chung cho các danh sách dài — mục 3.F.

    Trả về đối tượng Page để dùng thẳng trong template (has_next, has_previous,
    number, paginator.num_pages...).
    """
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(param) or 1
    try:
        return paginator.page(page_number)
    except Exception:
        return paginator.page(1)


def _friendly_error(request, exc, user_message, log_context=""):
    """Log lỗi kỹ thuật ở server, chỉ hiển thị thông báo thân thiện cho người dùng.

    Mục 3.D: trước đây rất nhiều `except Exception as e` show thẳng
    `f"...: {e}"` (lỗi kỹ thuật gốc) ra UI cho người dùng cuối.
    """
    logger.exception("Lỗi khi xử lý %s (user=%s): %s", log_context or request.path, request.user, exc)
    if isinstance(exc, ValidationError):
        # Lỗi validate dữ liệu (full_clean) vẫn nên cho người dùng biết cụ thể sai ở đâu.
        detail = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        messages.error(request, f"{user_message} ({detail})")
    else:
        messages.error(request, user_message)


def _director_employees():
    return Employee.objects.filter(position__position_name__icontains="Giám đốc", employment_status="Active")


def _get_employee(request):
    return getattr(request.user, "employee", None)


def _role_code(request):
    return get_role_code(request.user)


def _employees_with_permission(permission):
    """Các nhân viên có tài khoản mang vai trò được cấp `permission` (theo PERMISSION_MATRIX).

    Dùng để tìm người cần nhận thông báo/duyệt cho các nghiệp vụ không có một
    người duyệt cố định (đặt phòng, đặt xe, VPP, mua sắm...).
    """
    from apps.security.permissions import PERMISSION_MATRIX
    role_codes = PERMISSION_MATRIX.get(permission, ())
    if not role_codes:
        return Employee.objects.none()
    return Employee.objects.filter(
        user_account__role__role_code__in=role_codes, employment_status="Active",
    ).distinct()

DIRECTOR_TITLE_KEYWORDS = ["Giám đốc"]
