"""BCC presentation keeps weekend work, formulas, query cost and form contracts."""
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.attendance.models import Holiday, TimesheetEntry
from apps.project.models import Project
from apps.portal import test_home_dashboard as fixtures


class TimesheetPrintTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.person = self.user('EMPLOYEE', True)
        self.client.force_login(self.person)
        self.project = Project.objects.create(project_code='INC3B',project_name='Dự án giả lập')
        Holiday.objects.create(holiday_code='BCC-HOL',holiday_date=date(2026,9,1),holiday_name='Lễ giả lập')
        for day,text in ((1,'Holiday work sentinel'),(12,'Retreat 2026 weekend sentinel')):
            TimesheetEntry.objects.create(employee=self.person.employee,work_date=date(2026,9,day),
                project=self.project,task_description=text,hours=8)

    def test_weekend_holiday_entries_and_formulas_are_preserved(self):
        response=self.client.get(reverse('portal:timesheet_month'),{'year':2026,'month':9})
        self.assertContains(response,'Holiday work sentinel')
        self.assertContains(response,'Retreat 2026 weekend sentinel')
        self.assertContains(response,'Dự án INC3B')
        self.assertEqual(response.context['total_hours'],Decimal('16'))
        self.assertEqual(response.context['required_hours'],Decimal('168'))
        self.assertEqual(response.context['diff_hours'],Decimal('-152'))
        self.assertContains(response,'class="ui-timesheet-weekend"')
        self.assertContains(response,'name="sick_days"')
        self.assertContains(response,'csrfmiddlewaretoken')

    def test_print_identity_and_signature_group_are_present(self):
        response=self.client.get(reverse('portal:timesheet_month'),{'year':2026,'month':9})
        self.assertContains(response,'class="timesheet-print-heading ui-print-only"')
        self.assertContains(response,'alt="VietHealth"')
        self.assertContains(response,'Phụ lục 1')
        self.assertContains(response,'Phòng/Ban/Dự án:')
        self.assertContains(response,'class="timesheet-ending"')
        self.assertContains(response,'rowspan="2"')
        self.assertNotContains(response,'<span class="ui-print-only"><span class="">Chờ quản lý duyệt')

    def test_project_header_uses_loaded_entries_without_an_extra_query(self):
        url=reverse('portal:timesheet_month')+'?year=2026&month=9'
        self.client.get(url)
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as queries:
            response=self.client.get(url)
        self.assertEqual(response.status_code,200)
        # Query count is also recorded against the unmodified baseline in Edge UAT.
        project_queries=[q['sql'] for q in queries if 'tblProject' in q['sql'] and 'JOIN' not in q['sql'].upper()]
        self.assertEqual(len(project_queries),1)  # Existing project selector only.
        other=Project.objects.create(project_code='OTHER',project_name='Other synthetic project')
        TimesheetEntry.objects.create(employee=self.person.employee,work_date=date(2026,9,3),project=other,hours=2)
        response=self.client.get(url)
        self.assertNotContains(response,'rowspan="2"')
        self.assertContains(response,'[INC3B]')

    def test_empty_month_keeps_negative_difference_and_screen_status(self):
        response=self.client.get(reverse('portal:timesheet_month'),{'year':2026,'month':10})
        self.assertEqual(response.context['total_hours'],Decimal('0'))
        self.assertEqual(response.context['required_hours'],Decimal('176'))
        self.assertEqual(response.context['diff_hours'],Decimal('-176'))
        self.assertIsNone(response.context['balance'])
        self.assertIsNone(response.context.get('timesheet_project'))
        self.assertContains(response,'ui-screen-only ui-badge ui-badge--warning')
        self.assertNotContains(response,'rowspan="2"')
        self.assertContains(response,'Phụ lục 1')

    def test_approved_leave_values_remain_authoritative(self):
        from apps.attendance.models import MonthlyAttendanceSummary
        summary=MonthlyAttendanceSummary.objects.create(employee=self.person.employee,year=2026,month=9,
            status='Approved',sick_days=Decimal('1.5'),annual_leave_days=Decimal('2'))
        response=self.client.get(reverse('portal:timesheet_month'),{'year':2026,'month':9})
        self.assertEqual(response.context['approved_leave_total'],Decimal('3.5'))
        self.assertEqual(response.context['required_hours'],Decimal('140'))
        self.assertEqual(response.context['diff_hours'],Decimal('-124'))
        self.assertContains(response,'<span class="ui-print-only">1,5</span>',html=True)
        self.assertContains(response,'ui-screen-only ui-badge ui-badge--success')
        self.assertNotContains(response,'<span class="ui-print-only"><span class="">Đã duyệt')
