from django import forms
from pathlib import Path

from apps.activity.models import Activity, ActivityProposal
from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
from apps.document.models import OfficialDispatch
from apps.hrm.models import Employee
from apps.project.models import Project
from apps.security.models import User


class ActivityProposalUploadForm(forms.ModelForm):
    class Meta:
        model = ActivityProposal
        fields = ("proposal_pdf", "budget_pdf")
        widgets = {
            "proposal_pdf": forms.ClearableFileInput(attrs={"class": "block w-full rounded-lg border border-gray-400 bg-white px-3 py-2"}),
            "budget_pdf": forms.ClearableFileInput(attrs={"class": "block w-full rounded-lg border border-gray-400 bg-white px-3 py-2"}),
        }

    def clean(self):
        cleaned = super().clean()
        expected = {
            "proposal_pdf": {".pdf"},
            "budget_pdf": {".pdf"},
        }
        for field, extensions in expected.items():
            uploaded = cleaned.get(field)
            if uploaded and Path(uploaded.name).suffix.lower() not in extensions:
                self.add_error(field, "Tệp không đúng định dạng yêu cầu: " + ", ".join(sorted(extensions)))
        return cleaned


class ActivityProposalSendForm(forms.Form):
    approver = forms.ModelChoiceField(
        label="Giám đốc dự án nhận duyệt", queryset=User.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["approver"].queryset = User.objects.filter(
            is_active=True, role__role_code="DIRECTOR",
        ).select_related("employee", "role").order_by("last_name", "first_name", "username")
        self.fields["approver"].widget.attrs["class"] = "mt-1 block w-full rounded-lg border border-gray-400 bg-white px-3 py-2"


class ActivityProposalDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        label="Quyết định", choices=(("Approved", "Phê duyệt"), ("ChangesRequested", "Yêu cầu chỉnh sửa")),
    )
    comment = forms.CharField(label="Ý kiến", required=False, widget=forms.Textarea(attrs={"rows": 4}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "ChangesRequested" and not cleaned.get("comment", "").strip():
            self.add_error("comment", "Vui lòng nêu nội dung cần chỉnh sửa.")
        return cleaned


class ActivityForm(forms.ModelForm):
    activity_code = forms.ChoiceField(label="Mã hoạt động")

    class Meta:
        model = Activity
        fields = (
            "activity_code",
            "activity_name",
            "project",
            "location",
            "participants",
            "purpose",
            "expected_output",
            "start_date",
            "end_date",
            "lead_cbda",
            "coordinator",
            "outgoing_document",
            "status",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "purpose": forms.Textarea(attrs={"rows": 3}),
            "expected_output": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code_choices = [(code, code) for code in ACTIVITY_CODE_NAMES]
        if self.instance.pk and self.instance.activity_code not in ACTIVITY_CODE_NAMES:
            code_choices.insert(0, (self.instance.activity_code, self.instance.activity_code))
        self.fields["activity_code"].choices = [("", "---------"), *code_choices]
        self.fields["activity_name"].widget.attrs.update({
            "readonly": "readonly",
            "placeholder": "Tự động điền theo mã hoạt động",
            "aria-describedby": "activity-name-help",
        })
        self.fields["activity_name"].help_text = "Tên hoạt động được điền tự động theo mã đã chọn."
        self.fields["project"].queryset = Project.objects.filter(is_active=True).order_by("project_name")
        active_employees = Employee.objects.filter(
            employment_status__in=("Active", "Probation")
        ).order_by("full_name")
        self.fields["lead_cbda"].queryset = active_employees
        self.fields["coordinator"].queryset = active_employees
        self.fields["coordinator"].required = True
        self.fields["outgoing_document"].queryset = OfficialDispatch.objects.filter(
            dispatch_type="Outgoing"
        ).order_by("-received_or_sent_date", "-pk")
        self.fields["outgoing_document"].required = False
        self.fields["outgoing_document"].help_text = (
            "Chọn công văn đi đã phát hành. Khi liên kết, IHRMS tự tạo Task báo cáo "
            "và tính hạn 10 ngày làm việc. Có thể bổ sung công văn sau."
        )

        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "mt-1 block w-full rounded-lg border-gray-300 shadow-sm "
                "focus:border-blue-600 focus:ring-blue-600",
            )

    def clean(self):
        cleaned_data = super().clean()
        activity_code = cleaned_data.get("activity_code")
        if activity_code in ACTIVITY_CODE_NAMES:
            cleaned_data["activity_name"] = ACTIVITY_CODE_NAMES[activity_code]
        elif self.instance.pk and activity_code == self.instance.activity_code:
            cleaned_data["activity_name"] = self.instance.activity_name
        return cleaned_data
