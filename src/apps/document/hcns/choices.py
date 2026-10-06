"""Scoped reference pickers shared by all HCNS editors and table rows."""
from django import forms
from django.db.models import Q
from apps.security.permissions import has_permission


EMPLOYEE_KEYS = {"full_name", "signer", "manager", "recipient", "interviewer"}
POSITION_KEYS = {"position", "new_position", "manager_position", "recipient_position"}


class ReferenceField(forms.ModelChoiceField):
    def __init__(self, *args, value_attribute=None, **kwargs):
        self.value_attribute = value_attribute
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        if hasattr(obj, "employee_code"):
            return f"{obj.full_name} · {obj.employee_code} · {obj.position}"
        return str(obj)

    def printable(self, obj):
        return getattr(obj, self.value_attribute) if self.value_attribute else str(obj)

    def source_id(self, value):
        if value in (None, ""):
            return ""
        if hasattr(value, "pk"):
            return value.pk
        # Source values are converted separately from POST validation. Free text
        # sent by a client never becomes an extra allowed option.
        matches = [obj.pk for obj in self.queryset if self.printable(obj) == value]
        return matches[0] if len(matches) == 1 else value


def reference_sets(user, initial=None):
    from apps.hrm.models import Employee
    from apps.organization.models import Department, Position
    from apps.project.models import Project
    initial = initial or {}
    employees = Employee.objects.select_related("department", "position", "manager__position").order_by("full_name", "employee_code")
    if not (has_permission(user, "view_all_employees") and has_permission(user, "export_employee_data")):
        own = getattr(user, "employee", None)
        employees = employees.filter(pk=own.pk) if own and not own.is_deleted else employees.none()
    positions = Position.objects.filter(Q(is_active=True) | Q(pk__in=employees.values("position_id")) |
                                        Q(pk__in=[initial.get("_position_pk"), initial.get("_new_position_pk")])).order_by("position_name", "pk")
    departments = Department.objects.filter(Q(is_active=True) | Q(pk__in=employees.values("department_id")) |
                                            Q(pk=initial.get("_department_pk"))).order_by("department_name", "pk")
    result = {"employees": employees, "positions": positions, "departments": departments,
              "projects": Project.objects.filter(is_active=True).order_by("project_name", "pk")}
    if has_permission(user, "manage_hr"):
        from apps.recruitment.models import Candidate
        result["candidates"] = Candidate.objects.order_by("full_name", "candidate_code")
    if has_permission(user, "view_asset"):
        from apps.asset.models import Asset, AssetType
        result["assets"] = Asset.objects.select_related("asset_type").order_by("asset_code")
        result["asset_types"] = AssetType.objects.order_by("asset_type_name")
    return result


def configure_choices(form, user, references=None, table_key=None):
    refs = references or reference_sets(user, form.initial)
    form.reference_keys = []
    if table_key == "assets" and form.initial.get("code") and "assets" in refs:
        source = refs["assets"].filter(asset_code=form.initial["code"]).first()
        if source:
            form.initial["_asset_pk"] = source.pk
    if table_key == "results" and form.initial.get("candidate_code") and "candidates" in refs:
        source = refs["candidates"].filter(candidate_code=form.initial["candidate_code"]).first()
        if source:
            form.initial["_candidate_pk"] = source.pk
    for key in list(form.fields):
        pool, attr = None, None
        options = None
        if key == "gender":
            from apps.hrm.models import Employee
            options = [(label, label) for _, label in Employee.GENDER_CHOICES]
        elif table_key == "members" and key in ("role", "participation"):
            from apps.asset.models import InventoryMember, AssetDisposalRequestMember
            model = InventoryMember if form.spec["slug"] == "asset-inventory" else AssetDisposalRequestMember
            choices = model._meta.get_field(key).choices if key == "role" or model is AssetDisposalRequestMember else ()
            options = [(label, label) for _, label in choices]
        elif table_key == "assets" and key == "condition" and form.spec["slug"] == "asset-inventory":
            from apps.asset.models import Asset
            options = [(label, label) for _, label in Asset.CONDITION_CHOICES] + [("Chưa kiểm đếm", "Chưa kiểm đếm")]
        if options is not None:
            form.fields[key] = forms.ChoiceField(label=form.fields[key].label, required=False, choices=[("", "— Chọn —")] + options)
            continue
        if table_key == "assets" and key in ("name", "code"):
            pool, attr = "assets", "asset_name" if key == "name" else "asset_code"
        elif table_key == "assets" and key == "type":
            pool = "asset_types"
        elif table_key == "results" and key in ("candidate", "candidate_code"):
            pool, attr = "candidates", "full_name" if key == "candidate" else "candidate_code"
        elif table_key in ("members", "panel") and key == "name":
            pool, attr = "employees", "full_name"
        elif key == "full_name" and form.spec["slug"] == "candidate-interview":
            pool, attr = "candidates", "full_name"
        elif key in EMPLOYEE_KEYS:
            pool, attr = "employees", "full_name"
        elif key in POSITION_KEYS:
            pool = "positions"
        elif key in ("department", "workplace"):
            pool = "departments"
        elif key == "project":
            pool = "projects"
        if pool is None:
            continue
        label = form.fields[key].label
        if pool not in refs:
            from apps.hrm.models import Employee
            queryset = Employee.objects.none()
        else:
            queryset = refs[pool]
        if table_key in ("members", "panel") and pool == "employees" and form.initial.get("_employee_pk"):
            # A readable asset source already exposes its recorded committee.
            # Add only that source participant, never the whole HR directory.
            from apps.hrm.models import Employee
            queryset = Employee.objects.select_related("position").filter(
                Q(pk__in=queryset.values("pk")) | Q(pk=form.initial["_employee_pk"])).order_by("full_name", "employee_code")
        if pool == "positions" and form.initial.get("_position_pk"):
            from apps.organization.models import Position
            queryset = Position.objects.filter(Q(pk__in=queryset.values("pk")) | Q(pk=form.initial["_position_pk"])).order_by("position_name", "pk")
        field = ReferenceField(queryset=queryset, required=False, label=label, empty_label="— Chọn —", value_attribute=attr)
        field.widget.attrs.update({"data-reference": pool, "data-reference-key": key})
        form.fields[key] = field
        form.reference_keys.append(key)
        metadata = None
        if key in ("full_name", "name"):
            metadata = "_candidate_pk" if pool == "candidates" else "_asset_pk" if pool == "assets" else "_employee_pk"
        elif key in ("candidate", "candidate_code"):
            metadata = "_candidate_pk"
        elif key == "code":
            metadata = "_asset_pk"
        elif key in ("position", "new_position", "department", "manager", "manager_position"):
            metadata = "_" + key + "_pk"
        source = form.initial.get(metadata) if metadata else None
        form.initial[key] = source if source is not None else field.source_id(form.initial.get(key, ""))


