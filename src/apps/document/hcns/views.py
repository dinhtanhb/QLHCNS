import copy
from datetime import date, datetime, time
from decimal import Decimal
from urllib.parse import parse_qs, urlencode

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.document.models import PersonnelDecision, PersonnelDecisionHistory
from apps.hrm.models import Employee
from apps.notification.services import notify, notify_many
from apps.security.models import SecurityEvent, User
from apps.security.permissions import PERMISSION_MATRIX, has_permission

from .catalog import FORMS, GROUPS, tables_for
from .exports import export_docx, export_xlsx
from .forms import DraftForm, clean_tables, initial_document_data, make_table_formsets
from .filenames import draft_name
from .prefill import SELECTORS, can_use, prefill
from .rendering import display, document_context


def _json_safe(value):
    if hasattr(value, "_meta") and hasattr(value, "pk"):
        return value.pk
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _visible_personnel_decision(user, decision):
    if has_permission(user, "manage_hr"):
        return True
    employee = getattr(user, "employee", None)
    if decision.status == "Issued" and employee and decision.employee_id == employee.pk:
        return True
    return has_permission(user, "approve_personnel_decision") and (
        decision.status == "PendingApproval" or decision.history.filter(created_by=user).exists()
    )


def _decision_rendered(decision):
    return copy.deepcopy(decision.content_snapshot.get("rendered", {}))


def _record_decision_event(decision, action, previous_status, comment, user):
    PersonnelDecisionHistory.objects.create(
        decision=decision,
        action=action,
        status_from=previous_status,
        status_to=decision.status,
        comment=comment,
        created_by=user,
    )


def _decision_link(decision):
    return f"/portal/hr-decisions/{decision.pk}/"


def _notify_personnel_decision_approvers(decision, actor):
    recipients = User.objects.filter(is_active=True, employee__isnull=False).filter(
        Q(is_superuser=True)
        | Q(role__role_code__in=PERMISSION_MATRIX.get("approve_personnel_decision", ()))
    ).exclude(pk=actor.pk)
    if actor.employee_id:
        recipients = recipients.exclude(employee_id=actor.employee_id)
    employee_ids = recipients.values_list("employee_id", flat=True)
    notify_many(
        Employee.objects.filter(pk__in=employee_ids),
        "personnel-decision",
        "Có quyết định nhân sự cần duyệt",
        f"{decision.decision_no or 'Chưa đánh số'} của {decision.employee.full_name} đang chờ duyệt.",
        link=_decision_link(decision),
        created_by=actor,
    )


def _latest_decision_submitter(decision):
    submission = decision.history.filter(action="Submitted").select_related("created_by__employee").order_by("-pk").first()
    return submission.created_by if submission else decision.created_by


def _notify_decision_submitter(decision, action, comment, actor):
    submitter = _latest_decision_submitter(decision)
    recipient = getattr(submitter, "employee", None) if submitter else None
    if not recipient:
        return
    approved = action == "Approved"
    status_text = "đã được duyệt" if approved else "bị từ chối"
    message = f"Quyết định {decision.decision_no or decision.pk} {status_text}."
    if comment:
        message += f" Ý kiến: {comment[:600]}"
    notify(
        recipient,
        "personnel-decision",
        "Quyết định đã được duyệt" if approved else "Quyết định bị từ chối",
        message,
        link=_decision_link(decision),
        created_by=actor,
    )


def _notify_decision_issued(decision, comment, actor):
    recipient_ids = {decision.employee_id}
    submitter = _latest_decision_submitter(decision)
    submitter_employee_id = getattr(submitter, "employee_id", None) if submitter else None
    if submitter_employee_id:
        recipient_ids.add(submitter_employee_id)
    message = f"Quyết định {decision.decision_no or decision.pk} đã ban hành. Mở để xem và tải PDF đã ký."
    if comment:
        message += f" Ghi chú: {comment[:500]}"
    notify_many(
        Employee.objects.filter(pk__in=recipient_ids),
        "personnel-decision",
        "Quyết định nhân sự đã ban hành",
        message,
        link=_decision_link(decision),
        created_by=actor,
    )


