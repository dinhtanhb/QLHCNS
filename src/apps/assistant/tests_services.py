from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.assistant.models import SearchQueryLog
from apps.assistant.services import ask
from apps.document.models import DispatchBook, OfficialDispatch
from apps.m365.graph_client import GraphAPIError
from apps.portal import test_home_dashboard as fixtures

RESULT_KEYS = {"source", "type", "title", "meta", "url", "date"}


def _db_row(title, score, when=None):
    return {"source": "ihrms", "type": "document", "title": title, "meta": "m",
            "url": f"/u/{title}", "date": when, "score": score}


def _sp_row(title, score, when=None):
    return {"source": "sharepoint", "type": "file", "title": title, "meta": "SharePoint",
            "url": f"https://x/{title}", "date": when, "score": score}


class AskServiceTests(TestCase):
    """`services.ask` gọi DB (ORM thật) và SharePoint (mock, vì gọi Graph)."""

    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user(cls, "HR_MANAGER", True)
        cls.emp = cls.user(cls, "EMPLOYEE", True)
        book = DispatchBook.objects.create(
            book_code="IN-2026", book_name="Sổ đến 2026", book_type="Incoming", year=2026,
        )
        # C1: không có bản ghi nào thì `db_results` rỗng và nhánh "db+sharepoint"
        # của gộp/lưu log không bao giờ chạy, dù test vẫn đỗ.
        cls.dispatch = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=book, dispatch_no="128/CV-ĐN",
            title="Công văn về nghỉ phép", issuing_organization="Sở Y tế",
            issue_date=date(2026, 9, 15), received_or_sent_date=date(2026, 9, 16),
            security_level="Normal",
        )

    def _ask(self, question, *, sp=None, note=None, user=None, db=None):
        """Gọi `ask` với SharePoint dựng sẵn; DB để thật chạy theo RBAC."""
        with patch(
            "apps.assistant.services.m365_search.search_sharepoint",
            return_value=(sp or [], note),
        ):
            if db is not None:
                with patch(
                    "apps.assistant.services.db_search.search_database", return_value=db
                ):
                    return ask(question, user or self.hr)
            return ask(question, user or self.hr)

    def test_response_contract(self):
        response = self._ask("công văn nghỉ phép")
        self.assertEqual(set(response), {"query", "parsed", "took_ms", "partial", "results", "sharepoint_status"})
        self.assertEqual(response["query"], "công văn nghỉ phép")
        self.assertIsInstance(response["took_ms"], int)
        for result in response["results"]:
            # `score` là chi tiết xếp hạng nội bộ, không phải thứ để lộ ra UI.
            self.assertNotIn("score", result)
            self.assertEqual(set(result), RESULT_KEYS)

    def test_parsed_block_is_json_serialisable(self):
        # `parsed_filters` đi vào JSONField, `parsed` đi vào JSON response.
        import json

        response = self._ask("công văn tháng 9 năm 2026")
        json.dumps(response)
        self.assertEqual(response["parsed"]["date_from"], "2026-09-01")
        self.assertEqual(response["parsed"]["date_to"], "2026-09-30")
        self.assertEqual(response["parsed"]["doc_type"], "dispatch")

    def test_results_sorted_by_score_then_newest(self):
        response = self._ask(
            "công văn",
            db=[_db_row("A", 10, date(2026, 1, 2)), _db_row("B", 100), _db_row("C", 10, date(2026, 5, 1))],
        )
        # Điểm trước, ngày chỉ là tiebreak trong cùng điểm.
        self.assertEqual([r["title"] for r in response["results"]], ["B", "C", "A"])

    def test_merged_sources_are_interleaved_by_score(self):
        response = self._ask(
            "công văn nghỉ phép",
            sp=[_sp_row("sp-high", 300), _sp_row("sp-low", 5)],
        )
        titles = [r["title"] for r in response["results"]]
        self.assertEqual(titles[0], "sp-high")
        self.assertEqual(titles[-1], "sp-low")
        ihrms_titles = [r["title"] for r in response["results"] if r["source"] == "ihrms"]
        # `db_search` dựng tiêu đề "[Công văn đến] 128/CV-ĐN - …" nên so chuỗi con.
        self.assertTrue(any(self.dispatch.title in title for title in ihrms_titles))

    def test_partial_flag_on_sharepoint_error(self):
        self.assertTrue(self._ask("công văn", note="unavailable")["partial"])
        self.assertTrue(self._ask("công văn", note="search_fallback")["partial"])
        self.assertFalse(self._ask("công văn", note=None)["partial"])
        # Nguồn chưa bật không phải lỗi, đừng báo "SharePoint tạm không khả dụng".
        self.assertFalse(self._ask("công văn", note="not_configured")["partial"])

    def test_log_written_for_merged_search(self):
        response = self._ask("công văn nghỉ phép", sp=[_sp_row("f.pdf", 10)])
        log = SearchQueryLog.objects.get()
        self.assertEqual(log.user, self.hr)
        self.assertEqual(log.sources, "db+sharepoint")
        self.assertIn("keywords", log.parsed_filters)
        self.assertNotIn("score", log.parsed_filters)
        self.assertGreaterEqual(log.took_ms, 0)
        self.assertEqual(log.result_count, len(response["results"]))
        self.assertIsNone(log.error_note)

    def test_log_never_stores_result_contents(self):
        # Nhật ký chỉ được chứa câu hỏi + bộ lọc + số lượng, không chứa tiêu đề
        # hay URL tài liệu (ràng buộc đã ghi trong model docstring).
        self._ask("công văn nghỉ phép", sp=[_sp_row("Bí mật.pdf", 10)])
        log = SearchQueryLog.objects.get()
        dumped = str(log.parsed_filters)
        self.assertNotIn("Bí mật", dumped)
        self.assertNotIn("https://x", dumped)
        self.assertNotIn("/u/", dumped)

    def test_log_error_note_only_for_degraded_sharepoint(self):
        self._ask("công văn nghỉ phép", note="search_fallback")
        self.assertEqual(SearchQueryLog.objects.get().error_note, "search_fallback")
        SearchQueryLog.objects.all().delete()
        self._ask("công văn nghỉ phép", note="not_configured")
        self.assertIsNone(SearchQueryLog.objects.get().error_note)

    def test_empty_results_sources_none(self):
        self._ask("zzzzz", db=[])
        self.assertEqual(SearchQueryLog.objects.get().sources, "none")

    def test_sharepoint_only_results(self):
        self._ask("zzzzz", db=[], sp=[_sp_row("f.pdf", 10)])
        self.assertEqual(SearchQueryLog.objects.get().sources, "sharepoint")

    def test_database_only_results(self):
        self._ask("công văn nghỉ phép")
        self.assertEqual(SearchQueryLog.objects.get().sources, "db")

    def test_sharepoint_crash_cannot_erase_database_answer(self):
        # Nguồn phụ phải chết riêng. `search_sharepoint` đã bọc lỗi Graph, nhưng
        # một DriveItem kỳ dị vẫn có thể làm nổ ở tầng dựng dict.
        with patch(
            "apps.assistant.services.m365_search.search_sharepoint",
            side_effect=GraphAPIError("sập mạng", status_code=503),
        ):
            response = ask("công văn nghỉ phép", self.hr)
        self.assertTrue(response["partial"])
        self.assertTrue(response["results"])
        log = SearchQueryLog.objects.get()
        self.assertEqual(log.sources, "db")
        self.assertEqual(log.error_note, "unavailable")

    def test_sharepoint_source_is_asked_as_the_asking_user(self):
        # Graph chạy app-only nên bản thân nó KHÔNG biết ai đang hỏi. Toàn bộ
        # quyền của nguồn này phụ thuộc vào đúng một tham số `user` ở đây; đánh
        # rơi nó là mọi tài khoản đọc được tên tệp của cả site.
        with patch(
            "apps.assistant.services.m365_search.search_sharepoint", return_value=([], None)
        ) as sp:
            ask("công văn nghỉ phép", self.hr)
        self.assertEqual(sp.call_args[0][1], self.hr)
        self.assertIs(sp.call_args[0][1], self.hr)

    def test_restricted_sharepoint_note_is_not_a_degraded_answer(self):
        # Người không có quyền sổ công văn bị chặn ở nguồn phụ là chuyện bình
        # thường; báo "partial" sẽ làm họ tưởng hệ thống hỏng.
        response = self._ask("công văn nghỉ phép", note="restricted")
        self.assertFalse(response["partial"])
        self.assertEqual(SearchQueryLog.objects.get().error_note, None)

    def test_database_errors_are_not_swallowed(self):
        # DB là nguồn chính và là nguồn có RBAC: lỗi ở đây là lỗi server thật,
        # phải leo lên view (T7 trả 500 + log), không được hóa "0 kết quả".
        with patch(
            "apps.assistant.services.db_search.search_database",
            side_effect=RuntimeError("DB down"),
        ):
            with self.assertRaises(RuntimeError):
                ask("công văn nghỉ phép", self.hr)
        self.assertEqual(SearchQueryLog.objects.count(), 0)

    def test_results_are_capped(self):
        rows = [_db_row(f"r{i}", 10) for i in range(30)]
        response = self._ask("công văn", db=rows)
        self.assertEqual(len(response["results"]), 20)
        self.assertEqual(SearchQueryLog.objects.get().result_count, 20)

    def test_question_is_truncated_for_the_log(self):
        self._ask("công văn " * 100)
        self.assertLessEqual(len(SearchQueryLog.objects.get().question), 500)

    def test_log_records_the_asking_user_not_the_result_owner(self):
        self._ask("công văn nghỉ phép", user=self.emp)
        log = SearchQueryLog.objects.get()
        self.assertEqual(log.user, self.emp)
        self.assertEqual(log.created_by, self.emp)
        # EMPLOYEE không có scope -> không có kết quả DB nào được ghi log.
        self.assertEqual(log.sources, "none")
