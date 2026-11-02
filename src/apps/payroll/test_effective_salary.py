"""Current compensation follows effective dates, including scheduled raises."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import Client, override_settings
from django.urls import reverse

from apps.portal import tests_review_20261008 as fixtures
from apps.payroll.models import EmployeeSalary


@override_settings(MOBILE_API_ENABLED=True, AXES_ENABLED=False)
class EffectiveSalaryTests(fixtures.Review20261008Fixtures):
    def setUp(self):
        self.employee = self.make_employee('SALARY-B')
        self.user = self.make_user('EMPLOYEE', self.employee, 'salary-b-employee')
        self.hr = self.make_user('HR_MANAGER', self.make_employee('SALARY-HR'), 'salary-b-hr')
        self.finance = self.make_user('FINANCE_OFFICER', self.make_employee('SALARY-FIN'), 'salary-b-finance')

    def mobile_salary(self):
        client = Client()
        response = client.post('/api/mobile/v1/login/',
            {'username': self.user.username, 'password': 'test-password'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + response.json()['token']
        result = client.get('/api/mobile/v1/my-profile/')
        self.assertEqual(result.status_code, 200)
        return result.json()['salary']

    def test_scheduled_raise_via_hr_form_is_not_current_on_mobile_or_web(self):
        old = EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=100,
                                            effective_date=date(2020, 1, 1))
        self.client.force_login(self.hr)
        response = self.client.post(reverse('portal:hr_salary_create', args=[self.employee.pk]),
                                   {'current_basic_salary': '200', 'effective_date': '2099-01-01'})
        self.assertEqual(response.status_code, 302)
        old.refresh_from_db()
        self.assertEqual((old.status, old.end_date), ('Ended', date(2098, 12, 31)))
        salary = self.mobile_salary()
        self.assertEqual(Decimal(salary['basic']), Decimal('100'))
        self.assertEqual(salary['effective_date'], '2020-01-01')
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('portal:profile')).context['current_salary'].pk, old.pk)
        self.client.force_login(self.finance)
        response = self.client.get(reverse('portal:finance_salary_list'))
        self.assertEqual([row.pk for row in response.context['salaries']], [old.pk])

    def test_expired_and_future_only_salary_are_absent(self):
        EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=100,
            effective_date=date(2000, 1, 1), end_date=date(2001, 1, 1), status='Ended')
        EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=200,
            effective_date=date(2099, 1, 1))
        self.assertIsNone(self.mobile_salary())
        self.client.force_login(self.finance)
        self.assertFalse(list(self.client.get(reverse('portal:finance_salary_list')).context['salaries']))

    def test_start_and_end_dates_are_inclusive_and_no_salary_is_absent(self):
        self.assertIsNone(self.mobile_salary())
        EmployeeSalary.objects.create(employee=self.employee, current_basic_salary=100,
            effective_date=date(2025, 1, 1), end_date=date(2025, 1, 31), status='Ended')
        for day, amount in [(date(2024, 12, 31), None), (date(2025, 1, 1), '100'),
                            (date(2025, 1, 31), '100'), (date(2025, 2, 1), None)]:
            with self.subTest(day=day), patch('django.utils.timezone.localdate', return_value=day):
                salary = self.mobile_salary()
                self.assertEqual(Decimal(salary['basic']) if salary else None,
                                 Decimal(amount) if amount else None)
