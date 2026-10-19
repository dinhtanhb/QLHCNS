from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.assistant.m365_search import search_sharepoint
from apps.assistant.nlp import parse
from apps.m365.graph_client import GraphAPIError, GraphNotConfigured

SEARCH_TARGET = "apps.assistant.m365_search.get_graph_client"
# Đường lùi duyệt đúng bảng thư mục mà `apps.m365.storage` dùng để GHI tệp.
# Ghim bằng override_settings để `.env` của máy lập trình viên không đổi được
# đáp án: `listings` keyed theo tên thư mục, lệch tên là test "đỗ" giả tạo.
FOLDER_MAP = {
    "dispatches": "CongVan",
    "incoming_docs": "CongVanDen",
    "outgoing_docs": "CongVanDi",
}
FOLDER_SETTINGS = {"M365_SHAREPOINT_LIBRARY": "Documents", "M365_FOLDER_MAP": FOLDER_MAP}


def _hit(name, url, modified=""):
    return {"name": name, "web_url": url, "last_modified": modified}


class _FakeClient:
    """Thế chỗ GraphClient thật: không có `_request`, nên không có đường nào
    gọi ra ngoài ngay cả khi `.env` đã cấu hình M365."""

    def __init__(self, *, configured=True, search=None, listing=None, listings=None):
        self._configured = configured
        self._search = [] if search is None else search
        self._listing = [] if listing is None else listing
        self._listings = listings
        self.search_calls = []
        self.list_calls = []

    def is_configured(self):
        return self._configured

    def search_files(self, query, top=20):
        self.search_calls.append((query, top))
        if isinstance(self._search, Exception):
            raise self._search
        return list(self._search)

    def list_folder_files(self, library_name, folder=""):
        self.list_calls.append((library_name, folder))
        if self._listings is not None:
            value = self._listings.get(folder, [])
            if isinstance(value, Exception):
                raise value
            return list(value)
        return list(self._listing)


