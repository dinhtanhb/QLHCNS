from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.notification.services import notify
from apps.office.models import (
    MeetingRoom,
    RoomBooking,
    SupplyItem,
    SupplyRequest,
    SupplyRequestItem,
    Vehicle,
    VehicleBooking,
)
from apps.procurement.models import ProcurementApproval, ProcurementItem, ProcurementRequest
from django.utils import timezone
from .common import _employees_with_permission, _friendly_error, _get_employee
from apps.common.params import parse_int




def _can_approve_office_request(request):
    return has_permission(request.user, "approve_office_request")


def _office_request_approvers():
    return _employees_with_permission("approve_office_request")


@login_required
def room_booking_list(request):
    employee = _get_employee(request)
    upcoming = RoomBooking.objects.filter(
        status__in=["Pending", "Approved"], end_time__gte=timezone.now(),
    ).select_related("room", "employee").order_by("start_time")
    return render(request, "portal/room_booking_list.html", {
        "upcoming": upcoming, "rooms": MeetingRoom.objects.filter(is_active=True),
    })


@login_required
@require_POST
def room_booking_create(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:room_booking_list")
    try:
        booking = RoomBooking(
            room_id=request.POST.get("room"), employee=employee,
            purpose=request.POST.get("purpose"),
            start_time=request.POST.get("start_time"), end_time=request.POST.get("end_time"),
            status="Pending", created_by=request.user,
        )
        booking.full_clean()
        booking.save()
        for approver in _office_request_approvers():
            notify(
                approver, "office", "Có yêu cầu đặt phòng họp chờ duyệt",
                f"{employee.full_name} đề nghị đặt {booking.room} "
                f"({booking.start_time:%d/%m %H:%M} - {booking.end_time:%H:%M}).",
                link="/portal/rooms/approvals/", created_by=request.user,
            )
        messages.success(request, "Đã gửi yêu cầu đặt phòng, chờ duyệt.")
    except Exception as e:
        _friendly_error(request, e, "Không thể đặt phòng.")
    return redirect("portal:room_booking_list")


@login_required
@require_POST
def room_booking_cancel(request, pk):
    employee = _get_employee(request)
    booking = get_object_or_404(RoomBooking, pk=pk, employee=employee)
    booking.status = "Cancelled"
    booking.save(update_fields=["status"])
    messages.success(request, "Đã hủy đặt phòng.")
    return redirect("portal:room_booking_list")


@login_required
def room_booking_approval_list(request):
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền duyệt đặt phòng họp.")
        return redirect("portal:dashboard")
    pending = RoomBooking.objects.filter(status="Pending").select_related("room", "employee").order_by("start_time")
    return render(request, "portal/room_booking_approval_list.html", {"bookings": pending})


@login_required
@require_POST
def room_booking_approve(request, pk):
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền duyệt đặt phòng họp.")
        return redirect("portal:dashboard")
    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:room_booking_approval_list")
    try:
        # transaction.atomic() + select_for_update(): tránh 2 người bấm duyệt
        # cùng lúc dẫn tới 2 phòng chồng giờ đều được duyệt (mục 3.C).
        with transaction.atomic():
            resource_id = get_object_or_404(RoomBooking, pk=pk, status="Pending").room_id
            # Lock the common resource before individual reservations, so two
            # approvals for different pending rows cannot both pass overlap checks.
            get_object_or_404(MeetingRoom.objects.select_for_update(), pk=resource_id)
            booking = get_object_or_404(
                RoomBooking.objects.select_for_update(), pk=pk, status="Pending"
            )
            if booking.room_id != resource_id:
                # Phòng bị đổi giữa hai lần đọc: khóa đang giữ không bảo vệ đúng
                # tài nguyên, phải tải lại thay vì duyệt nhầm.
                raise ValidationError("Phòng họp đã thay đổi. Tải lại yêu cầu trước khi duyệt.")
            booking.status = decision
            booking.modified_by = request.user
            # ResourceBookingSaveMixin khóa lại tài nguyên và chạy full_clean()
            # khi trạng thái là "Approved"; không lặp lại kiểm tra ở đây.
            booking.save()
        label = "duyệt" if decision == "Approved" else "từ chối"
        notify(
            booking.employee, "office", f"Yêu cầu đặt phòng họp đã được {label}",
            f"Đặt {booking.room} ({booking.start_time:%d/%m %H:%M} - {booking.end_time:%H:%M}) đã {label}.",
            link="/portal/rooms/", created_by=request.user,
        )
        messages.success(request, f"Đã {label} yêu cầu đặt phòng.")
    except Exception as e:
        _friendly_error(request, e, "Không thể xử lý yêu cầu đặt phòng.")
    return redirect("portal:room_booking_approval_list")


@login_required
def vehicle_booking_list(request):
    upcoming = VehicleBooking.objects.filter(
        status__in=["Pending", "Approved"], end_time__gte=timezone.now(),
    ).select_related("vehicle", "employee").order_by("start_time")
    return render(request, "portal/vehicle_booking_list.html", {
        "upcoming": upcoming, "vehicles": Vehicle.objects.filter(is_active=True),
    })


@login_required
@require_POST
def vehicle_booking_create(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:vehicle_booking_list")
    try:
        booking = VehicleBooking(
            vehicle_id=request.POST.get("vehicle"), employee=employee,
            destination=request.POST.get("destination"), purpose=request.POST.get("purpose", ""),
            start_time=request.POST.get("start_time"), end_time=request.POST.get("end_time"),
            status="Pending", created_by=request.user,
        )
        booking.full_clean()
        booking.save()
        for approver in _office_request_approvers():
            notify(
                approver, "office", "Có yêu cầu đặt xe chờ duyệt",
                f"{employee.full_name} đề nghị đặt xe đi {booking.destination} "
                f"({booking.start_time:%d/%m %H:%M} - {booking.end_time:%H:%M}).",
                link="/portal/vehicles/approvals/", created_by=request.user,
            )
        messages.success(request, "Đã gửi yêu cầu đặt xe, chờ duyệt.")
    except Exception as e:
        _friendly_error(request, e, "Không thể đặt xe.")
    return redirect("portal:vehicle_booking_list")


@login_required
@require_POST
def vehicle_booking_cancel(request, pk):
    employee = _get_employee(request)
    booking = get_object_or_404(VehicleBooking, pk=pk, employee=employee)
    booking.status = "Cancelled"
    booking.save(update_fields=["status"])
    messages.success(request, "Đã hủy đặt xe.")
    return redirect("portal:vehicle_booking_list")


@login_required
def vehicle_booking_approval_list(request):
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền duyệt đặt xe.")
        return redirect("portal:dashboard")
    pending = VehicleBooking.objects.filter(status="Pending").select_related("vehicle", "employee").order_by("start_time")
    return render(request, "portal/vehicle_booking_approval_list.html", {"bookings": pending})


@login_required
@require_POST
def vehicle_booking_approve(request, pk):
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền duyệt đặt xe.")
        return redirect("portal:dashboard")
    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:vehicle_booking_approval_list")
    try:
        with transaction.atomic():
            resource_id = get_object_or_404(VehicleBooking, pk=pk, status="Pending").vehicle_id
            get_object_or_404(Vehicle.objects.select_for_update(), pk=resource_id)
            booking = get_object_or_404(
                VehicleBooking.objects.select_for_update(), pk=pk, status="Pending"
            )
            if booking.vehicle_id != resource_id:
                # Xe bị đổi giữa hai lần đọc: khóa đang giữ không bảo vệ đúng
                # tài nguyên, phải tải lại thay vì duyệt nhầm.
                raise ValidationError("Xe đã thay đổi. Tải lại yêu cầu trước khi duyệt.")
            booking.status = decision
            booking.modified_by = request.user
            # ResourceBookingSaveMixin khóa lại tài nguyên và chạy full_clean()
            # khi trạng thái là "Approved"; không lặp lại kiểm tra ở đây.
            booking.save()
        label = "duyệt" if decision == "Approved" else "từ chối"
        notify(
            booking.employee, "office", f"Yêu cầu đặt xe đã được {label}",
            f"Đặt xe đi {booking.destination} ({booking.start_time:%d/%m %H:%M} - {booking.end_time:%H:%M}) đã {label}.",
            link="/portal/vehicles/", created_by=request.user,
        )
        messages.success(request, f"Đã {label} yêu cầu đặt xe.")
    except Exception as e:
        _friendly_error(request, e, "Không thể xử lý yêu cầu đặt xe.")
    return redirect("portal:vehicle_booking_approval_list")


@login_required
def supply_request_list(request):
    employee = _get_employee(request)
    requests_qs = SupplyRequest.objects.filter(employee=employee).prefetch_related("items__item").order_by("-request_date") if employee else []
    return render(request, "portal/supply_request_list.html", {
        "requests": requests_qs, "items": SupplyItem.objects.all(),
    })


@login_required
@require_POST
def supply_request_create(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:supply_request_list")

    item_ids = request.POST.getlist("item")
    quantities = request.POST.getlist("quantity")
    valid_lines = []
    if len(item_ids) != len(quantities):
        messages.error(request, "Danh sách vật tư và số lượng không khớp.")
        return redirect("portal:supply_request_list")
    for item_id, quantity in zip(item_ids, quantities):
        if not item_id and not quantity:
            continue
        parsed_id = parse_int(item_id, None, min_value=1, max_value=2147483647)
        parsed_quantity = parse_int(quantity, None, min_value=1, max_value=2147483647)
        if parsed_id is None or parsed_quantity is None:
            messages.error(request, "Vui lòng chọn vật tư và nhập số lượng nguyên dương hợp lệ.")
            return redirect("portal:supply_request_list")
        valid_lines.append((parsed_id, parsed_quantity))

    if not valid_lines:
        messages.error(request, "Vui lòng chọn ít nhất 1 vật tư với số lượng > 0.")
        return redirect("portal:supply_request_list")

    try:
        with transaction.atomic():
            supply_request = SupplyRequest.objects.create(
                request_no=f"VPP-{employee.employee_code}-{timezone.now():%Y%m%d%H%M%S}",
                employee=employee, request_date=timezone.now().date(), created_by=request.user,
            )
            for item_id, qty in valid_lines:
                SupplyRequestItem.objects.create(
                    supply_request=supply_request, item_id=item_id, quantity_requested=qty, created_by=request.user,
                )
        for approver in _office_request_approvers():
            notify(
                approver, "office", "Có đề nghị cấp VPP chờ duyệt",
                f"{employee.full_name} gửi đề nghị {supply_request.request_no}.",
                link="/portal/supplies/approvals/", created_by=request.user,
            )
        messages.success(request, "Đã gửi đề nghị cấp vật tư, chờ Hành chính duyệt.")
    except Exception as e:
        _friendly_error(request, e, "Không thể tạo đề nghị.")
    return redirect("portal:supply_request_list")


@login_required
def supply_request_approval_list(request):
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền duyệt đề nghị VPP.")
        return redirect("portal:dashboard")
    pending = SupplyRequest.objects.filter(status="Pending").select_related("employee").prefetch_related("items__item").order_by("request_date")
    approved = SupplyRequest.objects.filter(status="Approved").select_related("employee").prefetch_related("items__item").order_by("request_date")
    return render(request, "portal/supply_request_approval_list.html", {
        "pending": pending, "approved": approved,
    })


@login_required
@require_POST
def supply_request_approve(request, pk):
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền duyệt đề nghị VPP.")
        return redirect("portal:dashboard")
    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:supply_request_approval_list")
    try:
        with transaction.atomic():
            supply_request = get_object_or_404(
                SupplyRequest.objects.select_for_update(), pk=pk, status="Pending"
            )
            supply_request.status = decision
            supply_request.modified_by = request.user
            supply_request.save(update_fields=["status", "modified_by"])
        label = "duyệt" if decision == "Approved" else "từ chối"
        notify(
            supply_request.employee, "office", f"Đề nghị cấp VPP đã được {label}",
            f"Đề nghị {supply_request.request_no} đã {label}.",
            link="/portal/supplies/", created_by=request.user,
        )
        messages.success(request, f"Đã {label} đề nghị {supply_request.request_no}.")
    except Exception as e:
        _friendly_error(request, e, "Không thể xử lý đề nghị.")
    return redirect("portal:supply_request_approval_list")


@login_required
@require_POST
def supply_request_issue(request, pk):
    """Xuất kho cho đề nghị đã duyệt — trừ tồn kho theo từng dòng vật tư.

    Bọc transaction.atomic() + select_for_update() trên cả SupplyRequest lẫn
    SupplyItem để 2 người bấm "Xuất kho" cùng lúc không trừ tồn kho 2 lần
    hoặc xuất vượt tồn (mục 3.C).
    """
    if not _can_approve_office_request(request):
        messages.error(request, "Anh/chị không có quyền cấp phát VPP.")
        return redirect("portal:dashboard")
    try:
        from apps.office.services import issue_supply_request
        supply_request = issue_supply_request(pk, actor=request.user)
        notify(
            supply_request.employee, "office", "Đã cấp phát vật tư",
            f"Đề nghị {supply_request.request_no} đã được cấp phát.",
            link="/portal/supplies/", created_by=request.user,
        )
        messages.success(request, f"Đã cấp phát vật tư cho đề nghị {supply_request.request_no}.")
    except Exception as e:
        _friendly_error(request, e, "Không thể cấp phát vật tư.")
    return redirect("portal:supply_request_approval_list")


def _can_request_procurement(request):
    return has_permission(request.user, "request_procurement")


def _can_approve_procurement(request):
    return has_permission(request.user, "approve_procurement")


@login_required
def procurement_request_list(request):
    employee = _get_employee(request)
    if _can_approve_procurement(request):
        requests_qs = ProcurementRequest.objects.select_related(
            "requested_by", "department"
        ).prefetch_related("items").order_by("-request_date")
    elif employee:
        requests_qs = ProcurementRequest.objects.filter(requested_by=employee).select_related(
            "requested_by", "department"
        ).prefetch_related("items").order_by("-request_date")
    else:
        requests_qs = ProcurementRequest.objects.none()
    return render(request, "portal/procurement_request_list.html", {
        "requests": requests_qs,
        "can_create": _can_request_procurement(request) and employee is not None,
        "can_approve": _can_approve_procurement(request),
    })


@login_required
@require_POST
def procurement_request_create(request):
    if not _can_request_procurement(request):
        messages.error(request, "Anh/chị không có quyền đề nghị mua sắm.")
        return redirect("portal:procurement_request_list")
    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:procurement_request_list")
    if not employee.department_id:
        messages.error(request, "Hồ sơ nhân viên chưa gắn phòng ban.")
        return redirect("portal:procurement_request_list")

    item_names = request.POST.getlist("item_name")
    quantities = request.POST.getlist("quantity")
    costs = request.POST.getlist("estimated_cost")
    valid_lines = [
        (name.strip(), qty, cost) for name, qty, cost in zip(item_names, quantities, costs)
        if name.strip() and qty and qty.isdigit() and int(qty) > 0
    ]
    if not valid_lines:
        messages.error(request, "Vui lòng nhập ít nhất 1 hạng mục với số lượng > 0.")
        return redirect("portal:procurement_request_list")

    try:
        with transaction.atomic():
            proc_request = ProcurementRequest.objects.create(
                request_no=f"MS-{employee.employee_code}-{timezone.now():%Y%m%d%H%M%S}",
                requested_by=employee, department=employee.department,
                request_date=timezone.now().date(), reason=request.POST.get("reason", ""),
                created_by=request.user,
            )
            for name, qty, cost in valid_lines:
                ProcurementItem.objects.create(
                    procurement_request=proc_request, item_name=name, quantity=qty,
                    estimated_cost=cost or None, created_by=request.user,
                )
        for approver in _employees_with_permission("approve_procurement"):
            notify(
                approver, "procurement", "Có đề nghị mua sắm chờ duyệt",
                f"{employee.full_name} ({proc_request.department}) gửi đề nghị {proc_request.request_no}.",
                link="/portal/procurement/", created_by=request.user,
            )
        messages.success(request, f"Đã gửi đề nghị mua sắm {proc_request.request_no}, chờ duyệt.")
    except Exception as e:
        _friendly_error(request, e, "Không thể tạo đề nghị mua sắm.")
    return redirect("portal:procurement_request_list")


@login_required
@require_POST
def procurement_request_approve(request, pk):
    if not _can_approve_procurement(request):
        messages.error(request, "Anh/chị không có quyền duyệt đề nghị mua sắm.")
        return redirect("portal:procurement_request_list")
    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:procurement_request_list")
    approver = _get_employee(request)
    if not approver:
        messages.error(request, "Tài khoản của anh/chị chưa gắn hồ sơ nhân viên, không thể duyệt.")
        return redirect("portal:procurement_request_list")

    try:
        with transaction.atomic():
            proc_request = get_object_or_404(
                ProcurementRequest.objects.select_for_update(), pk=pk, status="Pending"
            )
            proc_request.status = decision
            proc_request.modified_by = request.user
            proc_request.save(update_fields=["status", "modified_by"])
            ProcurementApproval.objects.create(
                procurement_request=proc_request, approver=approver, decision=decision, created_by=request.user,
            )
        label = "duyệt" if decision == "Approved" else "từ chối"
        notify(
            proc_request.requested_by, "procurement", f"Đề nghị mua sắm đã được {label}",
            f"Đề nghị {proc_request.request_no} đã {label}.",
            link="/portal/procurement/", created_by=request.user,
        )
        messages.success(request, f"Đã {label} đề nghị {proc_request.request_no}.")
    except Exception as e:
        _friendly_error(request, e, "Không thể xử lý đề nghị mua sắm.")
    return redirect("portal:procurement_request_list")


@login_required
@require_POST
def procurement_request_mark_purchased(request, pk):
    if not _can_approve_procurement(request):
        messages.error(request, "Anh/chị không có quyền cập nhật đề nghị mua sắm.")
        return redirect("portal:procurement_request_list")
    try:
        with transaction.atomic():
            proc_request = get_object_or_404(
                ProcurementRequest.objects.select_for_update(), pk=pk, status="Approved"
            )
            proc_request.status = "Purchased"
            proc_request.modified_by = request.user
            proc_request.save(update_fields=["status", "modified_by"])
        messages.success(request, f"Đã đánh dấu {proc_request.request_no} là đã mua.")
    except Exception as e:
        _friendly_error(request, e, "Không thể cập nhật đề nghị mua sắm.")
    return redirect("portal:procurement_request_list")

