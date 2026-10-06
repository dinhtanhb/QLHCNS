import datetime
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.notification.services import notify, notify_with_email_draft
import calendar as calendar_module
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET
from apps.payroll.models import (
    EmployeeDependent,
    EmployeeSalary,
    InsuranceRateConfig,
    Payroll,
    PayrollPeriod,
    Payslip,
    PersonalIncomeTaxBracket,
    TaxDeductionConfig,
)
from apps.common.params import parse_int
from apps.hrm.models import Employee
import logging
logger = logging.getLogger(__name__)
from .common import _friendly_error, _get_employee




def _day_before(date_str_or_date):
    """Trả về ngày liền trước `date_str_or_date` (str 'YYYY-MM-DD' hoặc date) — dùng để tự động
    đóng `effective_to` của thế hệ cấu hình lương/thuế/BH cũ khi thêm thế hệ mới (mục C1)."""
    d = date_str_or_date
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
    return d - datetime.timedelta(days=1)


@login_required
def payslip_list(request):
    employee = _get_employee(request)
    # Mục I8: chỉ hiện phiếu lương của kỳ đã "Locked" — kỳ "Open" là số Kế toán
    # đang tính/chỉnh, chưa phải số cuối cùng, không nên cho nhân viên xem như đã chốt.
    payrolls = Payroll.objects.filter(
        employee=employee, payroll_period__status="Locked", payslip__isnull=False
    ).select_related("payroll_period", "payslip").order_by(
        "-payroll_period__payroll_year", "-payroll_period__payroll_month"
    ) if employee else []
    return render(request, "portal/payslip_list.html", {"payrolls": payrolls})


