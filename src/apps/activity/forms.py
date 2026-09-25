from django import forms

from apps.activity.models import Activity
from apps.document.models import OfficialDispatch
from apps.hrm.models import Employee
from apps.project.models import Project


class ActivityForm(forms.ModelForm):
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
