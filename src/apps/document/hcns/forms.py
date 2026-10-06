from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from django.utils import timezone

from .catalog import fields_for, tables_for
from .money import amount_in_words


def make_field(spec):
    options = {"label": spec["label"], "required": False}
    kind = spec.get("kind", "text")
    if kind == "date":
        return forms.DateField(**options, input_formats=["%Y-%m-%d"], widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    if kind == "time":
        return forms.TimeField(**options, widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}))
    if kind == "decimal":
        return forms.DecimalField(**options, min_value=0, max_value=spec.get("maximum", Decimal("9999999999999")),
            max_digits=18, decimal_places=4, widget=forms.NumberInput(attrs={"step": "any"}))
    if kind == "integer":
        return forms.IntegerField(**options, min_value=0, max_value=spec.get("maximum", 999999))
    if kind == "choice":
        return forms.ChoiceField(**options, choices=spec["choices"])
    if kind == "email":
        return forms.EmailField(**options, max_length=254)
    widget = forms.Textarea(attrs={"rows": 4}) if kind == "textarea" else forms.TextInput()
    return forms.CharField(**options, max_length=spec.get("max_length", 5000 if kind == "textarea" else 500), widget=widget)


class DraftForm(forms.Form):
    def __init__(self, spec, *args, **kwargs):
        self.spec = spec
        self.user = kwargs.pop("user", None)
        initial = {f["key"]: f.get("initial", f["choices"][0][0] if f.get("kind") == "choice" else "") for f in fields_for(spec)}
        if any(f["key"] == "document_date" for f in fields_for(spec)):
            initial["document_date"] = timezone.localdate()
        initial.update(kwargs.pop("initial", {}))
        super().__init__(*args, initial=initial, **kwargs)
        self.fields = {f["key"]: make_field(f) for f in fields_for(spec)}
        self.employee_choices = {}
        if self.user is not None:
            from .choices import configure_choices
            configure_choices(self, self.user)
        if "salary_words" in self.fields:
            self.fields["salary"] = forms.DecimalField(label=self.fields["salary"].label, required=False,
                min_value=0, max_value=9999999999999, max_digits=13, decimal_places=0,
                widget=forms.NumberInput(attrs={"step": "1"}))
            self.fields["salary_words"].widget.attrs["readonly"] = True
            self.fields["salary_words"].disabled = True
            try:
                self.initial["salary_words"] = amount_in_words(self.initial.get("salary"))
            except (ValueError, InvalidOperation):
                self.initial["salary_words"] = ""

    def clean(self):
        data = super().clean()
        if self.user is not None:
            from .choices import clean_choices
            clean_choices(self, data)
        if "salary_words" in self.fields:
            data["salary_words"] = amount_in_words(data.get("salary"))
            self.initial["salary_words"] = data["salary_words"]
        if data.get("from_date") and data.get("to_date") and data["to_date"] < data["from_date"]:
            self.add_error("to_date", "Ngày kết thúc phải từ ngày bắt đầu trở đi.")
        if data.get("start_time") and data.get("end_time") and data["end_time"] < data["start_time"]:
            self.add_error("end_time", "Giờ kết thúc phải từ giờ bắt đầu trở đi.")
        return data


def make_table_formsets(spec, data=None, initial=None, user=None):
    initial = initial or {}
    result = []
    for table_spec in tables_for(spec):
        rows = initial.get(table_spec["key"], table_spec["rows"])
        columns = [col for col in table_spec["columns"] if not col.get("locked")]
        attrs = {col["key"]: make_field(col) for col in columns}
        if user is not None:
            from .choices import configure_choices, clean_choices, reference_sets
            refs = reference_sets(user)
            # Capture each table's key independently; formsets are instantiated
            # lazily, after the loop has moved to another table.
            def row_init(self, *args, _key=table_spec["key"], _refs=refs, **kwargs):
                forms.Form.__init__(self, *args, **kwargs)
                self.spec = spec
                configure_choices(self, user, references=_refs, table_key=_key)

            def row_clean(self):
                return clean_choices(self, forms.Form.clean(self))

            attrs.update(__init__=row_init, clean=row_clean)
        row_form = type("HCNSRowForm", (forms.Form,), attrs)
        minimum = len(table_spec["rows"]) if table_spec["fixed"] else 0
        factory = formset_factory(row_form, extra=0, min_num=minimum, validate_min=table_spec["fixed"],
            max_num=table_spec["max_rows"], validate_max=True, absolute_max=table_spec["max_rows"])
        formset = factory(data=data, initial=rows, prefix=table_spec["key"])
        result.append({"spec": table_spec, "formset": formset, "rows": rows})
    return result


