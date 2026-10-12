from django.test import TestCase
from django.urls import reverse
from apps.portal import tests as portal_tests

class SharedSamplePagesTests(TestCase):
    setUpTestData=classmethod(portal_tests.PortalSensitiveWorkflowTests.setUpTestData.__func__)
    make_user=portal_tests.PortalSensitiveWorkflowTests.make_user
    make_employee=portal_tests.PortalSensitiveWorkflowTests.make_employee

    def test_payroll_form_keeps_post_action_csrf_names_and_labels(self):
        user=self.make_user("FINANCE_OFFICER",None,"shared-finance")
        self.client.force_login(user)
        html=self.client.get(reverse('portal:finance_period_list'))
        self.assertContains(html,'action="'+reverse('portal:finance_period_create')+'"')
        for name in ['payroll_month','payroll_year','csrfmiddlewaretoken']:
            self.assertContains(html,'name="'+name+'"')
        self.assertContains(html,'for="period-month"')
        self.assertContains(html,'for="period-year"')
        self.assertContains(html,'Chưa có kỳ lương')

    def test_employee_page_keeps_guards_and_post_submitters(self):
        employee=self.make_employee("UI-P4-TEST")
        user=self.make_user("HR_MANAGER",None,"shared-hr")
        self.client.force_login(user)
        response=self.client.get(reverse('portal:hr_employee_detail',args=[employee.pk]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'data-ui-confirm=')
        self.assertContains(response,'name="next" value="hcns"')
        self.assertContains(response,reverse('portal:hr_employee_history_create',args=[employee.pk,'discipline']))
        self.assertContains(response,'name="discipline_type"')
        self.assertContains(response,'name="csrfmiddlewaretoken"')
        unprivileged=self.make_user("EMPLOYEE",None,"shared-unprivileged")
        self.client.force_login(unprivileged)
        self.assertEqual(self.client.get(reverse('portal:hr_employee_detail',args=[employee.pk])).status_code,404)

    def test_filter_preserves_q_and_pagination_query(self):
        user=self.make_user("HR_MANAGER",None,"shared-filter")
        self.client.force_login(user)
        response=self.client.get(reverse('portal:hr_employee_list'),{'q':'Dữ liệu & giả'})
        self.assertContains(response,'name="q"')
        self.assertContains(response,'value="Dữ liệu &amp; giả"')
        self.assertContains(response,'Không có kết quả phù hợp')
        self.assertContains(response,'Xóa lọc')

        from django.core.paginator import Paginator
        from django.template.loader import render_to_string
        page=Paginator(list(range(25)),20).get_page(1)
        html=render_to_string("portal/_pagination.html",{"standard":True,"page_obj":page,"pagination_query":"q=Gi%E1%BA%A3+%26"})
        self.assertIn('href="?q=Gi%E1%BA%A3+%26&amp;page=2"',html)
        self.assertIn('aria-current="page"',html)
