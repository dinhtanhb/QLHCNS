import json

from django.core.cache import caches
from django.test import Client, TestCase
from django.urls import reverse

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
        self.client.force_login(self.hr)
        response = _post(self.client, "công văn " * 200)
        self.assertEqual(response.status_code, 200)
