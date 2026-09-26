from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from apps.asset.models import AssetAllocation
from apps.hrm.models import Employee
from apps.lifecycle.models import ChecklistTemplate, EmployeeLifecycleCase, LifecycleChecklistItem
from apps.lifecycle.services import open_offboarding_case, open_onboarding_case
from apps.security.models import User
from apps.security.permissions import has_permission


def _employee_for(user):
    return getattr(user, "employee", None)


def _can_view_case(user, case):
    if has_permission(user, "manage_lifecycle_case"):
        return True
    if not has_permission(user, "view_own_lifecycle_items"):
        return False
    return (
        getattr(user, "employee_id", None) == case.employee_id
        or case.items.filter(assigned_to_user=user).exists()
    )


@login_required
def lifecycle_case_list(request):
    if not has_permission(request.user, "view_own_lifecycle_items") and not has_permission(request.user, "manage_lifecycle_case"):
        return HttpResponseForbidden()
    cases = EmployeeLifecycleCase.objects.select_related("employee", "template")
    if not has_permission(request.user, "manage_lifecycle_case"):
        employee = _employee_for(request.user)
        if not employee:
            return HttpResponseForbidden()
        cases = cases.filter(Q(employee=employee) | Q(items__assigned_to_user=request.user)).distinct()
    return render(request, "lifecycle/case_list.html", {
        "cases": cases, "can_manage_lifecycle_case": has_permission(request.user, "manage_lifecycle_case")
    })


@login_required
def lifecycle_case_create(request):
    if not has_permission(request.user, "manage_lifecycle_case"):
        return HttpResponseForbidden()
    templates = ChecklistTemplate.objects.filter(is_active=True)
    employees = Employee.objects.filter(is_deleted=False).order_by("full_name")
    if request.method == "POST":
        employee = get_object_or_404(employees, pk=request.POST.get("employee_id"))
        template = get_object_or_404(templates, pk=request.POST.get("template_id"))
        case_type = request.POST.get("case_type")
        if case_type != template.template_type:
            messages.error(request, "Loại hồ sơ không khớp với mẫu checklist.")
            return redirect("portal:lifecycle_case_create")
        if case_type == "Onboarding":
            effective_date = employee.join_date
            open_onboarding_case(employee, template, request.user)
        elif case_type == "Offboarding":
            effective_date = parse_date(request.POST.get("effective_date", ""))
            if not effective_date:
                messages.error(request, "Vui lòng nhập ngày nghỉ việc hiệu lực.")
                return redirect("portal:lifecycle_case_create")
            open_offboarding_case(employee, template, effective_date, request.user)
        else:
            return HttpResponseForbidden("Loại hồ sơ không hợp lệ.")
        messages.success(request, "Checklist đã mở. Các đầu việc được tạo từ bản chụp mẫu.")
        return redirect("portal:lifecycle_case_list")
    return render(request, "lifecycle/case_create.html", {"templates": templates, "employees": employees})


@login_required
def lifecycle_case_detail(request, pk):
    case = get_object_or_404(
        EmployeeLifecycleCase.objects.select_related("employee", "template"), pk=pk
    )
    if not _can_view_case(request.user, case):
        return HttpResponseForbidden()
    items = case.items.select_related("assigned_to_user", "template_item", "asset_allocation__asset")
    users = User.objects.filter(is_active=True, employee__employment_status="Active").select_related("role", "employee")
    allocations = AssetAllocation.objects.filter(employee=case.employee).select_related("asset").order_by("-assigned_date")
    return render(request, "lifecycle/case_detail.html", {
        "case": case, "items": items, "users": users, "allocations": allocations,
        "can_manage_lifecycle_case": has_permission(request.user, "manage_lifecycle_case"),
    })


@login_required
@require_POST
def lifecycle_item_assign(request, pk):
    if not has_permission(request.user, "manage_lifecycle_case"):
        return HttpResponseForbidden()
    item = get_object_or_404(LifecycleChecklistItem.objects.select_related("case"), pk=pk, status="Pending")
    user_id = request.POST.get("assigned_to_user_id")
    user = get_object_or_404(
        User.objects.select_related("role", "employee").filter(
            is_active=True, employee__employment_status="Active",
            role__role_code=item.responsible_role_code,
        ), pk=user_id,
    )
    item.assigned_to_user = user
    item.modified_by = request.user
    item.save(update_fields=["assigned_to_user", "modified_by", "modified_date"])
    messages.success(request, "Đã giao đầu việc checklist.")
    return redirect("portal:lifecycle_case_detail", pk=item.case_id)


@login_required
@require_POST
def lifecycle_item_update(request, pk):
    item = get_object_or_404(
        LifecycleChecklistItem.objects.select_related("case", "case__employee"), pk=pk
    )
    if not _can_view_case(request.user, item.case):
        return HttpResponseForbidden()
    if item.assigned_to_user_id != request.user.pk and not has_permission(request.user, "manage_lifecycle_case"):
        return HttpResponseForbidden()
    if item.case.status != "Open" or item.status != "Pending":
        return HttpResponseForbidden("Đầu việc checklist này không còn ở trạng thái chờ xử lý.")
    action = request.POST.get("action")
    if action == "done":
        allocation_id = request.POST.get("asset_allocation_id")
        if allocation_id:
            allocation = get_object_or_404(
                AssetAllocation.objects.select_related("asset"), pk=allocation_id, employee=item.case.employee
            )
            if item.case.case_type == "Offboarding" and allocation.return_date is None:
                messages.error(request, "Tài sản đang sử dụng chưa được xác nhận thu hồi.")
                return redirect("portal:lifecycle_case_detail", pk=item.case_id)
            item.asset_allocation = allocation
        elif item.requires_asset_return:
            messages.error(request, "Hãy liên kết lịch sử cấp phát/thu hồi tài sản trước khi hoàn tất đầu việc này.")
            return redirect("portal:lifecycle_case_detail", pk=item.case_id)
        item.status = "Done"
        item.completed_by = request.user
        from django.utils import timezone
        item.completed_at = timezone.now()
        item.skip_reason = ""
    elif action == "skip":
        reason = request.POST.get("skip_reason", "").strip()
        if not reason:
            messages.error(request, "Cần ghi lý do khi bỏ qua đầu việc.")
            return redirect("portal:lifecycle_case_detail", pk=item.case_id)
        item.status = "Skipped"
        item.completed_by = request.user
        from django.utils import timezone
        item.completed_at = timezone.now()
        item.skip_reason = reason[:500]
    else:
        return HttpResponseForbidden("Thao tác không hợp lệ.")
    item.modified_by = request.user
    item.save(update_fields=[
        "status", "completed_by", "completed_at", "skip_reason", "asset_allocation",
        "modified_by", "modified_date",
    ])
    if not item.case.items.filter(status="Pending").exists():
        item.case.status = "Completed"
        item.case.modified_by = request.user
        item.case.save(update_fields=["status", "modified_by", "modified_date"])
    messages.success(request, "Đã cập nhật đầu việc checklist.")
    return redirect("portal:lifecycle_case_detail", pk=item.case_id)
