from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.security.models import SecurityEvent
from apps.security.permissions import has_permission

from .catalog import FORMS, GROUPS, tables_for
from .exports import export_docx, export_xlsx
from .forms import DraftForm, clean_tables, initial_document_data, make_table_formsets
from .filenames import draft_name
from .prefill import SELECTORS, can_use, prefill
from .rendering import display, document_context


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
    initial, table_initial, source_label = prefill(request.user, spec, request.GET)
    source_query = urlencode({key: request.GET[key] for key in SELECTORS if request.GET.get(key)})
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
        if valid:
            if getattr(form, "selected_employee", None):
                source_record = any(request.GET.get(key) for key in ("salary_id", "promotion_id", "transfer_id", "leave_id", "lifecycle_id"))
                same_record_employee = initial.get("_employee_pk") == form.selected_employee.pk and source_record
                if not same_record_employee:
                    source_label = "Hồ sơ nhân viên " + form.selected_employee.employee_code
                if request.GET.get("employee_id") or (source_record and not same_record_employee):
                    source_query = urlencode({"employee_id": form.selected_employee.pk})
                    initial["_employee_pk"] = form.selected_employee.pk
            if getattr(form, "selected_candidate", None):
                source_label = "Ứng viên " + form.selected_candidate.candidate_code
                if request.GET.get("candidate_id") or request.GET.get("employee_id"):
                    source_query = urlencode({"candidate_id": form.selected_candidate.pk})
                    initial.pop("_employee_pk", None)
            context = document_context(spec, form.cleaned_data, cleaned_tables, source_label)
    else:
        try:
            values, rows = initial_document_data(spec, initial, table_initial, user=request.user)
            context = document_context(spec, values, rows, source_label)
        except ValidationError:
            # No raw values or exception content are returned to the browser/logs.
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
        context["filename_stem"] = draft_name(context, identity, form.cleaned_data if request.method == "POST" else values)
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
        "reference_data": editor_data(form, request.user, table_initial),
        "workflow_source": any(key + "=" in source_query for key in ("salary_id", "promotion_id", "transfer_id")),
        "source_employee_id": initial.get("_employee_pk"),
        "source_reason": initial.get("_source_reason", ""),
        "catalog_query": urlencode({"employee_id": initial["_employee_pk"]}) if initial.get("_employee_pk") else "",
        "employee_source": "employee_id=" in source_query}, status=422 if request.method == "POST" and not valid else 200)
