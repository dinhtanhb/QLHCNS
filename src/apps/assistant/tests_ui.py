"""Kiểm tra trang chat và nút nổi dùng đúng thành phần của design system."""
import re
from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from apps.portal import test_home_dashboard as fixtures

CSS_PATH = Path(__file__).resolve().parents[2] / "static" / "css" / "assistant.css"
JS_PATH = Path(__file__).resolve().parents[2] / "static" / "js" / "assistant.js"


class AssistantUiTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user(cls, "HR_MANAGER", True)

    def _get(self, name):
        self.client.force_login(self.hr)
        return self.client.get(reverse(name))

    def test_page_contains_root_and_api_url(self):
        response = self._get("assistant:assistant_page")
        self.assertContains(response, 'class="ui-card assistant-root')
        self.assertContains(response, reverse("assistant:api_search"))

    def test_question_input_has_visible_label(self):
        # Audit layout chỉ tính label nhìn thấy được trong .ui-main.
        response = self._get("assistant:assistant_page")
        self.assertContains(response, '<label class="ui-field-label" for="assistantInput">')
        self.assertNotContains(response, 'class="ui-sr-only" for="assistantInput"')

    def test_submit_button_uses_shared_button_class(self):
        response = self._get("assistant:assistant_page")
        self.assertContains(response, 'class="ui-button ui-button--primary"')

    def test_base_page_renders_fab_and_assets(self):
        response = self._get("portal:dashboard")
        self.assertContains(response, 'id="assistantFab"')
        self.assertContains(response, "css/assistant.css")
        self.assertContains(response, "js/assistant.js")

    def test_fab_markup_is_accessibility_wired(self):
        response = self._get("portal:dashboard")
        self.assertContains(response, 'aria-controls="assistantDock"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'id="assistantDock" class="assistant-dock"')
        self.assertContains(response, 'aria-label="Trợ lý tài liệu" hidden')
        self.assertContains(response, 'data-api="' + reverse("assistant:api_search") + '"')
        self.assertContains(response, 'data-page-url="' + reverse("assistant:assistant_page") + '"')

    def test_result_icons_come_from_the_shared_icon_partial(self):
        # assistant.js clone từ hai template này; thiếu một là thẻ kết quả mất icon.
        # Bản trước đặt chúng trong khối của nút nổi, nên trang /assistant/ bị mất icon.
        for route in ("portal:dashboard", "assistant:assistant_page"):
            with self.subTest(route=route):
                response = self._get(route)
                self.assertContains(response, 'id="assistantIconIHRMS"')
                self.assertContains(response, 'id="assistantIconSharePoint"')

    def test_fab_hidden_from_anonymous(self):
        response = self.client.get(reverse("portal:login"))
        self.assertNotContains(response, 'id="assistantFab"')

    def test_fab_absent_on_assistant_page(self):
        # Trang /assistant/ đã có khung chat đầy đủ, nút nổi là trùng lặp.
        response = self._get("assistant:assistant_page")
        self.assertNotContains(response, 'id="assistantFab"')

    def test_assistant_assets_resolve_via_static_finders(self):
        # The {% asset %} tag silently returns v=dynamic for a missing file,
        # so a typo in base.html would render a 404 stylesheet, not an error.
        self.assertIsNotNone(finders.find("css/assistant.css"))
        self.assertIsNotNone(finders.find("js/assistant.js"))

    def test_assistant_css_uses_design_tokens_only(self):
        # Mirrors ops/audit_design_tokens.py so the gate runs with the unit suite.
        css = re.sub(r"/\*[\s\S]*?\*/", "", CSS_PATH.read_text(encoding="utf-8"))
        for token in ("#", "rgb(", "rgba(", "prefers-color-scheme"):
            self.assertNotIn(token, css, f"assistant.css must not hard-code {token}")

    def test_assistant_js_sends_csrf_header_and_never_injects_html(self):
        # Django's test client leaves CSRF off, so no request test can prove the
        # browser will not be rejected by api_search (see ledger C47).
        js = JS_PATH.read_text(encoding="utf-8")
        self.assertIn("X-CSRFToken", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("document.write", js)

    def test_assistant_js_allows_only_internal_or_https_links(self):
        # `safeUrl` là chắn duy nhất giữa một `webUrl` lấy từ Graph và
        # `card.href`: xóa nó mà suite vẫn xanh nghĩa là một chuỗi
        # javascript: từ dữ liệu ngoài đủ để chạy script trong phiên người dùng.
        js = JS_PATH.read_text(encoding="utf-8")
        self.assertIn("function safeUrl", js)
        self.assertIn("javascript:", js)
        self.assertIn("data:", js)
        self.assertIn("card.href = href", js)
        self.assertIn("noopener noreferrer", js)

    def test_assistant_css_hides_the_widget_when_printing(self):
        # AGENTS.md yêu cầu bỏ chrome không thuộc bản in. Probe in là tệp tạm
        # ngoài Git, nên quy tắc này phải có một test trong suite.
        css = CSS_PATH.read_text(encoding="utf-8")
        block = re.search(r"@media print\s*\{([^}]*)\}", css)
        self.assertIsNotNone(block, "assistant.css phải có khối @media print")
        for selector in (".assistant-fab", ".assistant-dock"):
            self.assertIn(selector, block.group(1))
        self.assertIn("display: none", block.group(1))

    def test_assistant_js_names_session_expiry_separately_from_no_results(self):
        # `login_required` trả 302 về trang đăng nhập; fetch đi theo redirect nên
        # `ok` vẫn true và JSON hỏng thành {}. Rơi vào `MESSAGES.empty` thì người
        # dùng nghe "không có tài liệu trong phạm vi quyền" khi hệ thống chỉ hết
        # phiên - cùng lớp lỗi mà C41 cấm.
        js = JS_PATH.read_text(encoding="utf-8")
        self.assertIn("session_expired", js)
        self.assertIn("application/json", js)

    def test_assistant_sources_contain_no_non_vietnamese_script(self):
        # AGENTS.md: mã nguồn chỉ tiếng Việt + ASCII. Scan này từng phải chạy
        # tay bằng script tạm ngoài Git; một chữ Hán lọt vào comment không làm đỏ
        # test nào khác và review chỉ phát hiện khi đọc từng dòng.
        # Cho phép: ASCII in được + khoảng trắng (0x20-0x7E), dấu tiếng Việt,
        # `…`, `—`, `‘’“”` (0x2000-0x206F) và `·` (0x00B7). Cấm mọi ký tự khác,
        # gồm Cyrillic (0x0400-0x04FF) và CJK (0x3000 trở lên).
        allowed = set("…—‘’“”·")
        for path in (CSS_PATH, JS_PATH):
            text = path.read_text(encoding="utf-8")
            outside = {c for c in text if not (0x20 <= ord(c) <= 0x7E) and c not in allowed}
            for char in sorted(outside):
                self.assertLess(
                    ord(char), 0x3000,
                    f"{path.name}: ký tự ngoài tiếng Việt {char!r} (U+{ord(char):04X})",
                )
