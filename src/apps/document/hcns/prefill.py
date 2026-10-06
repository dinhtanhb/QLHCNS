"""All selectors are allow-listed and checked before reading personal data."""
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.security.data_access import can_read_file
from apps.security.permissions import has_permission


SELECTORS = ("employee_id", "leave_id", "candidate_id", "inventory_id", "disposal_id", "lifecycle_id", "salary_id", "promotion_id", "transfer_id")


def can_use(user, spec):
    if not user.is_authenticated or not user.is_active:
        return False
    if spec.get("personal") or spec.get("public_internal"):
        return True
    group = spec["group"]
    if group == "asset":
        return has_permission(user, "view_asset")
    if group == "salary":
        return has_permission(user, "manage_finance") or has_permission(user, "view_employee_compensation")
    if group == "decision":
        return has_permission(user, "view_employee_compensation")
    return has_permission(user, "manage_hr") or (group == "personnel" and has_permission(user, "view_employee_compensation"))


def _employee_data(employee, *, private=False):
    result = {"_employee_pk": employee.pk, "_employee_code": employee.employee_code, "_position_pk": employee.position_id, "_department_pk": employee.department_id,
              "full_name": employee.full_name, "position": str(employee.position), "department": str(employee.department),
              "join_date": employee.join_date, "leave_date": employee.leave_date}
    if employee.manager_id and not employee.manager.is_deleted:
        result.update(manager=employee.manager.full_name, manager_position=str(employee.manager.position))
    if private:
        result.update(date_of_birth=employee.date_of_birth, national_id=employee.national_id,
            tax_code=employee.tax_code or "", insurance_no=employee.social_insurance_no or "",
            phone=employee.mobile_phone, email=employee.personal_email or employee.company_email, address=employee.address or "",
            gender=employee.get_gender_display(), birth_year=employee.date_of_birth.year)
    return result


def _employee_template_data(user, spec, employee):
    """Only map recorded values to matching slots; never infer a new decision."""
    from .catalog import fields_for
    from .rendering import display
    keys = {field["key"] for field in fields_for(spec)}
    values = _employee_data(employee, private=bool(keys & {"date_of_birth", "national_id", "tax_code", "insurance_no", "phone", "email", "address", "gender", "birth_year"}))
    if "new_position" in keys:
        values["new_position"] = values["position"]
        values["_new_position_pk"] = employee.position_id
    if employee.manager_id and not employee.manager.is_deleted:
        values["_manager_pk"] = employee.manager_id
        values["_manager_position_pk"] = employee.manager.position_id
    if keys & {"salary", "salary_note"} and has_permission(user, "view_employee_compensation"):
        from apps.payroll.models import EmployeeSalary
        today = timezone.localdate()
        # A scheduled raise closes the prior interval immediately. Its previous
        # salary still applies today until that interval's recorded end date.
        salaries = list(EmployeeSalary.objects.filter(employee=employee, status__in=("Active", "Ended"), effective_date__lte=today)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).order_by("-effective_date", "-pk")[:2])
        if len(salaries) == 1:
            amount = salaries[0].current_basic_salary
            values["salary"] = amount.to_integral_value() if amount == amount.to_integral_value() else amount
            values["salary_note"] = display(amount) + " đồng (lương cơ bản hiện hành)"
    if "contract_no" in keys:
        from apps.contract.models import Contract
        today = timezone.localdate()
        contracts = list(Contract.objects.filter(employee=employee, status="Active", start_date__lte=today)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).order_by("-start_date", "-pk")[:2])
        if len(contracts) == 1:
            values["contract_no"] = contracts[0].contract_no
    # Private values used for another template must not leak through editor metadata.
    if spec["slug"] == "candidate-interview":
        # An employee source is not an applicant source.
        return {key: value for key, value in values.items() if key in ("position", "department", "_position_pk", "_department_pk", "_employee_pk", "_employee_code") and (key in keys or key.startswith("_"))}
    return {key: value for key, value in values.items() if key in keys or key in ("_employee_pk", "_employee_code", "_position_pk", "_department_pk", "_new_position_pk", "_manager_pk", "_manager_position_pk")}


