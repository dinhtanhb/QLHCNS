from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.assistant.m365_search import search_sharepoint
from apps.assistant.nlp import parse
from apps.m365.graph_client import GraphAPIError, GraphNotConfigured

SEARCH_TARGET = "apps.assistant.m365_search.get_graph_client"
# Cờ bật-tắt lưu trữ M365 mà `apps.m365.storage` đã dùng từ trước; trợ lý phải
# đọc cùng cờ, không chỉ đọc credentials. Bật ở đây để các test bên dưới thật sự
# đi tới nhánh gọi Graph thay vì bị chặn ngay ở cửa bật/tắt.
# Ghim luôn `M365_FOLDER_MAP` (bảng mà `apps.m365.storage` dùng để GHI tệp): lệch
# tên thư mục là test "đỗ" giả tạo, và webUrl phải nằm trong thư mục được phép.
ASSISTANT_SETTINGS = {
    "M365_STORAGE_ENABLED": True,
    "M365_SHAREPOINT_LIBRARY": "Documents",
    "M365_FOLDER_MAP": {
        "dispatches": "CongVan",
        "incoming_docs": "CongVanDen",
        "outgoing_docs": "CongVanDi",
        # Ba thư mục nghiệp vụ khác tồn tại thật trong settings nhưng KHÔNG được
        # trợ lý đọc: lộ tên hồ sơ ứng viên/đơn nghỉ phép cho tài khoản chỉ có
        # quyền văn thư là rò rỉ dữ liệu, không phải tiện ích.
        "recruitment_cv": "HoSoUngVien",
        "leave": "DonNghiPhep",
    },
}
SITE = "https://tenant.sharepoint.com/sites/IHRMS/Shared Documents"


def _user(role_code, superuser=False):
    """Chỉ `has_permission` cần tới `user.role.role_code` nên mới chỉ cần mẫu này."""
    return SimpleNamespace(
        is_authenticated=True, is_active=True, is_superuser=superuser,
        is_staff=False, role=SimpleNamespace(role_code=role_code),
    )


HR = _user("HR_MANAGER")            # có manage_office
CLERK = _user("EMPLOYEE")           # không có quyền sổ công văn


def _hit(name, url, modified=""):
    return {"name": name, "web_url": url, "last_modified": modified}


def _in(folder, name):
    """webUrl thật của tệp nằm trong một thư mục nghiệp vụ của site IHRMS."""
    return _hit(name, f"{SITE}/{folder}/{name}")


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

    def search_files(self, query, top=20, timeout=None):
        self.search_calls.append((query, top, timeout))
        if isinstance(self._search, Exception):
            raise self._search
        return list(self._search)

    def list_folder_files(self, library_name, folder="", timeout=None):
        self.list_calls.append((library_name, folder, timeout))
        if self._listings is not None:
            value = self._listings.get(folder, [])
            if isinstance(value, Exception):
                raise value
            return list(value)
        return list(self._listing)


