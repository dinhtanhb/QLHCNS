"""Imported historical decisions must be searchable without weakening scope."""
from unittest.mock import patch
from datetime import date

from django.test import SimpleTestCase, TestCase, override_settings
from django.core import signing
from django.urls import reverse
from apps.portal import test_home_dashboard as fixtures

from .m365_search import search_sharepoint
from .nlp import parse
from .tests_m365_search import _FakeClient, _hit, _user, SITE


@override_settings(
    M365_STORAGE_ENABLED=True,
    M365_SHAREPOINT_LIBRARY="Documents",
    M365_FOLDER_MAP={"personnel_decisions": "QuyetDinh"},
)
class HistoricalDecisionSearchTests(SimpleTestCase):
    def run_search(self, items, question, role="HR_MANAGER", indexed=True):
        client = _FakeClient(search=items if indexed else [], listing=items)
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            result = search_sharepoint(parse(question), _user(role))
        return result, client

    def test_uploaded_historical_decision_matches_its_business_date(self):
        item = _hit(
            "QD nghi bu cua CBDA lam viec cuoi tuan - 29.04.2020.pdf",
            f"{SITE}/QuyetDinh/2020/4/QD-nghi-bu-CBDA-29.04.2020.pdf",
            "2026-10-20T07:00:00Z",
        )
        for role in ("HR_MANAGER", "DIRECTOR"):
            for question in (
                "tìm quyết định nghỉ bù cho CBDA năm 2020",
                "tìm quyết định nghỉ bù năm 2020",
                "tìm quyết định nghỉ bù tháng 4/2020",
            ):
                with self.subTest(role=role, question=question):
                    client = _FakeClient(search=[item], listing=[item])
                    with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
                        results, _ = search_sharepoint(parse(question), _user(role))
                    self.assertEqual([r["url"] for r in results], [item["web_url"]])

    def test_unindexed_file_is_found_recursively_with_business_date(self):
        item = _hit("QD nghi bu - 29.04.2020.pdf", f"{SITE}/QuyetDinh/2020/4/qd.pdf", "2026-10-20T00:00:00Z")
        (results, _), client = self.run_search([item], "quyết định nghỉ bù tháng 4/2020", indexed=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["date"], date(2020, 4, 29))
        self.assertIn("ngày trong tên tệp", results[0]["meta"])
        self.assertEqual(client.list_calls[0][1], "QuyetDinh")

    def test_folder_period_is_used_without_inventing_an_exact_date(self):
        item = _hit("QD nghi bu.pdf", f"{SITE}/QuyetDinh/2020/4/qd.pdf", "2026-10-20T00:00:00Z")
        (results, _), _ = self.run_search([item], "quyết định nghỉ bù tháng 4/2020")
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["date"])
        for question in ("quyết định nghỉ bù tháng 5/2020", "quyết định nghỉ bù năm 2026"):
            self.assertEqual(self.run_search([item], question)[0][0], [])

    def test_no_business_date_never_uses_upload_date_for_decisions(self):
        item = _hit("QD nghi bu.pdf", f"{SITE}/QuyetDinh/qd.pdf", "2020-04-29T00:00:00Z")
        self.assertEqual(self.run_search([item], "quyết định nghỉ bù năm 2020")[0][0], [])

    def test_only_global_decision_readers_can_list_raw_imports(self):
        item = _hit("QD nghi bu - 29.04.2020.pdf", f"{SITE}/QuyetDinh/2020/4/qd.pdf")
        for role in ("HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER"):
            self.assertEqual(len(self.run_search([item], "quyết định nghỉ bù năm 2020", role)[0][0]), 1)
        for role in ("EMPLOYEE", "DEPT_MANAGER", "PROJECT_MANAGER", "PROJECT_COORDINATOR", "SYS_ADMIN"):
            (results, _), client = self.run_search([item], "quyết định nghỉ bù năm 2020", role)
            self.assertEqual(results, [])
            self.assertEqual(client.search_calls + client.list_calls + client.root_calls, [])

    def test_private_library_and_other_roots_remain_excluded(self):
        items = [_hit("QD nghi bu - 29.04.2020.pdf", url) for url in (
            f"{SITE}/HoSoNoiBo/QuyetDinh/2020/4/qd.pdf",
            f"{SITE}/QuyetDinh/../DonNghiPhep/qd.pdf",
            f"{SITE.replace('Shared Documents', 'PrivateLibrary')}/QuyetDinh/2020/4/qd.pdf",
        )]
        self.assertEqual(self.run_search(items, "quyết định nghỉ bù năm 2020")[0][0], [])

    def test_decision_date_formats_and_priority(self):
        # 1. Year first YYYY-MM-DD
        item1 = _hit("QD-bo-nhiem-2026-10-20.pdf", f"{SITE}/QuyetDinh/qd1.pdf")
        (res1, _), _ = self.run_search([item1], "quyết định bổ nhiệm tháng 10/2026")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["date"], date(2026, 10, 20))

        # 2. 2-digit year DD-MM-YY (20-10-26 -> 2026, 29.04.20 -> 2020)
        item2 = _hit("QD-tang-luong-20-10-26.pdf", f"{SITE}/QuyetDinh/qd2.pdf")
        (res2, _), _ = self.run_search([item2], "quyết định tăng lương năm 2026")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0]["date"], date(2026, 10, 20))

        item3 = _hit("QD-khen-thuong-29.04.20.pdf", f"{SITE}/QuyetDinh/qd3.pdf")
        (res3, _), _ = self.run_search([item3], "quyết định khen thưởng năm 2020")
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0]["date"], date(2020, 4, 29))

        # 3. Invalid date first (31-02-2020) skipped, picks first valid (15-03-2020)
        item4 = _hit("QD-31-02-2020-hieuluc-15-03-2020.pdf", f"{SITE}/QuyetDinh/qd4.pdf")
        (res4, _), _ = self.run_search([item4], "quyết định tháng 3/2020")
        self.assertEqual(len(res4), 1)
        self.assertEqual(res4[0]["date"], date(2020, 3, 15))

        # 4. Multiple valid dates: picks the first one from left to right
        item5 = _hit("QD-ban-hanh-01-10-2026-hieu-luc-15-10-2026.pdf", f"{SITE}/QuyetDinh/qd5.pdf")
        (res5, _), _ = self.run_search([item5], "quyết định tháng 10/2026")
        self.assertEqual(len(res5), 1)
        self.assertEqual(res5[0]["date"], date(2026, 10, 1))

    def test_undated_files_reported_when_filtering_by_date(self):
        dated_item = _hit("QD-nghi-bu-2020-04-29.pdf", f"{SITE}/QuyetDinh/qd_dated.pdf")
        undated_item1 = _hit("QD-nghi-bu-khong-ngay.pdf", f"{SITE}/QuyetDinh/qd_undated1.pdf")
        undated_item2 = _hit("QD-nghi-bu-chua-ro.pdf", f"{SITE}/QuyetDinh/qd_undated2.pdf")

        result, _ = self.run_search([dated_item, undated_item1, undated_item2], "quyết định nghỉ bù năm 2020")
        results, note = result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["date"], date(2020, 4, 29))
        self.assertEqual(getattr(result, "undated_count", 0), 2)

    @override_settings(
        M365_STORAGE_ENABLED=True,
        M365_SHAREPOINT_LIBRARY="Documents",
        M365_FOLDER_MAP={},
    )
    def test_default_personnel_decisions_folder_without_opt_in(self):
        item = _hit("QD-2026-10-20.pdf", f"{SITE}/QuyetDinh/qd.pdf")
        for role in ("HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER"):
            (results, _), client = self.run_search([item], "quyết định tháng 10/2026", role)
            self.assertEqual(len(results), 1, f"Role {role} should find decisions by default")
            self.assertEqual(client.list_calls[0][1], "QuyetDinh")