def clean_choices(form, data):
    selected = data.get("full_name")
    form.selected_employee = selected if hasattr(selected, "employee_code") else None
    form.selected_candidate = selected if hasattr(selected, "candidate_code") else None
    if form.selected_employee:
        employee = form.selected_employee
        for key in ("position", "department", "new_position"):
            if key in form.fields and not data.get(key):
                obj = employee.position if key == "new_position" else getattr(employee, key)
                if obj.is_deleted:
                    form.add_error(key, "Danh mục trong hồ sơ đã bị xóa. Hãy chọn danh mục còn sử dụng.")
                else:
                    data[key] = obj
    for left, right in (("name", "code"), ("candidate", "candidate_code")):
        if left in form.reference_keys and right in form.reference_keys and data.get(left) and data.get(right):
            if data[left].pk != data[right].pk:
                form.add_error(right, "Mã và tên phải thuộc cùng một hồ sơ.")
    for key in form.reference_keys:
        obj = data.get(key)
        data[key] = form.fields[key].printable(obj) if obj else ""
    return data


def editor_data(form, user, table_initial=None):
    """Return only slots used in this editor, within the export employee scope."""
    from .prefill import _employee_data
    refs = reference_sets(user, form.initial)
    result = {"employees": {}, "candidates": {}, "assets": {}}
    for employee in refs["employees"]:
        result["employees"][str(employee.pk)] = {"position": str(employee.position_id)}
    source_ids = [row["_employee_pk"] for key in ("members", "panel") for row in (table_initial or {}).get(key, []) if row.get("_employee_pk")]
    if source_ids:
        from apps.hrm.models import Employee
        for employee in Employee.objects.filter(pk__in=source_ids):
            result["employees"].setdefault(str(employee.pk), {"position": str(employee.position_id)})
    if "full_name" in form.fields and form.spec["slug"] != "candidate-interview":
        private = bool(set(form.fields) & {"date_of_birth", "national_id", "tax_code", "insurance_no", "phone", "email", "address", "gender", "birth_year"})
        for employee in refs["employees"]:
            profile = _employee_data(employee, private=private)
            profile.update(position=str(employee.position_id), department=str(employee.department_id), new_position=str(employee.position_id))
            if employee.manager_id and not employee.manager.is_deleted:
                profile.update(manager=str(employee.manager_id), manager_position=str(employee.manager.position_id))
            result["employees"][str(employee.pk)] = {key: value.isoformat() if hasattr(value, "isoformat") else value
                                                     for key, value in profile.items() if key in form.fields and key != "full_name"}
    if "candidates" in refs and form.spec["slug"] in ("candidate-interview", "candidate-score-summary"):
        for candidate in refs["candidates"]:
            result["candidates"][str(candidate.pk)] = {"candidate_code": str(candidate.pk), "candidate": str(candidate.pk),
                "phone": candidate.phone_number, "email": candidate.email, "address": candidate.current_address or ""}
    if "assets" in refs and form.spec["group"] == "asset":
        from .prefill import _asset_row
        for asset in refs["assets"]:
            row = _asset_row(asset)
            row.update(name=str(asset.pk), code=str(asset.pk), type=str(asset.asset_type_id))
            result["assets"][str(asset.pk)] = {key: value.isoformat() if hasattr(value, "isoformat") else str(value) if value is not None else "" for key, value in row.items()}
    return result
