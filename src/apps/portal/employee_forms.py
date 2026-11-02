"""Bound edit input, isolated from the employee used by the surrounding page."""
from django.forms import ModelForm

from apps.hrm.models import Employee


class EmployeeEditForm(ModelForm):
    class Meta:
        model = Employee
        fields = ('employee_code', 'first_name', 'last_name', 'full_name', 'date_of_birth', 'gender',
                  'national_id', 'tax_code', 'social_insurance_no', 'company_email', 'personal_email',
                  'mobile_phone', 'address', 'join_date', 'leave_date', 'department', 'position',
                  'job_title', 'manager', 'employment_status')
