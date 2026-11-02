"""Owner decisions for spreadsheet identity data and scoped dispatch counts."""
from datetime import date,timedelta
import io
from openpyxl import load_workbook
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from apps.portal import tests_review_20261008 as fixtures
from apps.document.models import DispatchBook,OfficialDispatch
from apps.security.data_access import visible_dispatches_for


@override_settings(AXES_ENABLED=False)
class OwnerReportPolicyTests(fixtures.Review20261008Fixtures):
    def test_employee_export_masks_identity_unless_explicit_full_export_permission(self):
        employee=self.make_employee('EXPORT-C')
        employee.national_id='001234561234';employee.save(update_fields=['national_id'])
        for code,expected in [('FINANCE_OFFICER','********1234'),('HR_OFFICER','********1234'),('DIRECTOR','********1234'),('HR_MANAGER','001234561234')]:
            with self.subTest(role=code):
                user=self.make_user(code,self.make_employee('EX-'+code[:8]),'export-c-'+code)
                self.client.force_login(user);response=self.client.get(reverse('reporting:export_employees'))
                self.assertEqual(response.status_code,200)
                sheet=load_workbook(io.BytesIO(response.content)).active
                row=next(row for row in sheet.iter_rows(min_row=5) if row[1].value==employee.employee_code)
                self.assertEqual((row[5].value,row[5].data_type),(expected,'s'))

    def test_short_identity_is_completely_masked_and_export_permission_is_unchanged(self):
        from apps.reporting.services import generate_employee_list_excel
        employee=self.make_employee('SHORT-ID-C');employee.national_id='123';employee.save(update_fields=['national_id'])
        sheet=load_workbook(generate_employee_list_excel()).active
        row=next(row for row in sheet.iter_rows(min_row=5) if row[1].value==employee.employee_code)
        self.assertEqual(row[5].value,'************')
        self.client.force_login(self.make_user('EMPLOYEE',self.make_employee('EXPORT-NO'),'export-no-c'))
        self.assertEqual(self.client.get(reverse('reporting:export_employees')).status_code,403)

    def test_report_dispatch_totals_match_visible_scope_without_changing_shared_types(self):
        finance=self.make_user('FINANCE_OFFICER',self.make_employee('SC-FIN'),'scope-fin-c')
        hr=self.make_user('HR_MANAGER',self.make_employee('SC-HR'),'scope-hr-c')
        today=timezone.localdate();book=DispatchBook.objects.create(book_code='SCOPE-C',book_name='Synthetic',book_type='Internal',year=today.year)
        for index,(kind,security) in enumerate([('Incoming','Confidential'),('Outgoing','Confidential'),('InternalDirective','Normal'),('InternalDirective','Confidential')]):
            OfficialDispatch.objects.create(dispatch_type=kind,security_level=security,dispatch_book=book,dispatch_no='SCOPE-'+str(index),title='Synthetic scope',issuing_organization='QA',issue_date=today,received_or_sent_date=today,status='Pending',due_date=today-timedelta(days=1),created_by=hr)
        totals=[]
        for user in [finance,hr]:
            self.client.force_login(user);response=self.client.get(reverse('reporting:dashboard'))
            self.assertEqual(response.status_code,200)
            expected=visible_dispatches_for(user).filter(status='Pending').count()
            self.assertEqual(response.context['pending_dispatches'],expected)
            self.assertEqual(response.context['overdue_dispatches'],expected)
            self.assertEqual(visible_dispatches_for(user).filter(dispatch_type__in=['Incoming','Outgoing']).count(),2)
            totals.append(expected)
        self.assertLess(totals[0],totals[1])
        from apps.portal.reporting_dashboard import build_report_snapshot
        finance_snapshot=build_report_snapshot(today,today,user=finance)
        hr_snapshot=build_report_snapshot(today,today,user=hr)
        self.assertEqual(finance_snapshot['headline']['overdue_dispatches'],totals[0])
        self.assertEqual(hr_snapshot['headline']['overdue_dispatches'],totals[1])