@login_required
@require_GET
def payslip_pdf(request, pk):
    """A staff member may download only their own issued payslip for a locked period."""
    employee = _get_employee(request)
    if employee is None:
        raise Http404
    payslip = get_object_or_404(
        Payslip.objects.select_related(
            "payroll__employee__department", "payroll__employee__position",
            "payroll__payroll_period",
        ),
        pk=pk, payroll__employee=employee, payroll__payroll_period__status="Locked",
        payroll__is_deleted=False, payroll__payroll_period__is_deleted=False, payroll__employee__is_deleted=False,
    )
    from apps.payroll.payslip_pdf import render_payslip_pdf
    response = HttpResponse(render_payslip_pdf(payslip), content_type="application/pdf")
    period = payslip.payroll.payroll_period
    from apps.common.export_names import export_name
    from django.utils import timezone
    filename = export_name("Phieu_Luong", f"{employee.employee_code}-{period.payroll_year}{period.payroll_month:02d}", timezone.localtime(payslip.generated_date).date(), "pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def _can_manage_finance(request):
    return has_permission(request.user, "manage_finance")


@login_required
def finance_period_list(request):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền truy cập.")
        return redirect("portal:dashboard")
    periods = PayrollPeriod.objects.order_by("-payroll_year", "-payroll_month")
    return render(request, "portal/finance_period_list.html", {"periods": periods})


@login_required
@require_POST
def finance_period_create(request):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")
    month = parse_int(request.POST.get("payroll_month"), None, min_value=1, max_value=12)
    year = parse_int(request.POST.get("payroll_year"), None, min_value=2000, max_value=2100)
    if month is None or year is None:
        messages.error(request, "Tháng/năm không hợp lệ.")
        return redirect("portal:finance_period_list")
    try:
        first_day = f"{year}-{month:02d}-01"
        last_day = calendar_module.monthrange(year, month)[1]
        period = PayrollPeriod.objects.create(
            payroll_month=month, payroll_year=year,
            start_date=first_day, end_date=f"{year}-{month:02d}-{last_day:02d}",
            created_by=request.user,
        )
        messages.success(request, f"Đã tạo kỳ lương {month}/{year}.")
        return redirect("portal:finance_payroll_run", pk=period.pk)
    except Exception as e:
        _friendly_error(request, e, "Không thể tạo kỳ lương.")
        return redirect("portal:finance_period_list")


def _employees_payable_for_period(period):
    """Return active employees and inactive employees whose last day falls in this period."""
    return Employee.objects.filter(join_date__lte=period.end_date).filter(
        models.Q(employment_status="Active")
        | models.Q(leave_date__gte=period.start_date, leave_date__lte=period.end_date)
    )


@login_required
def finance_payroll_run(request, pk):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")

    period = get_object_or_404(PayrollPeriod, pk=pk)
    existing_emp_ids = set(Payroll.objects.filter(payroll_period=period).values_list("employee_id", flat=True))

    payrolls = Payroll.objects.filter(payroll_period=period).select_related("employee")
    missing_employees = _employees_payable_for_period(period).exclude(id__in=existing_emp_ids)
    unissued_payslips = payrolls.filter(payslip__isnull=True).count() if period.status == "Locked" else 0

    return render(request, "portal/finance_payroll_run.html", {
        "period": period, "payrolls": payrolls, "missing_employees": missing_employees,
        "unissued_payslips": unissued_payslips,
    })


@login_required
@require_POST
def finance_payroll_generate(request, pk):
    """Tạo dòng Bảng lương cho các nhân viên chưa có trong kỳ này, lấy lương cơ bản từ EmployeeSalary."""
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")

    period = get_object_or_404(PayrollPeriod, pk=pk)
    if period.status == "Locked":
        messages.error(request, "Kỳ lương đã khóa — không thể tạo thêm dòng bảng lương.")
        return redirect("portal:finance_payroll_run", pk=pk)

    with transaction.atomic():
        # Khóa bản ghi kỳ lương để 2 người bấm cùng lúc không tạo trùng
        period = PayrollPeriod.objects.select_for_update().get(pk=pk)
        if period.status != "Open":
            messages.error(request, "Kỳ lương đã khóa — không thể tạo thêm dòng.")
            return redirect("portal:finance_payroll_run", pk=pk)
        existing_emp_ids = set(
            Payroll.objects.filter(payroll_period=period).values_list("employee_id", flat=True)
        )
        employees = list(
            _employees_payable_for_period(period).exclude(id__in=existing_emp_ids)
        )
        # Lấy lương cơ bản của tất cả nhân viên trong 1 lần truy vấn thay vì lặp từng người
        salary_map = {}
        for sal in (
            EmployeeSalary.objects.filter(employee__in=employees, effective_date__lte=period.start_date)
            .filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=period.start_date))
            .order_by("effective_date")
        ):
            salary_map[sal.employee_id] = sal.current_basic_salary

        new_rows = [
            Payroll(
                payroll_period=period, employee=employee,
                basic_salary=salary_map.get(employee.id, 0),
                insurance_salary=salary_map.get(employee.id, 0),
                created_by=request.user,
            )
            for employee in employees
        ]
        Payroll.objects.bulk_create(new_rows)
        count = len(new_rows)

    messages.success(request, f"Đã tạo {count} dòng bảng lương mới cho kỳ {period}.")
    return redirect("portal:finance_payroll_run", pk=pk)


