"""Owner decision: probation and leave remain employed for payroll."""
from datetime import date
from decimal import Decimal

from django.test import override_settings
from django.urls import reverse

from apps.payroll import tests as fixtures
from apps.payroll.models import EmployeeSalary, Payroll, Payslip
from apps.attendance.models import MonthlyAttendanceSummary
from apps.security.models import Role,User


@override_settings(AXES_ENABLED=False)
class EmployedPayrollTests(fixtures.PayrollTestBase):
    def setUp(self):
        role,_=Role.objects.get_or_create(role_code='FINANCE_OFFICER',defaults={'role_name':'Synthetic Finance'})
        self.client.force_login(User.objects.create_user(username='fix-c-finance',role=role))

    def test_probation_and_paid_unpaid_on_leave_generate_and_lock_without_new_formula(self):
        for index,status in enumerate(['Active','Probation','OnLeave','OnLeave']):
            employee=self.employee if index==0 else self._create_employee('STATUS-'+str(index))
            employee.employment_status=status;employee.save(update_fields=['employment_status'])
            EmployeeSalary.objects.create(employee=employee,current_basic_salary=1000000,effective_date=date(2020,1,1))
            if index==3:
                MonthlyAttendanceSummary.objects.create(employee=employee,year=2025,month=1,
                    unpaid_leave_days=23,status='Approved')
        self.client.post(reverse('portal:finance_payroll_generate',args=[self.period.pk]))
        rows=list(Payroll.objects.filter(payroll_period=self.period).select_related('employee'))
        self.assertEqual(len(rows),4)
        for row in rows:
            row.calculate();row.save()
            self.assertEqual(row.basic_salary,Decimal('1000000'))
            self.assertEqual(row.gross_income,Decimal('0') if row.employee.employee_code=='STATUS-3' else Decimal('1000000'))
        self.client.post(reverse('portal:finance_payroll_lock',args=[self.period.pk]))
        self.period.refresh_from_db();self.assertEqual(self.period.status,'Locked')
        self.assertEqual(Payslip.objects.filter(payroll__payroll_period=self.period).count(),4)

    def test_resigned_employee_is_excluded_even_when_last_day_is_in_period(self):
        self.employee.employment_status='Resigned';self.employee.leave_date=date(2025,1,15)
        self.employee.save(update_fields=['employment_status','leave_date'])
        EmployeeSalary.objects.create(employee=self.employee,current_basic_salary=1000000,effective_date=date(2020,1,1))
        self.client.post(reverse('portal:finance_payroll_generate',args=[self.period.pk]))
        self.assertFalse(Payroll.objects.filter(payroll_period=self.period).exists())
