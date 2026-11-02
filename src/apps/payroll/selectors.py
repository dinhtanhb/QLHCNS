"""Effective salary intervals, independent of the scheduling status label."""
from django.db.models import OuterRef, Q, Subquery

from .models import EmployeeSalary


def salaries_on(day, queryset=None):
    records = EmployeeSalary.objects.all() if queryset is None else queryset
    return records.filter(effective_date__lte=day).filter(Q(end_date__isnull=True) | Q(end_date__gte=day))


def current_salaries(day):
    """One latest effective record per employee, keeping the result lazy."""
    latest = salaries_on(day).filter(employee_id=OuterRef('employee_id')).order_by('-effective_date', '-pk')
    return salaries_on(day).filter(pk=Subquery(latest.values('pk')[:1]))


def salary_for(employee, day):
    return salaries_on(day, employee.salaries.all()).order_by('-effective_date', '-pk').first()


def salary_amounts_for_dates(effective_dates):
    """Bulk payroll selection; a mid-period hire uses their joining date."""
    if not effective_dates:
        return {}
    records = EmployeeSalary.objects.filter(employee_id__in=effective_dates, effective_date__lte=max(effective_dates.values()))
    records = records.filter(Q(end_date__isnull=True) | Q(end_date__gte=min(effective_dates.values())))
    amounts = {}
    for salary in records.order_by('effective_date', 'pk'):
        day = effective_dates[salary.employee_id]
        if salary.effective_date <= day and (salary.end_date is None or salary.end_date >= day):
            amounts[salary.employee_id] = salary.current_basic_salary
    return amounts
