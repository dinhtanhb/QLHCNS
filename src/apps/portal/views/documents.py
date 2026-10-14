from django.db import models, transaction
from datetime import date
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from apps.document.models import DispatchBook, DispatchTracking, OfficialDispatch
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.notification.services import notify, notify_many, notify_with_email_draft
from apps.organization.models import Department
from apps.hrm.models import Employee
from apps.document.models import Document, DocumentApproval
from apps.reporting.views import _can_view_reports
from .common import _friendly_error, _get_employee, _role_code, _paginated_context




def _can_approve_document(request):
    return has_permission(request.user, "approve_document")


@login_required
def document_list(request):
    documents = Document.objects.filter(status="Approved").select_related("category").order_by("-effective_date")
    return render(request, "portal/document_list.html", {
        "documents": documents,
    })


@login_required
def document_approval_list(request):
    if not _can_approve_document(request):
        messages.error(request, "Anh/chị không có quyền duyệt tài liệu.")
        return redirect("portal:dashboard")
    pending = Document.objects.filter(status="PendingApproval").select_related("category")
    return render(request, "portal/document_approval_list.html", {"documents": pending})


@login_required
@require_POST
def document_approve(request, pk):
    if not _can_approve_document(request):
        messages.error(request, "Anh/chị không có quyền duyệt tài liệu.")
        return redirect("portal:dashboard")

    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:document_approval_list")

    approver = _get_employee(request)
    if not approver:
        messages.error(request, "Tài khoản của anh/chị chưa gắn hồ sơ nhân viên, không thể duyệt.")
        return redirect("portal:document_approval_list")

    # transaction.atomic() + select_for_update(): tránh 2 người bấm duyệt cùng lúc
    # tạo 2 bản ghi DocumentApproval trùng cho cùng 1 tài liệu (mục 3.C).
    with transaction.atomic():
        document = get_object_or_404(
            Document.objects.select_for_update(), pk=pk, status="PendingApproval"
        )
        document.status = decision
        document.save()
        approval = DocumentApproval.objects.create(
            document=document, approver=approver, decision=decision, created_by=request.user
        )
        submitter = None
        if document.created_by_id and hasattr(document.created_by, "employee"):
            submitter = document.created_by.employee
        label = "được duyệt" if decision == "Approved" else "bị từ chối"
        if submitter:
            notify_with_email_draft(
                submitter,
                "document-decision",
                f"Tài liệu {label}",
                f"Tài liệu {document.document_no} đã {label}.",
                link="/portal/documents/",
                email_subject="IHRMS: Có cập nhật về tài liệu bạn gửi",
                email_body=(
                    "Có cập nhật mới về tài liệu anh/chị gửi trong IHRMS. "
                    "Vui lòng đăng nhập cổng nhân viên để xem trạng thái."
                ),
                created_by=request.user,
                idempotency_key=f"document-decision:{approval.pk}:{submitter.pk}",
            )

    if document.status == "Approved":
        notify_many(Employee.objects.filter(employment_status="Active"), "document",
                    "Tài liệu mới ban hành", document.document_name, link="/portal/documents/")

    label = "Đã ban hành" if decision == "Approved" else "Đã từ chối"
    messages.success(request, f"{label} tài liệu {document.document_no}.")
    return redirect("portal:document_approval_list")


def _visible_dispatches(request):
    """Các công văn mà tài khoản đang đăng nhập ĐƯỢC PHÉP xem.

    Dùng chung cho cả danh sách và trang chi tiết, nếu không trang chi tiết sẽ
    hở lỗ hổng: chỉ cần đổi số pk trên URL là đọc được công văn của phòng khác.
    """
    from apps.security.data_access import visible_dispatches_for
    qs = OfficialDispatch.objects.select_related("department", "assigned_to", "dispatch_book")
    return visible_dispatches_for(request.user, qs)


@login_required
def dispatch_list(request):
    is_mgmt = has_permission(request.user, "manage_office")
    qs = _visible_dispatches(request)

    dispatch_type = request.GET.get("type")
    if dispatch_type in ("Incoming", "Outgoing", "InternalDirective"):
        qs = qs.filter(dispatch_type=dispatch_type)

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    search = request.GET.get("q")
    if search:
        qs = qs.filter(
            models.Q(dispatch_no__icontains=search) |
            models.Q(title__icontains=search) |
            models.Q(issuing_organization__icontains=search)
        )

    return render(request, "portal/dispatch_list.html", {
        **_paginated_context(request, qs.order_by('-issue_date', '-pk'), 'dispatches'),
        "selected_type": dispatch_type or "",
        "selected_status": status or "",
        "search_query": search or "",
        "is_management": is_mgmt,
        "can_export_dispatches": _can_view_reports(request),
    })


