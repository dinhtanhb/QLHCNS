from django.core.exceptions import ValidationError
from django.urls import reverse
import re
from django.db import IntegrityError, models, transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.db.models import Exists, OuterRef, Q, Subquery
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.notification.services import notify
from django.http import HttpResponseForbidden
from apps.hrm.models import EmployeePromotion, EmployeeTransfer
from apps.organization.models import Department
from apps.hrm.models import EmployeeDiscipline, EmployeeReward
from apps.contract.models import Contract, ContractAppendix, ContractType
from apps.organization.models import JobTitle
from apps.payroll.models import EmployeeSalary
from django.utils import timezone
from apps.hrm.models import Employee
from apps.organization.models import Position
from .common import _friendly_error, _get_employee, _role_code, _paginated_context, _status_tabs
from .finance import _can_manage_finance, _day_before




def _can_manage_hr(request):
    return has_permission(request.user, "manage_hr")


def _can_draft_hr(request):
    return all(has_permission(request.user, permission) for permission in
               ("export_employee_data", "view_all_employees", "view_employee_compensation"))


def _save_history(model, **values):
    obj = model(**values)
    obj.full_clean()
    obj.save()
    return obj


def _employee_scope(request):
    """Trả về queryset Employee theo đúng quyền xem của tài khoản đang đăng nhập."""
    if has_permission(request.user, "view_all_employees"):
        return Employee.objects.all()
    if _role_code(request) == "DEPT_MANAGER":
        employee = _get_employee(request)
        if not employee:
            return Employee.objects.none()
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        return Employee.objects.filter(department_id__in=dept_ids)
    return Employee.objects.none()


@login_required
def hr_employee_list(request):
    q = request.GET.get("q", "").strip()
    # The directory contains contracted employees. Keep the broader scope for
    # contract creation/detail so initial registration never becomes a dead end.
    contracts = Contract.objects.filter(employee_id=OuterRef("pk"))
    # Phương án B: danh sách cần cột "Loại hợp đồng" nên lấy loại của hợp đồng
    # mới nhất bằng subquery — một truy vấn, không N+1 theo từng dòng.
    latest_contract = Contract.objects.filter(employee_id=OuterRef("pk")).order_by("-start_date", "-pk")
    employees = (
        _employee_scope(request)
        .filter(Exists(contracts))
        .select_related("department", "position")
        .annotate(current_contract_type=Subquery(latest_contract.values("contract_type__contract_type_name")[:1]))
        .order_by("full_name")
    )
    if q:
        employees = employees.filter(models.Q(full_name__icontains=q) | models.Q(employee_code__icontains=q))
    return render(request, "portal/hr_employee_list.html", {
        **_paginated_context(request, employees.order_by('full_name', 'pk'), 'employees'),
        "q": q, "can_manage_hr": _can_manage_hr(request), "can_draft_hr": _can_draft_hr(request),
    })


@login_required
def hr_employee_detail(request, pk):
    employee = get_object_or_404(_employee_scope(request), pk=pk)
    sensitive = has_permission(request.user, 'view_employee_compensation')
    return render(request, "portal/hr_employee_detail.html", {
        "employee": employee, "can_manage_hr": _can_manage_hr(request), "can_draft_hr": _can_draft_hr(request),
        "contracts": employee.contracts.select_related("contract_type").prefetch_related("appendices").order_by("-start_date") if sensitive else [],
        "current_contract": employee.contracts.order_by("-start_date").first() if sensitive else None,
        "transfers": employee.transfers.select_related("from_department", "to_department"),
        "promotions": employee.promotions.select_related("old_position", "new_position"),
        "rewards": employee.rewards.all(),
        "disciplines": employee.disciplines.all(),
        "salaries": employee.salaries.order_by("-effective_date") if sensitive else [],
        "departments": Department.objects.filter(is_active=True),
        "positions": Position.objects.all(),
    })


