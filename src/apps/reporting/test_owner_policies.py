"""Owner decisions for spreadsheet identity data and scoped dispatch counts."""
import io
from openpyxl import load_workbook
from django.test import override_settings
from django.urls import reverse
from apps.portal import tests_review_20261008 as fixtures


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
