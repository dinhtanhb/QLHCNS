from django.test import SimpleTestCase

from apps.reporting.services import (
    ComplianceReportNotConfigured,
    generate_insurance_change_report_excel,
    generate_payroll_cost_by_department_excel,
    generate_pit_finalization_data,
)


class ComplianceReportScaffoldTests(SimpleTestCase):
    def test_bhxh_export_fails_closed_until_template_is_confirmed(self):
        with self.assertRaises(ComplianceReportNotConfigured):
            generate_insurance_change_report_excel("2026-09", [])

    def test_pit_mapping_fails_closed_until_year_template_is_confirmed(self):
        with self.assertRaises(ComplianceReportNotConfigured):
            generate_pit_finalization_data(2026)

    def test_department_payroll_export_fails_closed_until_allocation_is_confirmed(self):
        with self.assertRaises(ComplianceReportNotConfigured):
            generate_payroll_cost_by_department_excel("2026-09")