def _save_employee_form(request, employee, *, employee_code=None):
    employee.employee_code = employee_code or request.POST.get("employee_code")
    employee.first_name = request.POST.get("first_name")
    employee.last_name = request.POST.get("last_name")
    employee.full_name = request.POST.get("full_name")
    employee.date_of_birth = request.POST.get("date_of_birth")
    employee.gender = request.POST.get("gender")
    employee.national_id = request.POST.get("national_id")
    employee.tax_code = request.POST.get("tax_code", "")
    employee.social_insurance_no = request.POST.get("social_insurance_no", "")
    employee.personal_email = request.POST.get("personal_email", "")
    employee.company_email = request.POST.get("company_email")
    employee.mobile_phone = request.POST.get("mobile_phone")
    employee.address = request.POST.get("address", "")
    employee.join_date = request.POST.get("join_date")
    employee.leave_date = request.POST.get("leave_date") or None
    employee.department_id = request.POST.get("department")
    employee.position_id = request.POST.get("position")
    employee.job_title_id = request.POST.get("job_title") or None
    employee.manager_id = request.POST.get("manager") or None
    employee.employment_status = request.POST.get("employment_status", "Active")
    employee.full_clean()
    employee.save()


@login_required
def hr_employee_create(request):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền quản lý hồ sơ nhân viên.")
        return redirect("portal:hr_employee_list")

    if request.method == "POST":
        try:
            requested_code = (request.POST.get("employee_code") or "").strip()
            employee = None
            for attempt in range(3):
                candidate_code = requested_code if attempt == 0 else _generate_next_employee_code()
                try:
                    with transaction.atomic():
                        employee = Employee(created_by=request.user)
                        _save_employee_form(
                            request, employee, employee_code=candidate_code
                        )
                    break
                except ValidationError as error:
                    code_collision = bool(
                        re.fullmatch(r"VH\d{4,}", candidate_code)
                        and "employee_code" in getattr(error, "message_dict", {})
                        and Employee.objects.filter(employee_code=candidate_code).exists()
                    )
                    if not code_collision or attempt == 2:
                        raise
                except IntegrityError:
                    if not re.fullmatch(r"VH\d{4,}", candidate_code) or attempt == 2:
                        raise
            if employee is None or employee.pk is None:
                raise ValidationError("Không thể sinh mã nhân viên duy nhất sau 3 lần thử.")
            messages.success(request, "Đã tạo hồ sơ nhân viên mới.")
            return redirect("portal:hr_employee_detail", pk=employee.pk)
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo hồ sơ.")

    initial_fields = (
        "employee_code", "first_name", "last_name", "full_name",
        "personal_email", "mobile_phone", "address", "join_date",
    )
    initial = {field: request.GET.get(field, "") for field in initial_fields}
    if not initial.get("employee_code"):
        initial["employee_code"] = _generate_next_employee_code()
    return render(request, "portal/hr_employee_form.html", {
        "employee": None, "initial": initial,
        "departments": Department.objects.filter(is_active=True), "positions": Position.objects.all(),
        "job_titles": JobTitle.objects.all(), "managers": Employee.objects.filter(employment_status="Active"),
    })


