"""KPI destinations must explain the same scoped set, without contract gating."""
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.portal import test_home_dashboard as fixtures
from apps.portal.dashboard_data import dashboard_snapshot
from apps.leave.models import LeaveRequest, LeaveType
from apps.hrm.models import Employee


class DashboardDrilldownTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_all_four_counts_match_destinations_without_contract(self):
        hr = self.user('HR_MANAGER', True)
        employee = self.user('EMPLOYEE', True)
        probation = self.user('PROBATION', True)
        Employee.objects.filter(pk=probation.employee_id).update(employment_status='Probation')
        kind = LeaveType.objects.create(leave_type_code='DETAIL', leave_type_name='Giả')
        today = timezone.localdate()
        for _ in range(2):
            LeaveRequest.objects.create(employee=employee.employee, leave_type=kind, status='Approved', from_date=today, to_date=today)
        self.client.force_login(hr)
        snapshot = dashboard_snapshot(hr, hr.employee)
        for metric in snapshot['metrics']:
            response = self.client.get(metric['href'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].paginator.count, metric['value'])
        # The contracted directory policy remains independent of KPI status totals.
        self.assertEqual(self.client.get(reverse('portal:hr_employee_list')).context['page_obj'].paginator.count, 0)
        date_response = self.client.get(reverse('portal:dashboard_people'), {'metric':'approved','on_date':(today+timedelta(days=1)).isoformat()})
        self.assertEqual(date_response.context['page_obj'].paginator.count, 0)

    def test_scope_permission_invalid_filters_and_search(self):
        manager = self.user('DEPT_MANAGER', True)
        person = self.user('EMPLOYEE', True)
        self.client.force_login(manager)
        url = reverse('portal:dashboard_people')
        result = self.client.get(url, {'metric':'active','q':person.employee.employee_code,'department':'999'})
        self.assertEqual(result.context['page_obj'].paginator.count, 1)
        self.assertContains(result, 'name="metric" value="active"')
        self.assertEqual(self.client.get(url, {'metric':'approved'}).status_code, 403)
        self.assertEqual(self.client.get(url, {'metric':'salary'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'on_date':'2026-02-31'}).status_code, 400)
        manager.employee.managed_departments.clear()
        self.assertEqual(self.client.get(url).context['page_obj'].paginator.count, 0)
        self.client.force_login(person)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_pagination_preserves_metric_date_and_search(self):
        hr = self.user('HR_MANAGER', True)
        for i in range(22):
            Employee.objects.create(employee_code=f'DETAIL-{i}', first_name='Giả',last_name='Thử',full_name=f'Detail {i}',
                date_of_birth='1990-01-01',gender='Other',national_id=f'DETAIL-{i}',company_email=f'detail{i}@example.test',
                mobile_phone='0000000000',join_date='2020-01-01',department=self.department,position=self.position)
        self.client.force_login(hr)
        response = self.client.get(reverse('portal:dashboard_people'), {'metric':'active','on_date':'2026-10-13','q':'DETAIL-'})
        self.assertEqual(response.context['page_obj'].paginator.count, 22)
        self.assertContains(response,'metric=active&amp;on_date=2026-10-13&amp;q=DETAIL-&amp;page=2')
