from django.urls import reverse
from django.test import TestCase
from apps.portal import test_home_dashboard as fixtures
from apps.hrm.models import Employee
from apps.organization.models import Department
from apps.portal.views.search import PAGES
from apps.security.permissions import has_permission
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.db.models import Q
from unittest.mock import patch
import json
from apps.portal.views import search as search_views


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

    def test_page_guard_matrix(self):
        mismatches = []
        roles = ('EMPLOYEE', 'DEPT_MANAGER', 'HR_OFFICER', 'HR_MANAGER',
                 'DIRECTOR', 'FINANCE_OFFICER', 'SYS_ADMIN', 'SUPERUSER')
        for role in roles:
            user = self.user(role, True)
            if role == 'SUPERUSER':
                user.is_superuser = True
                user.save(update_fields=['is_superuser'])
            self.client.force_login(user)
            for label, route, permission in PAGES:
                url = reverse('portal:' + route)
                result = self.client.get(reverse('portal:global_search'), {'q': label})
                listed = any(p['href'] == url for p in result.context['search_pages'])
                target = self.client.get(url)
                if listed != (target.status_code == 200):
                    mismatches.append([role, route, listed, target.status_code])
                with self.subTest(role=role, route=route):
                    self.assertEqual(listed, target.status_code == 200)
        print('SEARCH_PAGE_GUARD_MISMATCHES=' + json.dumps(mismatches))

    def test_query_measurement(self):
        counts = {}
        for role in ('EMPLOYEE', 'DEPT_MANAGER', 'HR_OFFICER', 'HR_MANAGER',
                     'DIRECTOR', 'FINANCE_OFFICER', 'SYS_ADMIN', 'SUPERUSER'):
            user = self.user(role, True)
            if role == 'SUPERUSER':
                user.is_superuser = True
                user.save(update_fields=['is_superuser'])
            self.client.force_login(user)
            self.client.get(reverse('portal:global_search'))  # Login/lazy warm-up is outside measurement.
            def old_matches(scope, query):
                return scope.filter(Q(full_name__icontains=query) | Q(employee_code__icontains=query)
                                    | Q(company_email__icontains=query)).select_related('department').order_by('full_name', 'pk')[:21], False
            measured = {}
            for version in ('before', 'after'):
                # The previous matcher on the same final view/fixture isolates
                # the extra SELECT rather than comparing different login state.
                with patch.object(search_views, 'people_matches', old_matches if version == 'before' else search_views.people_matches):
                    with CaptureQueriesContext(connection) as queries:
                        self.client.get(reverse('portal:global_search'), {'q': 'gia'})
                measured[version] = sum(q['sql'].lstrip().upper().startswith('SELECT') for q in queries)
            self.assertLessEqual(measured['after'], measured['before'] + 1)
            counts[role] = measured
        print('SEARCH_QUERY_COUNTS=' + json.dumps(counts))

    def test_accent_case_and_safe_projection(self):
        hr = self.user('HR_MANAGER', True)
        person = self.user('EMPLOYEE', True)
        Employee.objects.filter(pk=person.employee_id).update(full_name='Nguyễn Đặng Thị Ánh',
            employee_code='ĐẶNG-ÁNH', company_email='nguyễn.đặng@example.test')
        self.client.force_login(hr)
        for query in ('nguyen', 'NGUYỄN', 'dang', 'ĐẶNG', 'thi anh', 'dang-anh', 'nguyen.dang'):
            response = self.client.get(reverse('portal:global_search'), {'q':query})
            self.assertEqual([r['code'] for r in response.context['search_people']], ['ĐẶNG-ÁNH'])
            self.assertFalse(response.context['search_limited'])
        with CaptureQueriesContext(connection) as queries:
            matches, limited = search_views.people_matches(Employee.objects.all(), 'nguyen')
            result = list(matches)
            self.assertEqual(result[0].department.department_name, self.department.department_name)
        self.assertFalse(limited)
        self.assertEqual(len(queries), 2)
        for item in queries:
            self.assertNotIn('NationalID', item['sql'])
            self.assertNotIn('MobilePhone', item['sql'])
            self.assertNotIn('BasicSalary', item['sql'])

    def test_scan_ceiling_and_scope_before_matching(self):
        manager = self.user('DEPT_MANAGER', True)
        outsider = self.user('EMPLOYEE', True)
        other = Department.objects.create(organization=self.department.organization, department_code='OUT', department_name='Other')
        Employee.objects.filter(pk=outsider.employee_id).update(department=other, full_name='Nguyễn Ngoài Phạm Vi')
        self.client.force_login(manager)
        self.assertEqual(self.client.get(reverse('portal:global_search'), {'q':'nguyen'}).context['search_people'], [])
        self.assertFalse(self.client.get(reverse('portal:global_search'), {'q':'nguyen'}).context['search_limited'])
        hr = self.user('HR_MANAGER', True)
        self.client.force_login(hr)
        with patch.object(search_views, 'PEOPLE_SCAN_LIMIT', 1):
            response = self.client.get(reverse('portal:global_search'), {'q':'home'})
        self.assertTrue(response.context['search_limited'])
        self.assertContains(response, 'Tìm không dấu bị giới hạn do số hồ sơ lớn')
        self.assertLessEqual(len(response.context['search_people']), 20)

    def test_unlinked_profile_change_guard(self):
        for role in ('EMPLOYEE', 'DEPT_MANAGER', 'HR_OFFICER', 'HR_MANAGER',
                     'DIRECTOR', 'FINANCE_OFFICER', 'SYS_ADMIN', 'SUPER_ADMIN', 'SUPERUSER'):
            user = self.user(role, False)
            if role == 'SUPERUSER':
                user.is_superuser = True
                user.save(update_fields=['is_superuser'])
            self.client.force_login(user)
            response = self.client.get(reverse('portal:global_search'), {'q':'Yêu cầu cập nhật hồ sơ'})
            href = reverse('portal:profile_change_request_list')
            listed = any(p['href'] == href for p in response.context['search_pages'])
            self.assertEqual(listed, self.client.get(href).status_code == 200, role)