@override_settings(**FOLDER_SETTINGS)
class SharePointSearchTests(SimpleTestCase):
    def _run(self, client, question):
        with patch(SEARCH_TARGET, return_value=client):
            return search_sharepoint(parse(question))

    def test_not_configured(self):
        results, note = self._run(_FakeClient(configured=False), "công văn")
        self.assertEqual((results, note), ([], "not_configured"))

    def test_graph_not_configured_error_maps_to_not_configured(self):
        # `_site_prefix()` của GraphClient báo GraphNotConfigured (status_code
        # None) khi thiếu M365_SHAREPOINT_HOSTNAME - khác với lỗi mạng.
        client = _FakeClient(search=GraphNotConfigured("thiếu site"))
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual((results, note), ([], "not_configured"))

    def test_question_without_searchable_text_is_skipped(self):
        client = _FakeClient()
        results, note = self._run(client, "tìm giúp tôi")
        self.assertEqual((results, note), ([], None))
        self.assertEqual(client.search_calls, [])

    def test_search_success_maps_and_keeps_date(self):
        client = _FakeClient(search=[
            _hit("CV nghỉ phép.pdf", "https://x/sites/IHRMS/CongVan/CV.pdf",
                 "2026-09-10T08:00:00Z"),
        ])
        results, note = self._run(client, '"nghỉ phép"')
        self.assertIsNone(note)
        self.assertEqual(results[0], {
            "source": "sharepoint", "type": "file", "title": "CV nghỉ phép.pdf",
            "meta": "SharePoint", "url": "https://x/sites/IHRMS/CongVan/CV.pdf",
            "date": date(2026, 9, 10), "score": results[0]["score"],
        })
        self.assertGreaterEqual(results[0]["score"], 10)

    def test_last_modified_without_value_is_none(self):
        # Graph có thể trả DriveItem thiếu lastModifiedDateTime, hoặc "giá trị"
        # không phải ngày (tenant lạ). Tên phải khớp từ khóa để được đưa vào
        # kết quả; `date` của cả hai dòng là None chứ không được raise.
        client = _FakeClient(search=[_hit("cv a.pdf", "u1", ""),
                                     _hit("cv b.pdf", "u2", "không phải ngày")])
        results, _ = self._run(client, "cv")
        self.assertEqual([r["date"] for r in results], [None, None])

    def test_403_falls_back_to_folder_listing(self):
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listing=[_hit("CV nghỉ phép scan.pdf", "https://x/CV.pdf")])
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép scan.pdf"])

    def test_fallback_dedupes_across_folders(self):
        # Root và từng thư mục nghiệp vụ cùng trả một tệp: cùng một liên kết chỉ
        # nên xuất hiện một lần, nếu không kết quả SharePoint nhấn chìm DB.
        shared = _hit("Quy chế.pdf", "https://x/sites/IHRMS/Quy%20che.pdf")
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listings={"CongVan": [shared], "": [shared]})
        results, note = self._run(client, "quy chế")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["url"] for r in results], [shared["web_url"]])

    def test_fallback_filters_by_keyword(self):
        client = _FakeClient(
            search=GraphAPIError("Forbidden", status_code=403),
            listings={"CongVan": [
                _hit("CV nghỉ phép.pdf", "u1"),
                _hit("Báo cáo tài chính.pdf", "u2"),
            ]},
        )
        results, _ = self._run(client, "nghỉ phép")
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép.pdf"])

    def test_fallback_browses_the_configured_business_folders(self):
        # Tên thư mục PHẢI đến từ M365_FOLDER_MAP (bảng mà apps.m365.storage ghi
        # tệp theo). Đọc nhầm `settings.M365_FOLDER_DISPATCHES` - vốn chỉ là tên
        # biến môi trường trong settings.py, không phải attribute - thì đường lùi
        # chỉ còn thư viện gốc và hầu như không thấy gì, mà test vẫn không đỏ.
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403))
        self._run(client, "nghỉ phép")
        self.assertEqual(
            [folder for _, folder in client.list_calls],
            ["CongVan", "CongVanDen", "CongVanDi", ""],
        )
        self.assertEqual({library for library, _ in client.list_calls}, {"Documents"})

    def test_fallback_skips_folder_errors_but_tries_the_others(self):
        client = _FakeClient(
            search=GraphAPIError("Forbidden", status_code=403),
            listings={"CongVan": GraphAPIError("Không tìm thấy thư viện", status_code=404),
                      "CongVanDen": [_hit("CV nghỉ phép.pdf", "u1")]},
        )
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["url"] for r in results], ["u1"])

    def test_fallback_without_configured_folder_is_not_configured(self):
        # `_drive_id` gọi `site_id`, và thiếu site config thì phải báo
        # "not_configured" chứ không phải "search_fallback" với danh sách rỗng.
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listings={"CongVan": GraphNotConfigured("thiếu site")})
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual((results, note), ([], "not_configured"))

    def test_fallback_ignores_files_already_returned_by_search(self):
        hit = _hit("CV 128.pdf", "https://x/sites/IHRMS/CongVan/CV-128.pdf")
        client = _FakeClient(search=[hit])
        results, _ = self._run(client, "128")
        self.assertEqual([r["url"] for r in results], [hit["web_url"]])

    def test_network_error_returns_unavailable(self):
        client = _FakeClient(search=GraphAPIError("timeout", status_code=503))
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual((results, note), ([], "unavailable"))

    def test_doc_number_is_the_query_when_no_text(self):
        client = _FakeClient(search=[])
        self._run(client, "128/CV-ĐN")
        self.assertEqual(client.search_calls[0][0], "128/CV-ĐN")

    def test_score_matches_accent_stripped_name(self):
        # `keywords` đã bỏ dấu nên so với tên tệp cũng phải bỏ dấu.
        client = _FakeClient(search=[_hit("Công văn nghỉ phép.pdf", "u1")])
        results, _ = self._run(client, "nghỉ phép")
        self.assertEqual([r["title"] for r in results], ["Công văn nghỉ phép.pdf"])
        self.assertGreaterEqual(results[0]["score"], 10)

    def test_number_match_dominates_name_match(self):
        client = _FakeClient(search=[
            _hit("Báo cáo nghỉ phép.pdf", "u1"),
            _hit("128/CV-ĐN nghỉ phép.pdf", "u2"),
        ])
        results, _ = self._run(client, "128/CV-ĐN")
        self.assertEqual(results[0]["url"], "u2")
        self.assertGreater(results[0]["score"], results[1]["score"])

    def test_results_are_capped(self):
        client = _FakeClient(search=[_hit(f"CV {i}.pdf", f"u{i}") for i in range(40)])
        results, _ = self._run(client, "cv")
        self.assertLessEqual(len(results), 20)
        self.assertEqual(client.search_calls[0][1], len(results))
