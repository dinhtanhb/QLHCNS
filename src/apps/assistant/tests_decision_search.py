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