@override_settings(**ASSISTANT_SETTINGS)
class SharePointSearchTests(SimpleTestCase):
    def _run(self, client, question, user=HR):
        with patch(SEARCH_TARGET, return_value=client):
            return search_sharepoint(parse(question), user)

    def test_storage_flag_off_makes_no_graph_call(self):
        # Hợp đồng cô lập của `ops/run_tests.py`: bật flag là CHỈ có `.env` quyết
        # định, nên không có cửa nào để test hay request thật chạm Microsoft.
        with override_settings(M365_STORAGE_ENABLED=False):
            client = _FakeClient(search=[_in("CongVan", "CV.pdf")])
            results, note = self._run(client, "công văn")
        self.assertEqual((results, note), ([], "not_configured"))
        self.assertEqual(client.search_calls, [])
        self.assertEqual(client.list_calls, [])

    def test_user_without_dispatch_access_makes_no_graph_call(self):
        # Graph chạy app-only: token thấy cả thư viện, không thấy quyền của
        # người hỏi. Lọc theo thư mục chỉ an toàn khi người hỏi đã được xem sổ
        # công văn, nên cửa thứ hai chặn ngay từ trước khi gọi.
        client = _FakeClient(search=[_in("CongVan", "CV.pdf")])
        results, note = self._run(client, "công văn", user=CLERK)
        self.assertEqual((results, note), ([], "restricted"))
        self.assertEqual(client.search_calls, [])
        self.assertEqual(client.list_calls, [])

    def test_superuser_may_query_sharepoint(self):
        client = _FakeClient(search=[_in("CongVan", "CV nghỉ phép.pdf")])
        results, note = self._run(client, "nghỉ phép", user=_user("?", superuser=True))
        self.assertIsNone(note)
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép.pdf"])

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
        hit = _hit("CV nghỉ phép.pdf", f"{SITE}/CongVan/CV.pdf", "2026-09-10T08:00:00Z")
        client = _FakeClient(search=[hit])
        results, note = self._run(client, '"nghỉ phép"')
        self.assertIsNone(note)
        self.assertEqual(results[0], {
            "source": "sharepoint", "type": "file", "title": "CV nghỉ phép.pdf",
            "meta": "SharePoint", "url": hit["web_url"],
            "date": date(2026, 9, 10), "score": results[0]["score"],
        })
        self.assertGreaterEqual(results[0]["score"], 10)

    def test_hits_outside_the_dispatch_folders_are_dropped(self):
        # Kết quả search cấp tenant khớp đúng từ khóa nhưng nằm trong hồ sơ ứng
        # viên hoặc đơn nghỉ phép: hiện được tên là đủ lộ, dù liên kết có thể
        # không mở được. Không có quyền theo từng tệp ở tầng Graph nên phải lọc.
        client = _FakeClient(search=[
            _in("HoSoUngVien", "Nguyễn Văn A - CV.pdf"),
            _in("DonNghiPhep", "Đơn nghỉ phép 2026.pdf"),
            _in("CongVanDen", "CV 500.pdf"),
        ])
        results, note = self._run(client, "nguyễn văn a")
        self.assertEqual([r["url"] for r in results], [f"{SITE}/CongVanDen/CV 500.pdf"])
        self.assertTrue(all("HoSoUngVien" not in r["url"] for r in results))
        self.assertIsNone(note)

    def test_folder_name_must_be_a_whole_path_segment(self):
        # "CongVan" là tiền tố của "CongVanDen" nhưng "CongVanFoo" thì không:
        # khớp theo đoạn, không khớp theo chuỗi con, để một thư mục lạ có cùng
        # tiền tố không slipped through.
        client = _FakeClient(search=[_hit("x.pdf", f"{SITE}/CongVanBíMật/x.pdf")])
        results, _ = self._run(client, "cv")
        self.assertEqual(results, [])

    def test_encoded_urls_are_decided_before_the_folder_check(self):
        # webUrl của SharePoint hay ở dạng `AllItems.aspx?id=%2F...%2FCongVan%2F`
        # hoặc chứa `%20`; từ chối vì không đọc ra dấu phân cách là làm mất tính
        # năng thật, nên phải giải mã trước khi so đoạn.
        encoded = ("https://tenant.sharepoint.com/sites/IHRMS/Shared%20Documents/_layouts/15/"
                   "view.aspx?initialid=%2Fsites%2FIHRMS%2FShared%20Documents%2FCongVan%2F")
        client = _FakeClient(search=[_hit("CV.pdf", encoded)])
        results, _ = self._run(client, "cv")
        self.assertEqual([r["url"] for r in results], [encoded])

    def test_last_modified_without_value_is_none(self):
        # Graph có thể trả DriveItem thiếu lastModifiedDateTime, hoặc "giá trị"
        # không phải ngày (tenant lạ). Tên phải khớp từ khóa để được đưa vào
        # kết quả; `date` của cả hai dòng là None chứ không được raise.
        client = _FakeClient(search=[_in("CongVan", "cv a.pdf"),
                                     _hit("cv b.pdf", f"{SITE}/CongVanDi/cv b.pdf",
                                          "không phải ngày")])
        results, _ = self._run(client, "cv")
        self.assertEqual([r["date"] for r in results], [None, None])

    def test_403_falls_back_to_folder_listing(self):
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listing=[_in("CongVan", "CV nghỉ phép scan.pdf")])
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép scan.pdf"])

    def test_fallback_dedupes_across_folders(self):
        # Hai thư mục công văn cùng trả một tệp (liên kết giống nhau): cùng một
        # liên kết chỉ nên xuất hiện một lần, nếu không kết quả SharePoint nhấn
        # chìm DB.
        shared = _hit("Quy chế.pdf", f"{SITE}/CongVan/Quy%20che.pdf")
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listings={"CongVan": [shared], "CongVanDen": [shared]})
        results, note = self._run(client, "quy chế")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["url"] for r in results], [shared["web_url"]])

    def test_fallback_filters_by_keyword(self):
        client = _FakeClient(
            search=GraphAPIError("Forbidden", status_code=403),
            listings={"CongVan": [
                _in("CongVan", "CV nghỉ phép.pdf"),
                _in("CongVan", "Báo cáo tài chính.pdf"),
            ]},
        )
        results, _ = self._run(client, "nghỉ phép")
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép.pdf"])

    def test_fallback_browses_only_the_dispatch_folders(self):
        # Tên thư mục PHẢI đến từ M365_FOLDER_MAP (bảng mà `apps.m365.storage` ghi
        # tệp theo). Đọc nhầm `settings.M365_FOLDER_DISPATCHES` - vốn chỉ là tên
        # biến môi trường trong settings.py, không phải attribute - thì đường lùi
        # chỉ còn thư viện gốc và hầu như không thấy gì, mà test vẫn không đỏ.
        # Thư viện gốc ("") cũng KHÔNG được duyệt: listing gốc trả mọi tệp của
        # cả site, tức là lộ tên hồ sơ ứng viên cho tài khoản chỉ có quyền văn thư.
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403))
        self._run(client, "nghỉ phép")
        self.assertEqual(
            [call[1] for call in client.list_calls],
            ["CongVan", "CongVanDen", "CongVanDi"],
        )
        self.assertEqual({call[0] for call in client.list_calls}, {"Documents"})

    def test_fallback_skips_folder_errors_but_tries_the_others(self):
        client = _FakeClient(
            search=GraphAPIError("Forbidden", status_code=403),
            listings={"CongVan": GraphAPIError("Không tìm thấy thư viện", status_code=404),
                      "CongVanDen": [_in("CongVanDen", "CV nghỉ phép.pdf")]},
        )
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["url"] for r in results], [f"{SITE}/CongVanDen/CV nghỉ phép.pdf"])

    def test_fallback_without_configured_folder_is_not_configured(self):
        # `_drive_id` gọi `site_id`, và thiếu site config thì phải báo
        # "not_configured" chứ không phải "search_fallback" với danh sách rỗng.
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listings={"CongVan": GraphNotConfigured("thiếu site")})
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual((results, note), ([], "not_configured"))

    def test_fallback_ignores_files_already_returned_by_search(self):
        hit = _in("CongVan", "CV 128.pdf")
        client = _FakeClient(search=[hit])
        results, _ = self._run(client, "128")
        self.assertEqual([r["url"] for r in results], [hit["web_url"]])

    def test_network_error_returns_unavailable(self):
        client = _FakeClient(search=GraphAPIError("timeout", status_code=503))
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual((results, note), ([], "unavailable"))

    def test_search_answered_but_every_hit_was_off_scope_uses_the_fallback(self):
        # `/search/query` là tìm cấp tenant với `size` trần: nếu 20 kết quả liên
        # quan nhất đều thuộc site/thư mục khác thì danh sách sau khi lọc rỗng.
        # Nói "không có tệp SharePoint" lúc đó là sai; phải thử đường lùi.
        client = _FakeClient(
            search=[_in("HoSoUngVien", "CV.pdf")],
            listings={"CongVan": [_in("CongVan", "CV nghỉ phép.pdf")],
                      "CongVanDen": [], "CongVanDi": []},
        )
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual(note, "search_fallback")
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép.pdf"])

    def test_search_answered_with_no_hits_at_all_does_not_browse_folders(self):
        # Không có hit nào trong site thì thư mục cũng chẳng có gì: gọi thêm ba
        # lượt mạng là vô nghĩa và chỉ kéo dài câu trả lời.
        client = _FakeClient(search=[])
        results, note = self._run(client, "nghỉ phép")
        self.assertEqual((results, note), ([], None))
        self.assertEqual(client.list_calls, [])

    def test_assistant_uses_a_short_timeout_not_the_sixty_second_default(self):
        # `_request` mặc định 60s cho nghiệp vụ upload. Trong khung chat, một
        # người hỏi không được chiếm worker nhiều phút (xem review C62/I6).
        client = _FakeClient(search=[])
        self._run(client, "nghỉ phép")
        self.assertIsNotNone(client.search_calls[0][2])
        self.assertEqual(client.list_calls, [])

    def test_assistant_timeout_applies_to_the_fallback_calls_too(self):
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403))
        self._run(client, "nghỉ phép")
        self.assertEqual(len(client.list_calls), 3)
        for _, _, timeout in client.list_calls:
            self.assertIsNotNone(timeout)

    def test_doc_number_is_the_query_when_no_text(self):
        client = _FakeClient(search=[])
        self._run(client, "128/CV-ĐN")
        self.assertEqual(client.search_calls[0][0], "128/CV-ĐN")

    def test_score_matches_accent_stripped_name(self):
        # `keywords` đã bỏ dấu nên so với tên tệp cũng phải bỏ dấu.
        client = _FakeClient(search=[_in("CongVan", "Công văn nghỉ phép.pdf")])
        results, _ = self._run(client, "nghỉ phép")
        self.assertEqual([r["title"] for r in results], ["Công văn nghỉ phép.pdf"])
        self.assertGreaterEqual(results[0]["score"], 10)

    def test_number_match_dominates_name_match(self):
        client = _FakeClient(search=[
            _in("CongVan", "Báo cáo nghỉ phép.pdf"),
            _in("CongVanDi", "128/CV-ĐN nghỉ phép.pdf"),
        ])
        results, _ = self._run(client, "128/CV-ĐN")
        self.assertEqual(results[0]["url"], f"{SITE}/CongVanDi/128/CV-ĐN nghỉ phép.pdf")
        self.assertGreater(results[0]["score"], results[1]["score"])

    def test_results_are_capped(self):
        client = _FakeClient(search=[_in("CongVan", f"CV {i}.pdf") for i in range(40)])
        results, _ = self._run(client, "cv")
        self.assertLessEqual(len(results), 20)
        self.assertEqual(client.search_calls[0][1], 20)