def _employee_for(user, pk):
    from apps.hrm.models import Employee
    employee = get_object_or_404(Employee.objects.select_related("department", "position", "manager__position"), pk=pk)
    own = getattr(user, "employee", None)
    if own and not own.is_deleted and own.pk == employee.pk:
        return employee
    # Merely being allowed to view employee lists is insufficient for exports.
    if not has_permission(user, "export_employee_data") or not has_permission(user, "view_all_employees"):
        raise PermissionDenied("Không có quyền lấy dữ liệu nhân sự cho biểu mẫu.")
    return employee


def _asset_row(asset):
    return {"_asset_pk": asset.pk, "name": asset.asset_name, "code": asset.asset_code, "quantity": asset.quantity,
            "brand": asset.brand or "", "condition": asset.get_condition_display(),
            "type": str(asset.asset_type), "location": asset.location or "", "serial": asset.serial_number or "",
            "funding": asset.funding_source or "", "purchase_date": asset.purchase_date,
            "unit": asset.unit or "", "value": asset.purchase_value}


def prefill(user, spec, params):
    values, tables, source_label = {}, {}, ""
    provided = [(key, params.get(key)) for key in SELECTORS if params.get(key)]
    if len(provided) > 1:
        raise Http404("Chỉ chọn một hồ sơ nguồn cho mỗi biểu mẫu.")
    if not provided:
        return values, tables, source_label
    selector, raw_pk = provided[0]
    try:
        pk = int(raw_pk)
        if pk <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise Http404("Mã hồ sơ không hợp lệ.")
    if selector == "employee_id":
        employee = _employee_for(user, pk)
        values = _employee_template_data(user, spec, employee)
        source_label = "Hồ sơ nhân viên " + employee.employee_code
    elif selector in ("salary_id", "promotion_id", "transfer_id"):
        from apps.hrm.models import EmployeePromotion, EmployeeTransfer
        from apps.payroll.models import EmployeeSalary
        models = {"salary_id": EmployeeSalary, "promotion_id": EmployeePromotion, "transfer_id": EmployeeTransfer}
        expected = "appointment-decision" if selector == "promotion_id" else "salary-decision"
        if spec["slug"] != expected:
            raise Http404("Bản ghi nghiệp vụ không khớp biểu mẫu.")
        if not has_permission(user, "view_employee_compensation"):
            raise PermissionDenied()
        obj = get_object_or_404(models[selector], pk=pk)
        employee = _employee_for(user, obj.employee_id)
        values = _employee_template_data(user, spec, employee)
        values["effective_date"] = obj.effective_date
        values["_source_reason"] = getattr(obj, "reason", "")
        if selector == "salary_id":
            amount = obj.current_basic_salary
            values["salary"] = amount.to_integral_value() if amount == amount.to_integral_value() else amount
            label = "Mức lương"
        elif selector == "promotion_id":
            values.update(position=str(obj.old_position), new_position=str(obj.new_position),
                          _position_pk=obj.old_position_id, _new_position_pk=obj.new_position_id,
                          decision_action="Bổ nhiệm")
            label = "Bổ nhiệm"
        else:
            values.update(department=str(obj.to_department), _department_pk=obj.to_department_id, workplace=str(obj.to_department))
            label = "Điều chuyển"
        source_label = f"{label} #{obj.pk} – {employee.employee_code} – {obj.effective_date:%d/%m/%Y}"
    elif selector == "leave_id":
        if spec["group"] != "leave" and spec["slug"] != "maternity-decision":
            raise Http404()
        from apps.leave.models import LeaveRequest
        obj = get_object_or_404(LeaveRequest.objects.select_related("employee__department", "employee__position", "leave_type"), pk=pk)
        if not can_read_file(user, obj):
            raise PermissionDenied()
        expected = {"AL": "annual-leave", "CO": "compensatory-leave", "UL": "unpaid-leave", "ML": "maternity-decision"}.get(obj.leave_type.leave_type_code)
        if expected != spec["slug"]:
            raise Http404("Loại đơn không khớp với mẫu; chọn đúng mẫu nghỉ.")
        values.update(_employee_data(obj.employee))
        values.update(from_date=obj.from_date, to_date=obj.to_date, reason=obj.reason or "")
        source_label = "Đơn nghỉ – " + obj.get_status_display()
    elif selector == "candidate_id":
        if spec["slug"] not in ("candidate-interview", "candidate-score-summary") or not has_permission(user, "manage_hr"):
            raise PermissionDenied()
        from apps.recruitment.models import Candidate
        obj = get_object_or_404(Candidate, pk=pk)
        values = {"_candidate_pk": obj.pk, "_candidate_code": obj.candidate_code, "full_name": obj.full_name, "phone": obj.phone_number, "email": obj.email, "address": obj.current_address or ""}
        if spec["slug"] == "candidate-score-summary":
            tables["results"] = [{"candidate": obj.full_name, "candidate_code": obj.candidate_code}]
        source_label = "Ứng viên " + obj.candidate_code
    elif selector == "inventory_id":
        if spec["slug"] != "asset-inventory" or not has_permission(user, "view_asset"):
            raise PermissionDenied()
        from apps.asset.models import InventorySession
        obj = get_object_or_404(InventorySession, pk=pk)
        values = {"session_no": obj.session_name, "inventory_date": timezone.localtime(obj.inventory_datetime).date(), "location": obj.office_name}
        tables["assets"] = []
        for line in obj.lines.select_related("asset__asset_type"):
            if line.asset.is_deleted:
                continue
            row = _asset_row(line.asset)
            row.update(condition=line.get_actual_condition_display() if line.is_counted else "Chưa kiểm đếm", note=line.note or "")
            tables["assets"].append(row)
        tables["members"] = [{"_employee_pk": m.employee.pk, "_position_pk": m.employee.position_id, "name": m.employee.full_name, "position": str(m.employee.position), "role": m.get_role_display()}
            for m in obj.members.select_related("employee__position") if not m.employee.is_deleted]
        source_label = "Đợt kiểm kê " + obj.session_name + " – " + obj.get_status_display()
    elif selector == "disposal_id":
        if spec["group"] != "asset" or spec["slug"] == "asset-inventory" or not has_permission(user, "view_asset"):
            raise PermissionDenied()
        from apps.asset.models import AssetDisposalRequest
        obj = get_object_or_404(AssetDisposalRequest.objects.select_related("decided_by"), pk=pk)
        values = {"request_no": obj.request_no, "document_date": obj.request_date, "location": obj.location_name,
            "disposal_type": obj.get_disposal_type_display(), "reason": obj.reason,
            "decision_no": obj.decision_no or "", "decision_date": obj.decision_date,
            "committee_decision_no": obj.committee_decision_no or "", "destroy_form": obj.destroy_form or "",
            "handling_method": obj.handling_method or ""}
        if spec["slug"] == "asset-destruction-minutes":
            values["reason"] = obj.disposal_reason
        if obj.execution_datetime:
            local = timezone.localtime(obj.execution_datetime)
            values.update(execution_date=local.date(), start_time=local.time().replace(tzinfo=None), end_time=obj.execution_end_time)
        # A draft must never print a source approver as if they signed this copy.
        tables["assets"] = []
        for item in obj.items.select_related("asset__asset_type"):
            if item.asset.is_deleted:
                continue
            row = _asset_row(item.asset)
            row["condition"] = item.damage_description or ""
            tables["assets"].append(row)
        tables["members"] = [{"_employee_pk": m.employee.pk, "_position_pk": m.employee.position_id, "name": m.employee.full_name, "position": str(m.employee.position), "role": m.get_role_display(), "participation": m.get_participation_display()}
            for m in obj.members.select_related("employee__position") if not m.employee.is_deleted]
        source_label = "Đề nghị " + obj.request_no + " – " + obj.get_status_display()
    elif selector == "lifecycle_id":
        if spec["group"] != "personnel" or not has_permission(user, "manage_lifecycle_case"):
            raise PermissionDenied()
        from apps.lifecycle.models import EmployeeLifecycleCase
        obj = get_object_or_404(EmployeeLifecycleCase.objects.select_related("employee__department", "employee__position"), pk=pk)
        if obj.employee.is_deleted:
            raise Http404()
        values = _employee_template_data(user, spec, obj.employee)
        values["leave_date"] = obj.effective_date if obj.case_type == "Offboarding" else obj.employee.leave_date
        source_label = "Hồ sơ vòng đời nhân sự – " + obj.get_status_display()
    return values, tables, source_label