@login_required
def hr_employee_edit(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền quản lý hồ sơ nhân viên.")
        return redirect("portal:hr_employee_list")

    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        try:
            employee.modified_by = request.user
            _save_employee_form(request, employee)
            messages.success(request, "Đã cập nhật hồ sơ nhân viên.")
            return redirect("portal:hr_employee_detail", pk=employee.pk)
        except Exception as e:
            _friendly_error(request, e, "Không thể cập nhật.")

    initial = {
        field: "" for field in (
            "employee_code", "first_name", "last_name", "full_name",
            "personal_email", "mobile_phone", "address", "join_date",
        )
    }
    return render(request, "portal/hr_employee_form.html", {
        "employee": employee, "initial": initial,
        "departments": Department.objects.filter(
            Q(is_active=True) | Q(pk=employee.department_id)
        ),
        "current_department_inactive": not employee.department.is_active,
        "positions": Position.objects.all(),
        "job_titles": JobTitle.objects.all(),
        "managers": Employee.objects.filter(employment_status="Active").exclude(pk=employee.pk),
    })


@login_required
@require_POST
def hr_employee_history_create(request, pk, history_type):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền thực hiện thao tác này.")
        return redirect("portal:hr_employee_list")

    employee = get_object_or_404(Employee, pk=pk)
    try:
        if history_type == "transfer":
            transfer = _save_history(EmployeeTransfer,
                employee=employee, from_department=employee.department,
                to_department_id=request.POST.get("to_department"),
                effective_date=request.POST.get("effective_date"),
                reason=request.POST.get("reason", ""), created_by=request.user,
            )
            notify(
                employee, "hr", "Bạn có quyết định điều chuyển",
                f"Điều chuyển từ {transfer.from_department} sang {transfer.to_department}, hiệu lực {transfer.effective_date}.",
                link=f"/portal/hr/employees/{pk}/", created_by=request.user,
            )
            messages.success(request, "Đã ghi nhận điều chuyển. Phòng ban được cập nhật theo ngày hiệu lực.")
        elif history_type == "promotion":
            promotion = _save_history(EmployeePromotion,
                employee=employee, old_position=employee.position,
                new_position_id=request.POST.get("new_position"),
                effective_date=request.POST.get("effective_date"),
                reason=request.POST.get("reason", ""), created_by=request.user,
            )
            notify(
                employee, "hr", "Bạn có quyết định bổ nhiệm/thăng chức",
                f"Từ {promotion.old_position} lên {promotion.new_position}, hiệu lực {promotion.effective_date}.",
                link=f"/portal/hr/employees/{pk}/", created_by=request.user,
            )
            messages.success(request, "Đã ghi nhận bổ nhiệm/thăng chức. Vị trí được cập nhật theo ngày hiệu lực.")
        elif history_type == "reward":
            reward = _save_history(EmployeeReward,
                employee=employee, reward_type=request.POST.get("reward_type"),
                reward_date=request.POST.get("reward_date"),
                amount=request.POST.get("amount") or None,
                description=request.POST.get("description", ""), created_by=request.user,
            )
            notify(
                employee, "hr", "Bạn nhận được khen thưởng",
                f"{reward.reward_type} ngày {reward.reward_date}.",
                link=f"/portal/hr/employees/{pk}/", created_by=request.user,
            )
            messages.success(request, "Đã ghi nhận khen thưởng.")
        elif history_type == "discipline":
            discipline = _save_history(EmployeeDiscipline,
                employee=employee, discipline_type=request.POST.get("discipline_type"),
                discipline_date=request.POST.get("discipline_date"),
                description=request.POST.get("description", ""), created_by=request.user,
            )
            notify(
                employee, "hr", "Bạn có quyết định kỷ luật",
                f"{discipline.discipline_type} ngày {discipline.discipline_date}.",
                link=f"/portal/hr/employees/{pk}/", created_by=request.user,
            )
            messages.success(request, "Đã ghi nhận kỷ luật.")
        else:
            raise ValidationError("Thao tác nhân sự không hợp lệ.")
        if request.POST.get("next") == "hcns" and _can_draft_hr(request) and history_type in ("transfer", "promotion"):
            record = transfer if history_type == "transfer" else promotion
            slug = "salary-decision" if history_type == "transfer" else "appointment-decision"
            return redirect(reverse("portal:hcns_draft", args=[slug]) + f"?{history_type}_id={record.pk}")
    except Exception as e:
        _friendly_error(request, e, "Không thể lưu.")
    return redirect("portal:hr_employee_detail", pk=pk)


@login_required
def hr_contract_list(request):
    if not _can_manage_hr(request):
        return HttpResponseForbidden("Bạn không có quyền xem danh sách hợp đồng nhân sự.")
    contracts = Contract.objects.select_related("employee", "contract_type")
    # Tab trạng thái dựng trên toàn bộ hợp đồng trong phạm vi, trước khi lọc,
    # để số trên tab là phân bố thật của từng trạng thái.
    status_tabs = _status_tabs(request, contracts, Contract.STATUS_CHOICES)
    selected_status = request.GET.get("status", "")
    if selected_status:
        contracts = contracts.filter(status=selected_status)
    return render(request, "portal/hr_contract_list.html", {
        "contracts": contracts.order_by("-start_date"),
        "status_tabs": status_tabs,
        "selected_status": selected_status,
        "can_manage_hr": _can_manage_hr(request),
    })


@login_required
def hr_contract_create(request):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền quản lý hợp đồng.")
        return redirect("portal:hr_contract_list")

    if request.method == "POST":
        try:
            contract = Contract(
                employee_id=request.POST.get("employee"),
                contract_type_id=request.POST.get("contract_type"),
                contract_no=request.POST.get("contract_no"),
                start_date=request.POST.get("start_date"),
                end_date=request.POST.get("end_date") or None,
                basic_salary=request.POST.get("basic_salary"),
                status=request.POST.get("status", "Draft"),
                created_by=request.user,
            )
            contract.full_clean()
            contract.save()
            notify(
                contract.employee, "contract", "Bạn có hợp đồng lao động mới",
                f"Hợp đồng {contract.contract_no}, hiệu lực từ {contract.start_date}.",
                link=f"/portal/hr/employees/{contract.employee_id}/#hopdong", created_by=request.user,
            )
            messages.success(request, "Đã tạo hợp đồng.")
            return redirect("portal:hr_contract_list")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo hợp đồng.")

    context = {
        "employees": Employee.objects.filter(employment_status__in=["Active", "Probation"]),
        "contract_types": ContractType.objects.all(),
        "selected_employee": request.POST.get("employee") or request.GET.get("employee_id", ""),
    }
    # Cột ngữ cảnh của biểu mẫu hai cột: khi đã chọn nhân viên (từ nút "Tạo hợp
    # đồng" trên hồ sơ), hiện luôn hồ sơ tóm tắt và hợp đồng gần nhất để người
    # nhập biết mình đang nối tiếp hợp đồng nào thay vì phải mở tab khác.
    try:
        employee_id = int(context["selected_employee"])
    except (TypeError, ValueError):
        employee_id = None
    if employee_id:
        rail_employee = (
            Employee.objects.select_related("department", "position").filter(pk=employee_id).first()
        )
        if rail_employee:
            context["rail_employee"] = rail_employee
            context["rail_current_contract"] = (
                rail_employee.contracts.select_related("contract_type").order_by("-start_date").first()
            )
    return render(request, "portal/hr_contract_form.html", context)


@login_required
@require_POST
def hr_contract_appendix_create(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền quản lý hợp đồng.")
        return redirect("portal:hr_contract_list")
    contract = get_object_or_404(Contract, pk=pk)
    try:
        appendix = _save_history(ContractAppendix,
            contract=contract, appendix_no=request.POST.get("appendix_no"),
            effective_date=request.POST.get("effective_date"),
            description=request.POST.get("description", ""), created_by=request.user,
        )
        notify(
            contract.employee, "contract", "Hợp đồng của bạn có phụ lục mới",
            f"Phụ lục {appendix.appendix_no} - {appendix.description or contract.contract_no}.",
            link=f"/portal/hr/employees/{contract.employee_id}/#hopdong", created_by=request.user,
        )
        messages.success(request, "Đã thêm phụ lục hợp đồng.")
    except Exception as e:
        _friendly_error(request, e, "Không thể thêm phụ lục.")
    return redirect("portal:hr_employee_detail", pk=contract.employee_id)


def _generate_next_employee_code():
    max_num = 0
    for code in Employee.objects.values_list("employee_code", flat=True):
        m = re.match(r"^VH(\d+)$", code or "")
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"VH{max_num + 1:04d}"


@login_required
@require_POST
def hr_salary_create(request, pk):
    if not (_can_manage_hr(request) or _can_manage_finance(request)):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_employee_detail", pk=pk)
    employee = get_object_or_404(Employee, pk=pk)
    try:
        effective_date = request.POST.get("effective_date")
        # transaction.atomic() + select_for_update(): tránh 2 người cùng bấm "nâng lương"
        # cho 1 nhân viên cùng lúc tạo ra 2 bản ghi lương "Active" song song (mục 3.C).
        with transaction.atomic():
            employee = Employee.objects.select_for_update().get(pk=employee.pk)
            previous_end = _day_before(effective_date)
            if EmployeeSalary.objects.filter(employee=employee, status="Active", effective_date__gt=previous_end).exists():
                raise ValidationError("Ngày nâng lương phải sau ngày hiệu lực của mức lương đang ghi nhận.")
            EmployeeSalary.objects.filter(employee=employee, status="Active").update(
                status="Ended", end_date=_day_before(effective_date)
            )
            new_salary = EmployeeSalary(
                employee=employee, current_basic_salary=request.POST.get("current_basic_salary"),
                effective_date=effective_date, status="Active", created_by=request.user,
            )
            new_salary.full_clean()
            new_salary.save()
        notify(
            employee, "salary", "Mức lương của bạn vừa được cập nhật",
            f"Lương cơ bản mới {new_salary.current_basic_salary}, áp dụng từ {effective_date}.",
            link=f"/portal/hr/employees/{pk}/#luong", created_by=request.user,
        )
        messages.success(request, "Đã ghi nhận nâng lương.")
        if request.POST.get("next") == "hcns" and _can_draft_hr(request):
            return redirect(reverse("portal:hcns_draft", args=["salary-decision"]) + f"?salary_id={new_salary.pk}")
    except Exception as e:
        _friendly_error(request, e, "Không thể lưu.")
    return redirect(f"/portal/hr/employees/{pk}/#luong")


@login_required
@require_POST
def hr_contract_renew(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_employee_detail", pk=pk)
    employee = get_object_or_404(Employee, pk=pk)
    contract = employee.contracts.filter(status="Active").order_by("-start_date", "-pk").first()
    if not contract:
        messages.error(request, "Nhân viên không có hợp đồng đang hiệu lực để gia hạn.")
        return redirect("portal:hr_employee_detail", pk=pk)
    try:
        new_end_date = request.POST.get("new_end_date")
        # transaction.atomic() + select_for_update(): tránh 2 người cùng gia hạn 1 hợp
        # đồng cùng lúc tạo 2 phụ lục trùng nhau (mục 3.C).
        with transaction.atomic():
            contract = Contract.objects.select_for_update().get(pk=contract.pk)
            renewed_end = Contract._meta.get_field("end_date").clean(new_end_date, contract)
            if not renewed_end or (contract.end_date and renewed_end <= contract.end_date):
                raise ValidationError("Gia hạn cần ngày kết thúc mới sau ngày kết thúc hiện tại.")
            if contract.end_date is None:
                raise ValidationError("Hợp đồng không xác định thời hạn không cần gia hạn ngày kết thúc.")
            business_now = timezone.localtime()
            appendix = ContractAppendix(
                contract=contract, appendix_no=request.POST.get("appendix_no") or f"GH-{business_now:%Y%m%d%H%M}",
                effective_date=business_now.date(),
                description=f"Gia hạn hợp đồng đến {new_end_date}", created_by=request.user,
            )
            appendix.full_clean()
            appendix.save()
            contract.end_date = new_end_date
            contract.modified_by = request.user
            contract.full_clean(exclude=["created_by", "modified_by"])
            contract.save(update_fields=["end_date", "modified_by"])
        notify(
            employee, "contract", "Hợp đồng của bạn đã được gia hạn",
            f"Hợp đồng {contract.contract_no} gia hạn đến {new_end_date}.",
            link=f"/portal/hr/employees/{pk}/#hopdong", created_by=request.user,
        )
        messages.success(request, "Đã gia hạn hợp đồng.")
    except Exception as e:
        _friendly_error(request, e, "Không thể gia hạn.")
    return redirect(f"/portal/hr/employees/{pk}/#hopdong")