def _save_personnel_decision(request, spec, form, cleaned_tables, context, source_label, source_query, saved_decision):
    employee = getattr(form, "selected_employee", None)
    if not employee:
        form.add_error("full_name", "Chọn hồ sơ nhân viên trước khi lưu quyết định.")
        return None

    values = form.cleaned_data
    content_snapshot = {
        "values": _json_safe(values),
        "reference_ids": {
            key: request.POST.get(key)
            for key, field in form.fields.items()
            if hasattr(field, "queryset") and request.POST.get(key)
            and field.queryset.filter(pk=request.POST.get(key)).exists()
        },
        "tables": _json_safe(cleaned_tables),
        "source_label": source_label,
        "source_query": source_query,
        "rendered": _json_safe(context),
    }
    decision_date = values.get("decision_date") or values.get("document_date")
    effective_date = values.get("effective_date")
    with transaction.atomic():
        if saved_decision:
            decision = get_object_or_404(PersonnelDecision.objects.select_for_update(), pk=saved_decision.pk)
            if decision.status not in ("Draft", "Rejected") or decision.template_slug != spec["slug"]:
                form.add_error(None, "Quyết định đã chuyển trạng thái. Tải lại trang để xem nội dung hiện tại.")
                return None
        else:
            decision = PersonnelDecision(created_by=request.user)
        previous_status = decision.status if saved_decision else ""
        decision.employee = employee
        decision.template_slug = spec["slug"]
        decision.decision_no = values.get("decision_no") or ""
        decision.decision_date = decision_date
        decision.effective_date = effective_date
        decision.content_snapshot = content_snapshot
        decision.status = "Draft"
        decision.modified_by = request.user if saved_decision else None
        try:
            decision.full_clean()
        except ValidationError as error:
            if hasattr(error, "message_dict"):
                for key, errors in error.message_dict.items():
                    form.add_error(key if key in form.fields else None, errors)
            else:
                form.add_error(None, error)
            return None
        decision.save()
        _record_decision_event(
            decision,
            "DraftUpdated" if saved_decision else "DraftCreated",
            previous_status,
            "",
            request.user,
        )
    return decision


@login_required
@never_cache
@require_http_methods(["GET"])
def catalog(request):
    group = request.GET.get("group", "")
    employee_id = request.GET.get("employee_id", "")
    if employee_id:
        # Validate the selector before displaying it or distributing prefill links.
        prefill(request.user, FORMS["employee-information"], request.GET)
    forms = []
    for spec in FORMS.values():
        if can_use(request.user, spec) and (not group or spec["group"] == group):
            item = dict(spec)
            item["source_query"] = urlencode({"employee_id": employee_id}) if employee_id else ""
            forms.append(item)
    groups = [{"key": key, "label": label, "forms": [spec for spec in forms if spec["group"] == key]} for key, label in GROUPS.items()]
    employees = []
    if has_permission(request.user, "view_all_employees") and has_permission(request.user, "export_employee_data"):
        from apps.hrm.models import Employee
        employees = Employee.objects.order_by("full_name").only("id", "employee_code", "full_name")
    own = getattr(request.user, "employee", None)
    return render(request, "document/hcns/catalog.html", {"groups": groups, "employees": employees, "selected_employee": employee_id,
        "own_employee": own if own and not own.is_deleted else None, "available_count": len(forms)})


