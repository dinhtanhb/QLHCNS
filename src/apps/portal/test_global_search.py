from django.urls import reverse
from django.test import TestCase
from apps.portal import test_home_dashboard as fixtures
from apps.hrm.models import Employee
from apps.organization.models import Department
from apps.portal.views.search import PAGES
from apps.security.permissions import has_permission


class GlobalSearchTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_scopes_email_routes_and_anonymous(self):
        url = reverse('portal:global_search')
        self.assertEqual(self.client.get(url).status_code, 302)
        hr = self.user('HR_MANAGER', True)
        person = self.user('EMPLOYEE', True)
        manager = self.user('DEPT_MANAGER', True)
        outsider = self.user('DIRECTOR', True)
        other = Department.objects.create(organization=self.department.organization, department_code='OTHER', department_name='Other')
        Employee.objects.filter(pk=outsider.employee_id).update(department=other)
        for account, expected in ((hr, 4), (manager, 3), (person, 1)):
            self.client.force_login(account)
            result = self.client.get(url, {'q':'@example.test'})
            self.assertEqual(len(result.context['search_people']), expected)
        self.client.force_login(person)
        result = self.client.get(url, {'q':'hop dong'})
        self.assertEqual(result.context['search_pages'], [])
        self.client.force_login(hr)
        result = self.client.get(url, {'q':'hop dong'})
        self.assertEqual(result.context['search_pages'][0]['href'], reverse('portal:hr_contract_list'))
        self.assertEqual(self.client.post(url, {'q':'test'}).status_code, 405)

    def test_limit_deleted_escape_and_minimum(self):
        hr = self.user('HR_MANAGER', True)
        self.client.force_login(hr)
        url = reverse('portal:global_search')
        self.assertEqual(self.client.get(url, {'q':'x'}).context['search_people'], [])
        response = self.client.get(url, {'q':'<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertIn('no-store', response['Cache-Control'])
        Employee.objects.filter(pk=hr.employee_id).update(is_deleted=True)
        self.assertEqual(self.client.get(url, {'q':'@example.test'}).context['search_people'], [])
        self.assertEqual(len(self.client.get(url, {'q':'a'*120}).context['search_query']), 100)

    def test_all_navigation_routes_and_bounded_results(self):
        # Resolve every indexed page to detect stale navigation entries.
        for _, route, _ in PAGES:
            self.assertTrue(reverse('portal:'+route))
        hr = self.user('HR_MANAGER', True)
        self.client.force_login(hr)
        for i in range(25):
            Employee.objects.create(employee_code=f'SEARCH-{i}', first_name='Giả',last_name='Search',full_name=f'Search {i}',
                date_of_birth='1990-01-01',gender='Other',national_id=f'SEARCH-{i}',company_email=f'search{i}@example.test',
                mobile_phone='0000000000',join_date='2020-01-01',department=self.department,position=self.position)
        result = self.client.get(reverse('portal:global_search'), {'q':'Search'})
        self.assertEqual(len(result.context['search_people']), 20)
        self.assertTrue(result.context['search_more'])
