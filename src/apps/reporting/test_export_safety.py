"""Formula injection regressions through actual export boundaries."""
from datetime import date
from decimal import Decimal
import io

from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook, load_workbook

from apps.asset.models import InventorySession
from apps.portal import tests_review_20261008 as fixtures

PAYLOADS = ('=1+1', '+1', '-1+1', '@SUM(1)', '\t=1', '\n=1', 'Văn bản thường')


class ExportRouteSafetyTests(fixtures.Review20261008Fixtures):
    def test_inventory_user_text_is_text_when_downloaded(self):
        employee = self.make_employee('EXPORT-QA')
        self.client.force_login(self.make_user('HR_MANAGER', employee, 'export-fix-a'))
        for payload in PAYLOADS:
            with self.subTest(payload=repr(payload)):
                session = InventorySession.objects.create(session_name='Synthetic export',
                    office_name=payload, inventory_datetime=timezone.now())
                response = self.client.get(reverse('portal:inventory_session_export_excel', args=[session.pk]))
                self.assertEqual(response.status_code, 200)
                cell = load_workbook(io.BytesIO(response.content)).active['A2']
                self.assertEqual(cell.value, payload)
                self.assertEqual(cell.data_type, 's')


class SpreadsheetValueTests(SimpleTestCase):
    def test_dashboard_untrusted_labels_are_text_without_apostrophe(self):
        from apps.portal.reporting_dashboard import export_snapshot_xlsx
        for payload in PAYLOADS:
            with self.subTest(payload=repr(payload)):
                snapshot = {'from_date': date(2026, 1, 1), 'to_date': date(2026, 1, 31),
                            'sections': [{'title': payload, 'metrics': [{'label': payload, 'display': payload}]}],
                            'month_rows': [{'label': payload, 'new_hires': 1, 'departures': 0,
                                            'transfers': 0, 'promotions': 0}],
                            'recruitment_funnel': [{'label': payload, 'value': 1}]}
                wb = load_workbook(io.BytesIO(export_snapshot_xlsx(snapshot)))
                matches = [cell for sheet in wb for row in sheet for cell in row if cell.value == payload]
                self.assertGreaterEqual(len(matches), 5)
                self.assertTrue(all(cell.data_type == 's' for cell in matches))

    def test_hcns_user_text_and_application_formulas_are_distinct(self):
        from apps.document.hcns.catalog import FORMS
        from apps.document.hcns.forms import initial_document_data
        from apps.document.hcns.rendering import document_context
        from apps.document.hcns.exports import export_xlsx
        spec = FORMS['candidate-score-summary']
        values, rows = initial_document_data(spec, {}, {})
        for record in rows['results']:
            record['candidate'] = '=1+1'
        context = document_context(spec, values, rows)
        wb = load_workbook(io.BytesIO(export_xlsx(context)))
        cells = [cell for row in wb.active for cell in row]
        self.assertTrue(any(cell.data_type == 'f' for cell in cells), 'System calculation formulas must remain formulas')
        self.assertTrue(any(cell.value == '=1+1' and cell.data_type == 's' for row in wb.active for cell in row))

    def test_excel_text_is_unchanged_and_generated_formula_numbers_dates_keep_types(self):
        from apps.common.spreadsheet_text import write_excel_value
        wb = Workbook()
        for row, value in enumerate((*PAYLOADS, Decimal('12.5'), -2, date(2026, 11, 2)), 1):
            write_excel_value(wb.active.cell(row, 1), value)
        write_excel_value(wb.active.cell(20, 1), '=SUM(1,2)', formula=True)
        output = io.BytesIO()
        wb.save(output)
        sheet = load_workbook(io.BytesIO(output.getvalue())).active
        for row, value in enumerate(PAYLOADS, 1):
            self.assertEqual((sheet.cell(row, 1).value, sheet.cell(row, 1).data_type), (value, 's'))
        self.assertEqual(sheet.cell(8, 1).data_type, 'n')
        self.assertEqual(sheet.cell(9, 1).value, -2)
        self.assertEqual(sheet.cell(10, 1).data_type, 'd')
        self.assertEqual(sheet.cell(20, 1).data_type, 'f')

    def test_csv_prefix_only_text_and_roundtrip(self):
        import csv
        from apps.common.spreadsheet_text import csv_text
        output = io.StringIO(newline='')
        csv.writer(output).writerow([csv_text(value) for value in PAYLOADS])
        values = next(csv.reader(io.StringIO(output.getvalue())))
        self.assertEqual(values, ["'" + value for value in PAYLOADS[:-1]] + [PAYLOADS[-1]])
        self.assertEqual(csv_text(-2), -2)
        self.assertEqual(csv_text(date(2026, 11, 2)), date(2026, 11, 2))
