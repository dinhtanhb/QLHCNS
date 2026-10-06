import io
from datetime import date, datetime, timezone as dt_timezone
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.common.export_names import export_name
from apps.asset.models import InventorySession
from apps.payroll.models import Payroll, PayrollPeriod, Payslip
from apps.recruitment.models import Candidate
from apps.leave.models import LeaveRequest, LeaveType
from apps.security.models import Role
from . import tests_hcns as fixtures
from .hcns.catalog import FORMS
from .hcns.filenames import PREFIXES, draft_name
from .hcns.forms import initial_document_data
from .hcns.rendering import document_context
from .hcns.prefill import prefill


class FilenameUnitTests(SimpleTestCase):
    def test_safe_ascii_and_bounded_windows_name(self):
        name = export_name("QD_NangLuong", 'VH/999\\x\r\n"../Đ', date(2026, 10, 6), "docx")
        self.assertEqual(name, "QD_NangLuong_VH-999-x-D_20261006.docx")
        self.assertLess(len(export_name("QD", "x"*500, date(2026, 10, 6), "docx")), 100)

    def test_every_template_has_explicit_prefix_and_missing_date_is_visible(self):
        self.assertEqual(set(PREFIXES), set(FORMS))
        for slug, spec in FORMS.items():
            values, rows = initial_document_data(spec, {}, {})
            for key in ("document_date", "decision_date", "execution_date", "inventory_date"):
                values[key] = None
            name = draft_name(document_context(spec, values, rows), "TEST-1")
            self.assertRegex(name, r"^[A-Za-z0-9_-]+_(ChuaKy|ChuaCoNgay)$")


class FilenameViewTests(TestCase):
    user = classmethod(fixtures.HCNSFormTests.user.__func__)
    data = fixtures.HCNSFormTests.data

    @classmethod
    def setUpTestData(cls):
        fixtures.HCNSFormTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.client.force_login(self.superuser)

    def url(self, slug):
        return reverse("portal:hcns_draft", args=[slug])

    def test_post_uses_selected_employee_and_signed_date_not_source_or_effective_date(self):
        url = self.url("salary-decision") + f"?employee_id={self.employees[0].pk}"
        data = self.data("salary-decision", full_name=self.employees[1].pk,
                         document_date="2025-02-03", effective_date="2090-01-01", action="export")
        result = self.client.post(url, data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result["Content-Disposition"], 'attachment; filename="QD_NangLuong_HCNS-1_20250203.docx"')
        data["action"] = "preview"
        preview = self.client.post(url, data)
        self.assertContains(preview, 'data-filename="QD_NangLuong_HCNS-1_20250203"')

    def test_missing_employee_or_date_and_appointment_action(self):
        data = self.data("appointment-decision", full_name="", document_date="", decision_action="Miễn nhiệm", action="export")
        result = self.client.post(self.url("appointment-decision"), data)
        self.assertEqual(result.status_code, 200)
        self.assertIn('QD_MienNhiem_ChuaChonNV_ChuaKy.docx', result["Content-Disposition"])

    def test_candidate_name_uses_code_and_get_employee_source(self):
        candidate = Candidate.objects.create(candidate_code="NAME-UV", full_name="Same name", phone_number="000", email="test@example.test")
        result = self.client.get(self.url("candidate-interview"), {"candidate_id": candidate.pk, "export": "1"})
        self.assertIn("Phieu_PhongVanUngVien_NAME-UV_", result["Content-Disposition"])
        result = self.client.get(self.url("employee-information"), {"employee_id": self.employees[0].pk, "export": "1"})
        self.assertIn("HS_ThongTinNhanVien_HCNS-0_", result["Content-Disposition"])

    def test_authorized_leave_source_keeps_code_without_extra_directory_permission(self):
        manager = self.admin
        manager.role, _ = Role.objects.get_or_create(role_code="DEPT_MANAGER", defaults={"role_name": "Test manager"})
        manager.save(update_fields=["role"])
        self.department.manager = self.employees[2]
        self.department.save(update_fields=["manager"])
        kind = LeaveType.objects.create(leave_type_code="AL", leave_type_name="Test")
        leave = LeaveRequest.objects.create(employee=self.employees[0], leave_type=kind, from_date=date(2026, 10, 12), to_date=date(2026, 10, 13))
        self.client.force_login(manager)
        values, _, _ = prefill(manager, FORMS["annual-leave"], {"leave_id": str(leave.pk)})
        self.assertEqual(values["_employee_code"], self.employees[0].employee_code)
        result = self.client.get(self.url("annual-leave"), {"leave_id": leave.pk})
        self.assertEqual(result.status_code, 200)

    def test_report_exports_share_convention(self):
        routes = [("export_employees", "generate_employee_list_excel", "DS_NhanSu_TongHop"),
                  ("export_contracts", "generate_expiring_contracts_excel", "DS_HopDongSapHetHan_60Ngay"),
                  ("export_dispatches", "generate_dispatch_book_excel", "So_CongVan_2025-den")]
        for route, generator, prefix in routes:
            with self.subTest(route=route), patch("apps.reporting.views."+generator, return_value=io.BytesIO(b"test")), patch("apps.reporting.views.timezone.localdate", return_value=date(2026, 10, 6)):
                response = self.client.get(reverse("reporting:"+route), {"year": 2025})
                self.assertEqual(response["Content-Disposition"], f'attachment; filename="{prefix}_20261006.xlsx"')

    def test_inventory_uses_session_date_and_sanitizes_session_name(self):
        session = InventorySession.objects.create(session_name='HN/Đợt "1"', inventory_datetime=timezone.make_aware(datetime(2025, 2, 3, 12)), office_name="Test")
        result = self.client.get(reverse("portal:inventory_session_export_excel", args=[session.pk]))
        self.assertEqual(result["Content-Disposition"], 'attachment; filename="BB_KiemKeTaiSan_HN-Dot-1_20250203.xlsx"')

    def test_payslip_uses_employee_period_and_issued_date(self):
        self.client.force_login(self.staff)
        period = PayrollPeriod.objects.create(payroll_year=2025, payroll_month=2, start_date=date(2025, 2, 1), end_date=date(2025, 2, 28), status="Open")
        payroll = Payroll.objects.create(employee=self.employees[1], payroll_period=period)
        slip = Payslip.objects.create(payroll=payroll)
        PayrollPeriod.objects.filter(pk=period.pk).update(status="Locked")
        Payslip.objects.filter(pk=slip.pk).update(generated_date=datetime(2025, 2, 3, 18, tzinfo=dt_timezone.utc))
        with patch("apps.payroll.payslip_pdf.render_payslip_pdf", return_value=b"%PDF-test"):
            result = self.client.get(reverse("portal:payslip_pdf", args=[slip.pk]))
        self.assertEqual(result["Content-Disposition"], 'attachment; filename="Phieu_Luong_HCNS-1-202502_20250204.pdf"')