@override_settings(
    M365_STORAGE_ENABLED=True,
    M365_SHAREPOINT_LIBRARY="Documents",
    M365_FOLDER_MAP={"personnel_decisions": "QuyetDinh"},
)
class DecisionFileAccessTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.reader = cls.user(cls, "HR_MANAGER", True)

    def test_signed_decision_download_reauthorizes_after_role_change(self):
        from apps.security.models import Role
        token = signing.dumps(f"{SITE}/QuyetDinh/2020/4/qd.pdf", salt="assistant-file")
        url = reverse("assistant:sharepoint_file", args=[token])
        client = _FakeClient()
        downloads = []
        def download(library, path):
            downloads.append((library, path))
            return b"%PDF-1.4 synthetic decision"
        client.download_file = download
        self.client.force_login(self.reader)
        with patch("apps.m365.graph_client.get_graph_client", return_value=client):
            response = self.client.get(url + "?download=1")
            self.assertEqual(response.status_code, 200)
            self.assertIn("attachment", response["Content-Disposition"])
            self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 synthetic decision")
            self.assertEqual(downloads, [("Documents", "QuyetDinh/2020/4/qd.pdf")])
            self.reader.role = Role.objects.get_or_create(role_code="EMPLOYEE", defaults={"role_name": "Employee"})[0]
            self.reader.save(update_fields=["role"])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(len(downloads), 1)

    def test_services_ask_includes_undated_notice(self):
        from apps.assistant.services import ask
        dated_item = _hit("QD-nghi-bu-2020-04-29.pdf", f"{SITE}/QuyetDinh/qd_dated.pdf")
        undated_item = _hit("QD-nghi-bu-khong-ngay.pdf", f"{SITE}/QuyetDinh/qd_undated.pdf")
        client = _FakeClient(search=[dated_item, undated_item], listing=[dated_item, undated_item])
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            response = ask("quyết định nghỉ bù năm 2020", self.reader)
        self.assertEqual(response.get("undated_count"), 1)
        self.assertEqual(response.get("undated_notice"), "còn 1 tệp trong thư mục chưa xác định được ngày")

    def test_download_security_event_records_folder_and_file(self):
        from apps.security.models import SecurityEvent
        token = signing.dumps(f"{SITE}/QuyetDinh/2020/4/qd_ky_luat.pdf", salt="assistant-file")
        url = reverse("assistant:sharepoint_file", args=[token])
        client = _FakeClient()
        client.download_file = lambda library, path: b"%PDF-1.4 synthetic content"
        self.client.force_login(self.reader)
        with patch("apps.m365.graph_client.get_graph_client", return_value=client):
            resp = self.client.get(url + "?download=1")
            self.assertEqual(resp.status_code, 200)

        event = SecurityEvent.objects.latest("occurred_at")
        self.assertEqual(event.action, "file_download")
        self.assertEqual(event.resource, "assistant.sharepoint:QuyetDinh")
        self.assertEqual(event.record_id, "2020/4/qd_ky_luat.pdf")

    def test_download_security_event_hashes_long_path(self):
        import hashlib
        from apps.security.models import SecurityEvent
        long_filename = "A" * 70 + ".pdf"
        token = signing.dumps(f"{SITE}/QuyetDinh/2020/{long_filename}", salt="assistant-file")
        url = reverse("assistant:sharepoint_file", args=[token])
        client = _FakeClient()
        client.download_file = lambda library, path: b"%PDF-1.4 synthetic content"
        self.client.force_login(self.reader)
        with patch("apps.m365.graph_client.get_graph_client", return_value=client):
            resp = self.client.get(url + "?download=1")
            self.assertEqual(resp.status_code, 200)

        event = SecurityEvent.objects.latest("occurred_at")
        self.assertEqual(event.action, "file_download")
        self.assertEqual(event.resource, "assistant.sharepoint:QuyetDinh")
        expected_hash = hashlib.sha256(f"2020/{long_filename}".encode("utf-8")).hexdigest()
        self.assertEqual(event.record_id, expected_hash)
        self.assertEqual(len(event.record_id), 64)