def _export(request, context):
    spec = context["spec"]
    kind = spec["kind"]
    payload = export_xlsx(context) if kind == "xlsx" else export_docx(context)
    content_type = "application/vnd.openxmlformats-officedocument." + ("spreadsheetml.sheet" if kind == "xlsx" else "wordprocessingml.document")
    response = HttpResponse(payload, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{context["filename_stem"]}.{kind}"'
    response["X-Content-Type-Options"] = "nosniff"
    SecurityEvent.objects.create(user=request.user, action="data_export", resource="hcns:" + spec["slug"])
    return response


@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def draft(request, slug):
    spec = FORMS.get(slug)
    if not spec:
        raise Http404()
    if not can_use(request.user, spec):
        return HttpResponseForbidden("Anh/chị không có quyền sử dụng mẫu này.")
    saved_decision = None
    decision_id = request.GET.get("decision_id", "")
    if decision_id:
        if spec["group"] != "decision":
            raise Http404()
        if not has_permission(request.user, "manage_hr"):
            return HttpResponseForbidden("Anh/chị không có quyền sửa quyết định nhân sự.")
        saved_decision = get_object_or_404(
            PersonnelDecision.objects.filter(status__in=("Draft", "Rejected")), pk=decision_id
        )
        if saved_decision.template_slug != slug:
            raise Http404()
        snapshot = saved_decision.content_snapshot
        initial = dict(snapshot.get("values", {}))
        initial.update(snapshot.get("reference_ids", {}))
        initial.update({"_employee_pk": saved_decision.employee_id, "_employee_code": saved_decision.employee.employee_code})
        table_initial = snapshot.get("tables", {})
        source_label = snapshot.get("source_label", "")
        source_selectors = parse_qs(snapshot.get("source_query", ""))
    else:
        initial, table_initial, source_label = prefill(request.user, spec, request.GET)
        source_selectors = {key: [request.GET[key]] for key in SELECTORS if request.GET.get(key)}
    source_selectors = {key: values[-1] for key, values in source_selectors.items() if key in SELECTORS and values}
    source_query = urlencode(source_selectors)
    large_source = any(len(table_initial.get(table["key"], [])) > table["max_rows"] for table in tables_for(spec))
    if large_source and request.method == "POST":
        return HttpResponseForbidden("Hồ sơ nhiều dòng chỉ được xem và xuất đầy đủ; sửa dữ liệu tại phân hệ nguồn.")
    data = request.POST if request.method == "POST" else None
    form = DraftForm(spec, data=data, initial=initial, user=request.user)
    bound_tables = make_table_formsets(spec, data=data, initial=table_initial, user=request.user) if not large_source else []
    valid = False
    context = None
    if request.method == "POST":
        table_valid, cleaned_tables = clean_tables(bound_tables)
        valid = form.is_valid() and table_valid
        if valid and request.POST.get("action") == "save_decision" and spec["group"] == "decision" and not getattr(form, "selected_employee", None):
            form.add_error("full_name", "Chọn hồ sơ nhân viên trước khi lưu quyết định.")
            valid = False
        if valid:
            if getattr(form, "selected_employee", None):
                source_record = any(source_selectors.get(key) for key in ("salary_id", "promotion_id", "transfer_id", "leave_id", "lifecycle_id"))
                same_record_employee = initial.get("_employee_pk") == form.selected_employee.pk and source_record
                if not same_record_employee:
                    source_label = "Hồ sơ nhân viên " + form.selected_employee.employee_code
                if source_selectors.get("employee_id") or (source_record and not same_record_employee) or (saved_decision and saved_decision.employee_id != form.selected_employee.pk):
                    source_query = urlencode({"employee_id": form.selected_employee.pk})
                    initial["_employee_pk"] = form.selected_employee.pk
            if getattr(form, "selected_candidate", None):
                source_label = "Ứng viên " + form.selected_candidate.candidate_code
                if request.GET.get("candidate_id") or request.GET.get("employee_id"):
                    source_query = urlencode({"candidate_id": form.selected_candidate.pk})
                    initial.pop("_employee_pk", None)
            context = document_context(spec, form.cleaned_data, cleaned_tables, source_label)
    else:
        if saved_decision:
            values = initial
            context = _decision_rendered(saved_decision)
        else:
            try:
                values, rows = initial_document_data(spec, initial, table_initial, user=request.user)
                context = document_context(spec, values, rows, source_label)
            except ValidationError:
                form.errors
                form.cleaned_data = {}
                form.add_error(None, "Dữ liệu hồ sơ nguồn chưa phù hợp với mẫu. Hãy kiểm tra tại phân hệ nguồn.")
    if context:
        identity = ""
        if request.method == "POST" and "full_name" in form.fields:
            selected = getattr(form, "selected_employee", None) or getattr(form, "selected_candidate", None)
            if selected:
                identity = getattr(selected, "employee_code", None) or selected.candidate_code
        elif initial.get("_employee_pk") and spec["slug"] != "candidate-interview":
            identity = initial.get("_employee_code", "")
        elif initial.get("_candidate_pk"):
            identity = initial.get("_candidate_code", "")
        if saved_decision and request.method == "GET":
            context["filename_stem"] = context.get("filename_stem") or draft_name(context, identity, values)
        else:
            context["filename_stem"] = draft_name(context, identity, form.cleaned_data if request.method == "POST" else values)
    if request.method == "POST" and request.POST.get("action") == "save_decision" and valid and context:
        if spec["group"] != "decision" or not has_permission(request.user, "manage_hr"):
            return HttpResponseForbidden("Anh/chị không có quyền lưu quyết định nhân sự.")
        decision = _save_personnel_decision(
            request, spec, form, cleaned_tables, context, source_label, source_query, saved_decision
        )
        if decision:
            messages.success(request, "Đã lưu bản nháp quyết định.")
            return redirect("portal:personnel_decision_detail", pk=decision.pk)
        valid = False
    export_requested = request.POST.get("action") == "export" if request.method == "POST" else request.GET.get("export") == "1"
    if export_requested and context and (valid or request.method == "GET"):
        return _export(request, context)
    editor_sections = []
    for section_spec in spec["sections"]:
        entry = {"title": section_spec["title"], "fields": [form[field["key"]] for field in section_spec["fields"]], "table": None}
        table_spec = section_spec.get("table")
        if table_spec and not large_source:
            bound = next(item for item in bound_tables if item["spec"]["key"] == table_spec["key"])
            rows = []
            for index, row_form in enumerate(bound["formset"].forms):
                cells = []
                for col in table_spec["columns"]:
                    cells.append({"locked": bool(col.get("locked")), "text": display(table_spec["rows"][index].get(col["key"]), placeholder=False) if col.get("locked") else "",
                        "field": None if col.get("locked") else row_form[col["key"]]})
                rows.append({"cells": cells, "form": row_form})
            entry["table"] = {**bound, "editor_rows": rows, "empty_fields": [bound["formset"].empty_form[col["key"]] for col in table_spec["columns"] if not col.get("locked")]}
        editor_sections.append(entry)
    from .choices import editor_data
    return render(request, "document/hcns/draft.html", {"spec": spec, "form": form, "editor_sections": editor_sections,
        "document": context, "source_label": source_label, "source_query": source_query, "read_only": large_source,
        "preview_updated": valid, "employee_choices": form.employee_choices,
        "can_save_decision": spec["group"] == "decision" and has_permission(request.user, "manage_hr"),
        "decision_query": urlencode({"decision_id": saved_decision.pk}) if saved_decision else "",
        "reference_data": editor_data(form, request.user, table_initial),
        "workflow_source": any(key + "=" in source_query for key in ("salary_id", "promotion_id", "transfer_id")),
        "source_employee_id": initial.get("_employee_pk"),
        "source_reason": initial.get("_source_reason", ""),
        "catalog_query": urlencode({"employee_id": initial["_employee_pk"]}) if initial.get("_employee_pk") else "",
        "employee_source": "employee_id=" in source_query}, status=422 if request.method == "POST" and not valid else 200)


@login_required
@never_cache
@require_http_methods(["GET"])
def personnel_decision_list(request):
    can_manage = has_permission(request.user, "manage_hr")
    can_approve = has_permission(request.user, "approve_personnel_decision")
    if not (can_manage or can_approve):
        return HttpResponseForbidden("Anh/chị không có quyền xem quyết định nhân sự.")

    decisions = PersonnelDecision.objects.select_related("employee", "created_by")
    if not can_manage:
        decisions = decisions.filter(Q(status="PendingApproval") | Q(history__created_by=request.user)).distinct()
    query = request.GET.get("q", "").strip()
    if query:
        decisions = decisions.filter(
            Q(decision_no__icontains=query)
            | Q(employee__employee_code__icontains=query)
            | Q(employee__full_name__icontains=query)
        )
    status = request.GET.get("status", "")
    valid_statuses = {choice[0] for choice in PersonnelDecision.STATUS_CHOICES}
    if status in valid_statuses and (can_manage or status == "PendingApproval"):
        decisions = decisions.filter(status=status)
    page_obj = Paginator(decisions.order_by("-created_date", "-pk"), 25).get_page(request.GET.get("page"))
    for decision in page_obj.object_list:
        decision.template_title = FORMS.get(decision.template_slug, {}).get("title", decision.template_slug)
    return render(request, "portal/personnel_decision_list.html", {
        "page_obj": page_obj,
        "decisions": page_obj.object_list,
        "query": query,
        "selected_status": status,
        "status_choices": PersonnelDecision.STATUS_CHOICES,
        "can_manage_decisions": can_manage,
        "can_approve_decisions": can_approve,
    })


@login_required
@never_cache
@require_http_methods(["GET"])
def personnel_decision_detail(request, pk):
    decision = get_object_or_404(
        PersonnelDecision.objects.select_related("employee", "created_by").prefetch_related("history__created_by"),
        pk=pk,
    )
    if not _visible_personnel_decision(request.user, decision):
        return HttpResponseForbidden("Anh/chị không có quyền xem quyết định này.")
    rendered = _decision_rendered(decision)
    decision.template_title = FORMS.get(decision.template_slug, {}).get("title", decision.template_slug)
    history = decision.history.select_related("created_by").all()
    last_submission = history.filter(action="Submitted").order_by("-pk").first()
    can_manage = has_permission(request.user, "manage_hr")
    can_approve = has_permission(request.user, "approve_personnel_decision")
    is_employee_recipient = bool(
        not can_manage and not can_approve and decision.status == "Issued"
        and request.user.employee_id == decision.employee_id
    )
    return render(request, "portal/personnel_decision_detail.html", {
        "decision": decision,
        "document": None if is_employee_recipient else rendered,
        "history": [] if is_employee_recipient else history,
        "is_employee_recipient": is_employee_recipient,
        "can_view_workflow": can_manage or can_approve,
        "can_download_word": not is_employee_recipient,
        "can_edit_decision": can_manage and decision.status in ("Draft", "Rejected"),
        "can_submit_decision": can_manage and decision.status == "Draft",
        "can_approve_decision": can_approve and decision.status == "PendingApproval" and last_submission and last_submission.created_by_id != request.user.pk,
        "can_issue_decision": can_manage and decision.status == "Approved",
        "can_cancel_decision": can_manage and decision.status in ("Draft", "Rejected"),
    })


@login_required
@never_cache
@require_http_methods(["GET"])
def personnel_decision_word(request, pk):
    decision = get_object_or_404(PersonnelDecision.objects.select_related("employee"), pk=pk)
    if not _visible_personnel_decision(request.user, decision) or not (
        has_permission(request.user, "manage_hr")
        or has_permission(request.user, "approve_personnel_decision")
    ):
        return HttpResponseForbidden("Anh/chị không có quyền tải quyết định này.")
    context = _decision_rendered(decision)
    if not context:
        raise Http404()
    if not context.get("filename_stem"):
        raise Http404()
    return _export(request, context)


@login_required
@never_cache
@require_POST
def personnel_decision_transition(request, pk, action):
    comment = request.POST.get("comment", "").strip()
    with transaction.atomic():
        decision = get_object_or_404(PersonnelDecision.objects.select_for_update(), pk=pk)
        previous_status = decision.status
        if action == "submit":
            if not has_permission(request.user, "manage_hr"):
                return HttpResponseForbidden("Anh/chị không có quyền trình duyệt quyết định.")
            if decision.status != "Draft":
                messages.error(request, "Chỉ bản nháp mới được trình duyệt.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            if not decision.decision_no or not decision.decision_date:
                messages.error(request, "Cần có số quyết định và ngày quyết định trước khi trình duyệt.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            decision.status = "PendingApproval"
            history_action = "Submitted"
        elif action in ("approve", "reject"):
            if not has_permission(request.user, "approve_personnel_decision"):
                return HttpResponseForbidden("Anh/chị không có quyền duyệt quyết định.")
            if decision.status != "PendingApproval":
                messages.error(request, "Quyết định không còn ở trạng thái chờ duyệt.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            latest_submission = decision.history.filter(action="Submitted").order_by("-pk").first()
            if latest_submission and latest_submission.created_by_id == request.user.pk:
                messages.error(request, "Người trình duyệt không được tự duyệt quyết định này.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            if action == "reject" and not comment:
                messages.error(request, "Nhập lý do từ chối để lưu lịch sử xử lý.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            decision.status = "Approved" if action == "approve" else "Rejected"
            history_action = "Approved" if action == "approve" else "Rejected"
        elif action == "issue":
            if not has_permission(request.user, "manage_hr"):
                return HttpResponseForbidden("Anh/chị không có quyền ban hành quyết định.")
            if decision.status != "Approved":
                messages.error(request, "Chỉ quyết định đã duyệt mới được ban hành.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            signed_pdf = request.FILES.get("issued_file")
            if not signed_pdf:
                messages.error(request, "Tải PDF đã ký lên để ghi nhận ban hành.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            decision.issued_file = signed_pdf
            decision.issued_at = timezone.now()
            decision.status = "Issued"
            history_action = "Issued"
        elif action == "cancel":
            if not has_permission(request.user, "manage_hr"):
                return HttpResponseForbidden("Anh/chị không có quyền hủy quyết định.")
            if decision.status not in ("Draft", "Rejected"):
                messages.error(request, "Chỉ bản nháp hoặc quyết định bị từ chối mới được hủy.")
                return redirect("portal:personnel_decision_detail", pk=pk)
            decision.status = "Cancelled"
            history_action = "Cancelled"
        else:
            raise Http404()

        decision.modified_by = request.user
        try:
            decision.full_clean()
        except ValidationError as error:
            messages.error(request, "; ".join(error.messages))
            return redirect("portal:personnel_decision_detail", pk=pk)
        decision.save()
        _record_decision_event(decision, history_action, previous_status, comment, request.user)
        if history_action == "Submitted":
            _notify_personnel_decision_approvers(decision, request.user)
        elif history_action in ("Approved", "Rejected"):
            _notify_decision_submitter(decision, history_action, comment, request.user)
        elif history_action == "Issued":
            _notify_decision_issued(decision, comment, request.user)
    messages.success(request, f"Đã cập nhật trạng thái: {decision.get_status_display()}.")
    return redirect("portal:personnel_decision_detail", pk=pk)