def clean_tables(bound_tables):
    result = {}
    valid = True
    for entry in bound_tables:
        spec, formset = entry["spec"], entry["formset"]
        if not formset.is_valid():
            valid = False
            continue
        rows = []
        for i, form in enumerate(formset.forms):
            row = dict(form.cleaned_data)
            if spec["fixed"]:
                for col in spec["columns"]:
                    if col.get("locked"):
                        row[col["key"]] = spec["rows"][i].get(col["key"], "")
            if spec["key"] == "scores" and row.get("score") is not None and row["score"] > Decimal(str(row["maximum"])):
                form.add_error("score", "Điểm vượt quá điểm tối đa của tiêu chí.")
                valid = False
            has_values = any(value is not None and value != "" for value in row.values())
            if spec["key"] == "results" and has_values:
                for required_key in ("candidate_code", "candidate", "interviewer"):
                    if not row.get(required_key):
                        form.add_error(required_key, "Nhập mã, tên ứng viên và người chấm để tổng hợp đúng người.")
                        valid = False
            if spec["fixed"] or has_values:
                rows.append(row)
        result[spec["key"]] = rows
        if spec["key"] == "results":
            names = {}
            for form in formset.forms:
                row = form.cleaned_data
                code, name = row.get("candidate_code"), row.get("candidate")
                if code and name and code in names and names[code] != name:
                    form.add_error("candidate", "Cùng mã ứng viên phải có cùng họ tên.")
                    valid = False
                elif code and name:
                    names[code] = name
    return valid, result


def initial_document_data(spec, initial, table_initial, user=None):
    """Validate defaults too; drafts with zero are not confused with blank cells."""
    form = DraftForm(spec, initial=initial, user=user)
    values = {}
    for key, form_field in form.fields.items():
        value = form.initial.get(key, "")
        values[key] = form_field.clean(value)
    form.cleaned_data = values
    form.clean()
    if form.errors:
        raise ValidationError("Invalid source field combination.")
    rows_by_key = {}
    for table_spec in tables_for(spec):
        rows = []
        for row in table_initial.get(table_spec["key"], table_spec["rows"]):
            cleaned = {key: value for key, value in row.items() if key in ("_employee_pk", "_asset_pk", "_candidate_pk", "_position_pk")}
            for col in table_spec["columns"]:
                value = row.get(col["key"], "")
                cleaned[col["key"]] = value if col.get("locked") else make_field(col).clean(value)
            rows.append(cleaned)
        rows_by_key[table_spec["key"]] = rows
    if user is not None:
        from .choices import configure_choices, clean_choices, reference_sets
        refs = reference_sets(user)
        for table_spec in tables_for(spec):
            for row in rows_by_key[table_spec["key"]]:
                row_form = forms.Form(initial=row)
                row_form.spec = spec
                row_form.fields = {col["key"]: make_field(col) for col in table_spec["columns"] if not col.get("locked")}
                configure_choices(row_form, user, references=refs, table_key=table_spec["key"])
                row_form.cleaned_data = {key: field.clean(row_form.initial.get(key, "")) for key, field in row_form.fields.items()}
                clean_choices(row_form, row_form.cleaned_data)
                if row_form.errors:
                    raise ValidationError("Invalid source reference combination.")
                row.update(row_form.cleaned_data)
    return values, rows_by_key