@login_required
@require_POST
def finance_payroll_calculate_all(request, pk):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")

    period = get_object_or_404(PayrollPeriod, pk=pk)
    if period.status == "Locked":
        messages.error(request, "Kỳ lương đã khóa — không thể tính lại lương.")
        return redirect("portal:finance_payroll_run", pk=pk)

    # I13: mỗi nhân viên dùng 1 savepoint atomic() riêng (nested), KHÔNG bọc chung
    # 1 atomic() cho cả vòng lặp. Nếu bọc chung, lỗi của 1 nhân viên (kể cả
    # ValidationError thuần Python) sẽ khiến Django đánh dấu toàn bộ transaction
    # ngoài là "needs_rollback" — mọi câu lệnh DB của các nhân viên tính SAU đó
    # trong cùng vòng lặp sẽ ăn theo lỗi TransactionManagementError, dù bản thân
    # họ tính hoàn toàn đúng. Dùng savepoint riêng từng người để cô lập lỗi.
    count, errors = 0, []
    configuration = Payroll.load_calculation_configuration(period.start_date)
    for payroll in Payroll.objects.filter(payroll_period=period).select_related("employee"):
        try:
            with transaction.atomic():
                locked_period = PayrollPeriod.objects.select_for_update().get(pk=period.pk)
                if locked_period.status != "Open":
                    raise ValidationError("Kỳ lương đã khóa — không thể tính lại.")
                payroll = Payroll.objects.select_for_update().select_related("employee").get(pk=payroll.pk)
                payroll.payroll_period = locked_period
                payroll.calculate(configuration=configuration)
                payroll.modified_by = request.user
                payroll.save()
            count += 1
        except ValidationError as e:
            detail = "; ".join(e.messages) if hasattr(e, "messages") else str(e)
            errors.append(f"{payroll.employee}: {detail}")
        except Exception as e:
            logger.exception("Lỗi tính lương nhân viên %s (kỳ %s)", payroll.employee, period)
            errors.append(f"{payroll.employee}: Có lỗi hệ thống khi tính lương, đã ghi log.")

    messages.success(request, f"Đã tính lương cho {count} nhân viên.")
    for err in errors:
        messages.error(request, err)
    return redirect("portal:finance_payroll_run", pk=pk)


@login_required
@require_POST
def finance_payroll_lock(request, pk):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")
    with transaction.atomic():
        period = get_object_or_404(PayrollPeriod.objects.select_for_update(), pk=pk)
        if period.status == "Locked":
            messages.info(request, "Kỳ lương đã khóa.")
            return redirect("portal:finance_period_list")
        payrolls = list(Payroll.objects.select_for_update().filter(payroll_period=period).select_related("employee"))
        try:
            if not payrolls:
                raise ValidationError("Kỳ lương chưa có dòng bảng lương.")
            if _employees_payable_for_period(period).exclude(pk__in=[row.employee_id for row in payrolls]).exists():
                raise ValidationError("Kỳ lương còn thiếu nhân viên cần trả lương; hãy tạo đủ dòng trước khi khóa.")
            configuration = Payroll.load_calculation_configuration(period.start_date)
            for payroll in payrolls:
                payroll.payroll_period = period
                payroll.validate_calculated(configuration=configuration)
        except ValidationError as error:
            _friendly_error(request, error, "Không thể khóa kỳ lương.")
            return redirect("portal:finance_payroll_run", pk=pk)
        period.status = "Locked"
        period.modified_by = request.user
        period.save()
        payrolls = list(Payroll.objects.filter(payroll_period=period).select_related("employee"))
        existing_ids = set(Payslip.objects.filter(payroll__payroll_period=period).values_list("payroll_id", flat=True))
        to_issue = [payroll for payroll in payrolls if payroll.pk not in existing_ids]
        Payslip.objects.bulk_create([
            Payslip(payroll=payroll, created_by=request.user) for payroll in to_issue
        ])
        period_managers = Employee.objects.filter(
            employment_status="Active",
            user_account__role__role_code__in=("DIRECTOR", "FINANCE_OFFICER"),
        ).select_related("user_account", "user_account__role").distinct()
        for recipient in period_managers:
            is_finance = recipient.user_account.role.role_code == "FINANCE_OFFICER"
            notify_with_email_draft(
                recipient,
                "payroll-period-locked",
                "Kỳ lương đã khóa",
                f"Kỳ lương {period} đã được khóa trong IHRMS.",
                link="/portal/finance/periods/" if is_finance else "/portal/reports/",
                email_subject="IHRMS: Kỳ lương đã khóa",
                email_body=(
                    f"Kỳ lương {period} đã được khóa. "
                    "Vui lòng đăng nhập IHRMS để xem thông tin theo quyền được cấp."
                ),
                created_by=request.user,
                idempotency_key=f"payroll-period-locked:{period.pk}:{recipient.pk}",
            )
    for payroll in to_issue:
        notify(
            payroll.employee, "payroll", "Phiếu lương của bạn đã sẵn sàng",
            f"Bảng lương kỳ {period} đã được chốt; tải phiếu lương PDF trong mục Phiếu lương.",
            link="/portal/payslip/", created_by=request.user,
        )
    messages.success(request, f"Đã khóa kỳ lương {period}. Không thể sửa bảng lương của kỳ này nữa.")
    return redirect("portal:finance_period_list")


