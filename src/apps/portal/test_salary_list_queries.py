"""Salary list query cost and pagination through the actual Finance view."""
from datetime import date

from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.payroll.models import EmployeeSalary
from apps.portal import tests_review_20261008 as fixtures


@override_settings(AXES_ENABLED=False)
class SalaryListQueryTests(fixtures.Review20261008Fixtures):
    def setUp(self):
        self.client.force_login(self.make_user('FINANCE_OFFICER', self.make_employee('QUERY-FIN'), 'salary-query-b'))
        self.url = reverse('portal:finance_salary_list')

    def add_rows(self, start, end):
        for index in range(start, end):
            EmployeeSalary.objects.create(employee=self.make_employee(f'QUERY-{index}'),
                current_basic_salary=100, effective_date=date(2020, 1, 1))

    def query_cost(self):
        cache.clear()
        self.client.get(self.url)  # Consistent warm middleware/template state for both sizes.
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        department = [q for q in queries if 'FROM "tblDepartment"' in q['sql']]
        return len(queries), len(department)

    def test_query_count_is_bounded_when_salary_population_doubles(self):
        self.add_rows(0, 13)
        small = self.query_cost()
        self.add_rows(13, 26)
        large = self.query_cost()
        print('SALARY_QUERY_GROWTH', {'rows13': small, 'rows26': large}, flush=True)
        self.assertEqual(small[1], 0, 'Department must be joined rather than fetched once per row')
        self.assertEqual(large, small)

    def test_pagination_preserves_query_parameters_and_covers_all_rows(self):
        self.add_rows(0, 26)
        first = self.client.get(self.url, {'q': 'Synthetic', 'department': self.department.pk})
        self.assertEqual(len(first.context['salaries']), 20)
        self.assertEqual(first.context['page_obj'].paginator.count, 26)
        self.assertContains(first, 'q=Synthetic&amp;department=')
        last = self.client.get(self.url, {'page': 2})
        self.assertEqual(len(last.context['salaries']), 6)
        self.assertFalse(set(s.pk for s in first.context['salaries']) & set(s.pk for s in last.context['salaries']))
