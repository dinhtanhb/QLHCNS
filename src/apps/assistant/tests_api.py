import json

from django.core.cache import caches
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from apps.portal import test_home_dashboard as fixtures

SEARCH_URL = "assistant:api_search"
PAGE_URL = "assistant:assistant_page"


def _post(client, question, **extra):
    return client.post(
        reverse(SEARCH_URL),
        data=json.dumps({"question": question}, **extra),
        content_type="application/json",
    )


class AssistantApiTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user(cls, "HR_MANAGER", True)
        cls.emp = cls.user(cls, "EMPLOYEE", True)

    def setUp(self):
        # Bộ đếm throttle sống trong cache; không dọn thì giới hạn của test này
        # sẽ ăn sang test kế tiếp trong cùng tiến trình.
        caches["default"].clear()

    def _json(self, response):
        self.assertEqual(response["Content-Type"], "application/json")
        return response.json()

    def test_anonymous_cannot_post(self):
        response = _post(self.client, "công văn")
        # `login_required` redirect về trang đăng nhập, không lộ lý do.
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_anonymous_cannot_open_page(self):
        response = self.client.get(reverse(PAGE_URL))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    @override_settings(M365_STORAGE_ENABLED=False)
    def test_no_request_builds_a_graph_client(self):
        # `ops/run_tests.py` đặt M365_STORAGE_ENABLED=False chính vì test không
        # được chạm Microsoft. Nguồn phụ chỉ đọc credentials, không đọc cờ này,
        # nên trên máy có `.env` đã cấu hình thì mỗi câu hỏi hợp lệ là một lượt
        # gọi Graph thật - và `services` nuốt mọi exception nên cả cụm vẫn xanh.
        # Dựng client ở đây sẽ nổ, nên muốn xanh là phải tắt đúng cửa.
        from apps.assistant.models import SearchQueryLog

        with patch(
            "apps.assistant.m365_search.get_graph_client",
            side_effect=AssertionError("test không được gọi Graph"),
        ) as factory:
            self.client.force_login(self.hr)
            for question in ("công văn nghỉ phép", "128/CV", "quyết định"):
                self.assertEqual(_post(self.client, question).status_code, 200)
        factory.assert_not_called()
        self.assertEqual(SearchQueryLog.objects.count(), 3)

    @override_settings(M365_STORAGE_ENABLED=True)
    def test_storage_flag_on_but_permission_denied_still_makes_no_call(self):
        # Cửa quyền phải đứng trước cửa mạng: người hỏi không có quyền sổ công
        # văn thì dù M365 đã bật, trợ lý cũng không được lộ tên tệp của cả site.
        # Test này có bật cờ một cách giả định, nên nó chạy được trên mọi `.env`.
        with patch(
            "apps.assistant.m365_search.get_graph_client",
            side_effect=AssertionError("EMPLOYEE không được gọi Graph"),
        ) as factory:
            self.client.force_login(self.emp)
            payload = self._json(_post(self.client, "hồ sơ ứng viên"))
        factory.assert_not_called()
        self.assertFalse(payload["partial"])

    def test_page_renders_for_logged_in_user(self):
        self.client.force_login(self.hr)
        response = self.client.get(reverse(PAGE_URL))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trợ lý tài liệu")
        # Mốc để JS tìm thấy: nếu tên data-* đổi, `assistant.js` chết âm thầm
        # và trang vẫn render 200.
        self.assertContains(response, 'data-api="')
        self.assertContains(response, 'data-role="panel"')

    def test_post_valid_question_returns_contract(self):
        self.client.force_login(self.hr)
        payload = self._json(_post(self.client, "công văn nghỉ phép"))
        self.assertEqual(
            set(payload), {"query", "parsed", "took_ms", "partial", "results"}
        )
        self.assertEqual(payload["query"], "công văn nghỉ phép")
        self.assertIsInstance(payload["results"], list)

    def test_csrf_is_enforced(self):
        # Test client mặc định bỏ qua CSRF check; nếu sau này ai đó đánh dấu
        # endpoint `@csrf_exempt` để "cho JS gọi dễ", phải có gì đó đỏ.
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.hr)
        response = _post(strict, "công văn")
        self.assertEqual(response.status_code, 403)

    def test_short_question_400(self):
        self.client.force_login(self.hr)
        response = _post(self.client, "a")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._json(response)["error"], "question_too_short")

    def test_blank_question_400(self):
        self.client.force_login(self.hr)
        response = _post(self.client, "     ")
        self.assertEqual(self._json(response)["error"], "question_too_short")

    def test_missing_question_key_400(self):
        self.client.force_login(self.hr)
        response = self.client.post(
            reverse(SEARCH_URL), data=json.dumps({"q": "công văn"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._json(response)["error"], "question_too_short")

    def test_invalid_json_400(self):
        self.client.force_login(self.hr)
        response = self.client.post(
            reverse(SEARCH_URL), data="{bad", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._json(response)["error"], "invalid_json")

    def test_json_that_is_not_an_object_400(self):
        # `"công văn"` hay `[1,2]` là JSON hợp lệ nhưng `.get` sẽ nổ 500 nếu
        # không chặn kiểu dữ liệu ở ranh giới.
        self.client.force_login(self.hr)
        for body in ('"công văn"', "[1, 2]", "null", "42"):
            response = self.client.post(
                reverse(SEARCH_URL), data=body, content_type="application/json"
            )
            self.assertEqual(response.status_code, 400, body)
            self.assertEqual(self._json(response)["error"], "invalid_json")

    def test_non_utf8_body_400(self):
        self.client.force_login(self.hr)
        response = self.client.post(
            reverse(SEARCH_URL), data=b"\xff\xfe not utf8",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._json(response)["error"], "invalid_json")

    def test_get_not_allowed_405(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse(SEARCH_URL)).status_code, 405)

    def test_rate_limit_429(self):
        self.client.force_login(self.hr)
        statuses = [_post(self.client, "công văn").status_code for _ in range(31)]
        self.assertEqual(statuses[:30], [200] * 30)
        self.assertEqual(statuses[30], 429)
        final = _post(self.client, "công văn")
        self.assertEqual(self._json(final)["error"], "rate_limited")

    def test_rate_limit_is_per_user(self):
        self.client.force_login(self.hr)
        for _ in range(30):
            _post(self.client, "công văn")
        self.assertEqual(_post(self.client, "công văn").status_code, 429)
        self.client.force_login(self.emp)
        self.assertEqual(_post(self.client, "công văn").status_code, 200)

    def test_rejected_request_does_not_consume_quota(self):
        # Chặn định dạng TRƯỚC khi trừ quota: một script gửi 10.000 request sai
        # cú pháp không được khiến người dùng thật bị khóa.
        self.client.force_login(self.hr)
        for _ in range(40):
            _post(self.client, "a")
        self.assertEqual(_post(self.client, "công văn nghỉ phép").status_code, 200)

    def test_long_question_is_truncated_not_rejected(self):
        # Không chỉ "không bị từ chối": cắt ở ranh giới là điều duy nhất ngăn
        # một câu >500 ký tự đập vào cột `nvarchar(500)` lúc ghi log. Cắt sai chỗ
        # thì SQL Server báo DataError 500 mà test cũ vẫn xanh.
        from apps.assistant.models import SearchQueryLog

        self.client.force_login(self.hr)
        response = _post(self.client, "công văn " * 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self._json(response)["query"]), 500)
        self.assertEqual(len(SearchQueryLog.objects.get().question), 500)