@login_required
@require_POST
def finance_payslip_issue(request, pk):
    """Backfill payslip records for periods locked before PDF release was enabled."""
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")
    with transaction.atomic():
        period = get_object_or_404(PayrollPeriod.objects.select_for_update(), pk=pk)
        if period.status != "Locked":
            messages.error(request, "Chỉ có thể phát hành phiếu lương sau khi kỳ đã khóa.")
            return redirect("portal:finance_payroll_run", pk=period.pk)
        existing_ids = set(Payslip.objects.filter(payroll__payroll_period=period).values_list("payroll_id", flat=True))
        to_issue = list(
            Payroll.objects.filter(payroll_period=period).exclude(pk__in=existing_ids).select_related("employee")
        )
        Payslip.objects.bulk_create([
            Payslip(payroll=payroll, created_by=request.user) for payroll in to_issue
        ])
    for payroll in to_issue:
        notify(
            payroll.employee, "payroll", "Phiếu lương của bạn đã sẵn sàng",
            f"Phiếu lương PDF kỳ {period} đã được phát hành trong mục Phiếu lương.",
            link="/portal/payslip/", created_by=request.user,
        )
    messages.success(request, f"Đã phát hành {len(to_issue)} phiếu lương PDF cho kỳ {period}.")
    return redirect("portal:finance_payroll_run", pk=period.pk)


@login_required
@require_POST
def finance_payroll_update_line(request, pk):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:finance_period_list")
    payroll = get_object_or_404(Payroll, pk=pk)
    if payroll.payroll_period.status == "Locked":
        messages.error(request, "Kỳ lương đã khóa, không thể sửa.")
        return redirect("portal:finance_payroll_run", pk=payroll.payroll_period_id)
    try:
        with transaction.atomic():
            period = PayrollPeriod.objects.select_for_update().get(pk=payroll.payroll_period_id)
            if period.status != "Open":
                raise ValidationError("Kỳ lương đã khóa, không thể sửa.")
            payroll = Payroll.objects.select_for_update().get(pk=pk)
            payroll.payroll_period = period
            payroll.allowance = request.POST.get("allowance") or 0
            payroll.overtime_amount = request.POST.get("overtime_amount") or 0
            payroll.overtime_tax_exempt_amount = request.POST.get("overtime_tax_exempt_amount") or 0
            payroll.insurance_salary = request.POST.get("insurance_salary") or 0
            payroll.deduction_amount = request.POST.get("deduction_amount") or 0
            payroll.modified_by = request.user
            payroll.full_clean(exclude=["created_by", "modified_by"])
            payroll.save()
            messages.success(request, "Đã cập nhật, cần bấm \"Tính lương lại\" để cập nhật số liệu.")
    except Exception as e:
        _friendly_error(request, e, "Không thể lưu.")
    return redirect("portal:finance_payroll_run", pk=payroll.payroll_period_id)


@login_required
def finance_salary_list(request):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:dashboard")
    salaries = EmployeeSalary.objects.filter(status="Active").select_related("employee").order_by("employee__full_name")
    return render(request, "portal/finance_salary_list.html", {"salaries": salaries})