@login_required
def dispatch_detail(request, pk):
    dispatch = get_object_or_404(
        _visible_dispatches(request).select_related("signer", "reply_to"),
        pk=pk
    )
    trackings = dispatch.trackings.select_related("actor").order_by("-action_date")

    if request.method == "POST":
        action_type = request.POST.get("action_type", "Cập nhật tiến độ")
        comment = request.POST.get("comment", "").strip()
        new_status = request.POST.get("new_status")

        employee = _get_employee(request)
        if not employee:
            messages.error(request, "Tài khoản chưa liên kết hồ sơ nhân viên.")
            return redirect("portal:dispatch_detail", pk=pk)

        # Chỉ người được phân công xử lý hoặc vai trò văn thư mới được cập nhật tiến độ.
        # `is_staff` chỉ cấp quyền vào Django Admin, không phải quyền nghiệp vụ.
        is_mgmt = has_permission(request.user, "manage_office")
        if not is_mgmt and dispatch.assigned_to_id != employee.pk:
            messages.error(request, "Anh/chị không có quyền cập nhật công văn này.")
            return redirect("portal:dispatch_detail", pk=pk)

        if comment:
            DispatchTracking.objects.create(
                dispatch=dispatch,
                actor=employee,
                action_type=action_type,
                comment=comment,
                created_by=request.user
            )

        if new_status in dict(OfficialDispatch.STATUS_CHOICES):
            dispatch.status = new_status
            dispatch.save(update_fields=["status"])

        # Báo cho "phía bên kia": người xử lý cập nhật thì báo người tạo/giao,
        # quản lý cập nhật thì báo người được giao xử lý.
        status_label = dict(OfficialDispatch.STATUS_CHOICES).get(dispatch.status, dispatch.status)
        recipient = None
        if dispatch.assigned_to_id == employee.pk:
            recipient = dispatch.created_by.employee if hasattr(dispatch.created_by, "employee") else None
        elif dispatch.assigned_to_id:
            recipient = dispatch.assigned_to
        if recipient and recipient.pk != employee.pk:
            notify(
                recipient, "dispatch", "Công văn có cập nhật mới",
                f"{dispatch.dispatch_no} - {dispatch.title}: {status_label}.",
                link=f"/portal/dispatches/{dispatch.pk}/", created_by=request.user,
            )

        messages.success(request, "Đã cập nhật tiến độ xử lý công văn.")
        return redirect("portal:dispatch_detail", pk=pk)

    return render(request, "portal/dispatch_detail.html", {
        "dispatch": dispatch,
        "trackings": trackings,
        "status_choices": OfficialDispatch.STATUS_CHOICES,
    })


@login_required
def dispatch_create(request):
    if not has_permission(request.user, "manage_office"):
        messages.error(request, "Anh/chị không có quyền vào sổ công văn.")
        return redirect("portal:dispatch_list")

    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:dispatch_list")

    if request.method == "POST":
        try:
            with transaction.atomic():
                dispatch_type = request.POST.get("dispatch_type")
                issue_date = request.POST.get("issue_date")
                if dispatch_type not in dict(OfficialDispatch.DISPATCH_TYPE_CHOICES):
                    raise ValidationError("Loại công văn không hợp lệ.")
                try:
                    issue_date = date.fromisoformat(issue_date or "")
                except ValueError:
                    raise ValidationError("Ngày ban hành phải là ngày hợp lệ (YYYY-MM-DD).")
                year = issue_date.year
                book_type = "Internal" if dispatch_type == "InternalDirective" else dispatch_type

                book_names = {
                    "Incoming": "Sổ công văn đến", "Outgoing": "Sổ công văn đi", "InternalDirective": "Sổ văn bản nội bộ",
                }
                book, _ = DispatchBook.objects.select_for_update().get_or_create(
                    book_type=book_type, year=year,
                    defaults={
                        "book_code": f"{book_type}-{year}",
                        "book_name": f"{book_names.get(dispatch_type)} {year}",
                        "created_by": request.user,
                    },
                )
                book.current_number += 1
                book.save(update_fields=["current_number"])

                dispatch = OfficialDispatch(
                    dispatch_type=dispatch_type, dispatch_book=book,
                    dispatch_no=request.POST.get("dispatch_no"),
                    original_doc_no=request.POST.get("original_doc_no", ""),
                    title=request.POST.get("title"),
                    issuing_organization=request.POST.get("issuing_organization"),
                    issue_date=issue_date,
                    received_or_sent_date=request.POST.get("received_or_sent_date"),
                    urgency_level=request.POST.get("urgency_level", "Normal"),
                    security_level=request.POST.get("security_level", "Normal"),
                    department_id=request.POST.get("department") or None,
                    assigned_to_id=request.POST.get("assigned_to") or None,
                    signer_id=request.POST.get("signer") or None,
                    due_date=request.POST.get("due_date") or None,
                    attachment=request.FILES.get("attachment"),
                    created_by=request.user,
                )
                dispatch.full_clean()
                dispatch.save()
                DispatchTracking.objects.create(
                    dispatch=dispatch, actor=employee, action_type="Vào sổ",
                    comment="Tiếp nhận/Phát hành công văn.", created_by=request.user,
                )
                if dispatch.assigned_to_id:
                    notify(
                        dispatch.assigned_to, "dispatch", "Bạn được giao xử lý công văn",
                        f"{dispatch.dispatch_no} - {dispatch.title}.",
                        link=f"/portal/dispatches/{dispatch.pk}/", created_by=request.user,
                    )
            messages.success(request, f"Đã vào sổ công văn {dispatch.dispatch_no}.")
            return redirect("portal:dispatch_detail", pk=dispatch.pk)
        except Exception as e:
            _friendly_error(request, e, "Không thể lưu.")

    return render(request, "portal/dispatch_create.html", {
        "departments": Department.objects.filter(is_active=True),
        "employees": Employee.objects.filter(employment_status="Active"),
    })