@login_required
def finance_tax_config(request):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:dashboard")

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        try:
            if form_type == "insurance":
                effective_from = request.POST.get("effective_from")
                with transaction.atomic():
                    # Đóng effective_to của các thế hệ cũ còn bỏ ngỏ (C1: nếu không đóng,
                    # calculate() có thể vẫn chỉ lấy .first() theo effective_from mới nhất nên ít rủi ro
                    # hơn bracket, nhưng đóng lại cho rõ ràng, tránh nhầm lẫn khi tra cứu).
                    InsuranceRateConfig.objects.filter(effective_to__isnull=True).exclude(
                        effective_from__gte=effective_from
                    ).update(effective_to=_day_before(effective_from))
                    InsuranceRateConfig.objects.create(
                        effective_from=effective_from,
                        employee_social_insurance_rate=request.POST.get("employee_social_insurance_rate"),
                        employee_health_insurance_rate=request.POST.get("employee_health_insurance_rate"),
                        employee_unemployment_insurance_rate=request.POST.get("employee_unemployment_insurance_rate"),
                        employer_social_insurance_rate=request.POST.get("employer_social_insurance_rate"),
                        employer_health_insurance_rate=request.POST.get("employer_health_insurance_rate"),
                        employer_unemployment_insurance_rate=request.POST.get("employer_unemployment_insurance_rate"),
                        legal_reference=request.POST.get("legal_reference", ""),
                        created_by=request.user,
                    )
                messages.success(request, "Đã thêm cấu hình tỷ lệ Bảo hiểm.")
            elif form_type == "deduction":
                effective_from = request.POST.get("effective_from")
                with transaction.atomic():
                    TaxDeductionConfig.objects.filter(effective_to__isnull=True).exclude(
                        effective_from__gte=effective_from
                    ).update(effective_to=_day_before(effective_from))
                    TaxDeductionConfig.objects.create(
                        effective_from=effective_from,
                        self_deduction_monthly=request.POST.get("self_deduction_monthly"),
                        dependent_deduction_monthly=request.POST.get("dependent_deduction_monthly"),
                        created_by=request.user,
                    )
                messages.success(request, "Đã thêm cấu hình giảm trừ thuế.")
            elif form_type == "bracket":
                # C1 (sửa): tự đóng effective_to của TOÀN BỘ thế hệ bậc thuế cũ (mọi bracket_no
                # cùng effective_from cũ, chưa có effective_to) trước khi thêm bậc của thế hệ mới —
                # để calculate() (và bất kỳ báo cáo nào lọc theo effective_to) không bao giờ thấy
                # 2 thế hệ cùng "đang hiệu lực" một lúc, kể cả khi người dùng không khai đủ tất cả
                # các bậc trong cùng 1 lần submit.
                effective_from = request.POST.get("effective_from")
                with transaction.atomic():
                    PersonalIncomeTaxBracket.objects.filter(effective_to__isnull=True).exclude(
                        effective_from__gte=effective_from
                    ).update(effective_to=_day_before(effective_from))
                    PersonalIncomeTaxBracket.objects.create(
                        effective_from=effective_from,
                        bracket_no=request.POST.get("bracket_no"),
                        income_from_monthly=request.POST.get("income_from_monthly"),
                        income_to_monthly=request.POST.get("income_to_monthly") or None,
                        tax_rate=request.POST.get("tax_rate"),
                        created_by=request.user,
                    )
                messages.success(request, "Đã thêm bậc thuế TNCN.")
        except Exception as e:
            _friendly_error(request, e, "Không thể lưu.")
        return redirect("portal:finance_tax_config")

    return render(request, "portal/finance_tax_config.html", {
        "insurance_configs": InsuranceRateConfig.objects.order_by("-effective_from"),
        "deduction_configs": TaxDeductionConfig.objects.order_by("-effective_from"),
        "tax_brackets": PersonalIncomeTaxBracket.objects.order_by("-effective_from", "bracket_no"),
    })


@login_required
def finance_dependent_list(request):
    if not _can_manage_finance(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:dashboard")
    if request.method == "POST":
        try:
            dependent = EmployeeDependent(
                employee_id=request.POST.get("employee"),
                full_name=request.POST.get("full_name"),
                relationship=request.POST.get("relationship"),
                registered_from=request.POST.get("registered_from"),
                created_by=request.user,
            )
            dependent.full_clean()
            dependent.save()
            messages.success(request, "Đã thêm người phụ thuộc.")
        except Exception as e:
            _friendly_error(request, e, "Không thể lưu.")
        return redirect("portal:finance_dependent_list")
    return render(request, "portal/finance_dependent_list.html", {
        "dependents": EmployeeDependent.objects.filter(is_active=True).select_related("employee"),
        "employees": Employee.objects.filter(employment_status="Active"),
    })

