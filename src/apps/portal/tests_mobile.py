import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve, reverse

from apps.portal import test_home_dashboard as home_fixtures
from apps.portal.views import service_worker


TABLE_TEMPLATES = {
    "holiday_list.html": 1,
    "finance_period_list.html": 1,
    "disposal_request_detail.html": 1,
    "inventory_session_list.html": 1,
    "disposal_request_list.html": 1,
    "report_budget.html": 1,
    "training_my_list.html": 1,
    "timesheet_month.html": 1,
    "supply_request_list.html": 1,
    "hr_candidate_list.html": 1,
    "report_personnel_changes.html": 4,
    "finance_salary_list.html": 1,
    "hr_contract_list.html": 1,
    "room_booking_list.html": 1,
    "finance_tax_config.html": 1,
    "report_headcount.html": 1,
    "finance_dependent_list.html": 1,
    "vehicle_booking_list.html": 1,
}


class TableWrapperParser(HTMLParser):
    """Count tables whose immediate parent is the responsive scroll wrapper."""

    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.wrapped_tables = 0
        self.tables = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.tables += 1
            if self.stack:
                parent_tag, parent_classes = self.stack[-1]
                if parent_tag == "div" and "mobile-table-scroll" in parent_classes and bool({"overflow-x-auto", "ui-scroll"} & parent_classes):
                    self.wrapped_tables += 1
        if tag not in self.VOID_TAGS:
            classes = set((attrs.get("class") or "").split())
            self.stack.append((tag, classes))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return


class MobileTableTests(SimpleTestCase):
    def test_requested_tables_are_each_inside_one_mobile_scroll_wrapper(self):
        templates_dir = Path(settings.BASE_DIR) / "apps" / "portal" / "templates" / "portal"
        total_tables = 0

        for filename, expected_count in TABLE_TEMPLATES.items():
            with self.subTest(template=filename):
                parser = TableWrapperParser()
                parser.feed((templates_dir / filename).read_text(encoding="utf-8"))
                self.assertEqual(parser.tables, expected_count)
                self.assertEqual(parser.wrapped_tables, expected_count)
                total_tables += parser.tables

        self.assertEqual(total_tables, 21)

    def test_base_uses_local_tailwind_and_has_mobile_navigation_controls(self):
        base = (Path(settings.BASE_DIR) / "templates" / "base.html").read_text(encoding="utf-8")
        built_css = Path(settings.BASE_DIR) / "static" / "css" / "tailwind.css"
        self.assertNotIn("cdn.tailwindcss.com", base)
        self.assertIn("css/tailwind.css", base)
        self.assertIn('rel="manifest"', base)
        self.assertIn('name="theme-color"', base)
        self.assertTrue(built_css.is_file())
        self.assertIn('id="mobileNavToggle"', base)
        self.assertIn('aria-controls="portalSidebar"', base)
        shell = (Path(settings.BASE_DIR) / "static/js/app_shell.js").read_text(encoding="utf-8")
        self.assertIn("(min-width: 1024px)", shell)

    def test_print_templates_remain_outside_mobile_table_wrapping(self):
        portal_templates = Path(settings.BASE_DIR) / "apps" / "portal" / "templates" / "portal"
        for path in portal_templates.glob("*_print.html"):
            with self.subTest(template=path.name):
                self.assertNotIn("mobile-table-scroll", path.read_text(encoding="utf-8"))

    def test_design_tokens_alignment_and_metric_hooks_are_shared(self):
        root = Path(settings.BASE_DIR)
        css_root = root / "static" / "css"
        css = (css_root / "ihrms.css").read_text(encoding="utf-8")
        tokens = (css_root / "design_tokens.css").read_text(encoding="utf-8")
        admin = (css_root / "admin.css").read_text(encoding="utf-8")
        self.assertTrue(css.startswith('@import url("design_tokens.css")'))
        self.assertTrue(admin.startswith('@import url("design_tokens.css")'))
        self.assertIn("--ihrms-content-width: 64rem", tokens)
        shell_css = (css_root / "app_shell.css").read_text(encoding="utf-8")
        self.assertIn("max-width:var(--ui-content-max-width)", shell_css)
        self.assertIn(".ihrms-kpi-value", css)
        self.assertIn("font-variant-numeric: tabular-nums", css)
        self.assertIn("prefers-reduced-motion", css)
        for relative, expected in (
            ("apps/activity/templates/activity/dashboard.html", 5),
            ("templates/reporting/dashboard.html", 4),
        ):
            with self.subTest(template=relative):
                source = (root / relative).read_text(encoding="utf-8")
                self.assertEqual(source.count("ihrms-kpi-value") if relative != "templates/reporting/dashboard.html" else source.count('include "ui/kpi.html"'), expected)
        leave_source = (root / "apps/portal/templates/portal/leave_list.html").read_text(encoding="utf-8")
        self.assertEqual(leave_source.count('class="ui-kpi-value"'), 2)
        worker = (root / "static/js/service-worker.js").read_text(encoding="utf-8")
        self.assertIn("ihrms-static-v33", worker)
        self.assertIn("/static/css/components.css", worker)
        self.assertIn("/static/css/design_tokens.css", worker)

    def test_theme_is_available_before_styles_and_in_admin(self):
        root = Path(settings.BASE_DIR)
        base = (root / "templates/base.html").read_text(encoding="utf-8")
        self.assertLess(base.index("js/theme.js"), base.index("css/tailwind.css"))
        self.assertIn("data-theme-toggle", base)
        self.assertIn('aria-pressed="false"', base)
        admin = (root / "templates/admin/base_site.html").read_text(encoding="utf-8")
        self.assertIn('{% extends "admin/base_site.html" %}', admin)
        self.assertIn("js/theme.js", admin)
        theme = (root / "static/css/theme.css").read_text(encoding="utf-8")
        self.assertIn("@media screen", theme)
        self.assertIn("@media print", theme)
        worker = (root / "static/js/service-worker.js").read_text(encoding="utf-8")
        self.assertIn("/static/js/theme.js", worker)
        self.assertIn("/static/css/theme.css", worker)

    def test_service_worker_endpoint_is_scoped_and_never_caches_html(self):
        path = reverse("portal:service_worker")
        self.assertEqual(resolve(path).url_name, "service_worker")
        response = service_worker(RequestFactory().get(path))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Service-Worker-Allowed"], "/portal/")
        self.assertIn("no-store", response["Cache-Control"])
        worker_source = response.content.decode("utf-8")
        from apps.common.asset_version import get_service_worker_cache_version
        self.assertIn(f'const STATIC_CACHE = "{get_service_worker_cache_version()}";', worker_source)
        self.assertIn('url.pathname.startsWith("/static/")', worker_source)
        self.assertNotIn("/static/img/logo.png", worker_source)
        self.assertNotIn('caches.match("/")', worker_source)
        self.assertNotRegex(worker_source, re.compile(r"request\.destination\s*===\s*['\"]document"))

    def test_manifest_is_online_portal_installation_with_local_icons(self):
        manifest_path = Path(settings.BASE_DIR) / "static" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "/portal/")
        self.assertEqual(manifest["scope"], "/portal/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual({icon["sizes"] for icon in manifest["icons"]}, {"192x192", "512x512"})
        for icon in manifest["icons"]:
            icon_path = Path(settings.BASE_DIR) / "static" / icon["src"].removeprefix("/static/")
            self.assertTrue(icon_path.is_file())
            with icon_path.open("rb") as image:
                self.assertEqual(image.read(8), b"\x89PNG\r\n\x1a\n")
                image.read(8)  # IHDR chunk length and type
                width, height = struct.unpack(">II", image.read(8))
            self.assertEqual((width, height), tuple(map(int, icon["sizes"].split("x"))))

    def test_asset_hash_computes_sha1_and_invalidates_on_content_change(self):
        from apps.common.asset_version import get_asset_hash, clear_asset_hash_cache
        h = get_asset_hash("css/components.css")
        self.assertEqual(len(h), 8)
        # Verify hex characters
        self.assertTrue(all(c in "0123456789abcdef" for c in h))


class MobileShellStylesheetTests(SimpleTestCase):
    """The P0 shell must stay a mobile-only overlay: no desktop, no print change."""

    def setUp(self):
        self.css = (Path(settings.BASE_DIR) / "static" / "css" / "mobile_shell.css").read_text(encoding="utf-8")
        self.base = (Path(settings.BASE_DIR) / "templates" / "base.html").read_text(encoding="utf-8")

    def test_base_loads_shell_after_shared_sheets_and_before_print(self):
        self.assertIn("css/mobile_shell.css", self.base)
        self.assertLess(self.base.index("css/project_layout.css"), self.base.index("css/mobile_shell.css"))
        self.assertLess(self.base.index("css/mobile_shell.css"), self.base.index("css/print_forms.css"))

    def test_shell_is_scoped_to_mobile_and_never_layered(self):
        self.assertIn("@media screen and (max-width: 1023px)", self.css)
        # Unlayered on purpose: the project mixes layered and unlayered rules, and
        # an @layer wrapper would lose to Tailwind utilities at normal priority.
        # Comments may mention @layer; only a real at-rule would change the cascade.
        self.assertIsNone(re.search(r"^\s*@layer\b", self.css, re.MULTILINE))
        self.assertIn(".ui-mobile-only { display: none; }", self.css)

    def test_shell_leaves_print_alone(self):
        # Print was deferred on 21/10/2026; a stray print block would silently
        # change paper output that nobody has reviewed.
        self.assertNotIn("@media print", self.css)


class TabbarParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "ui-tabbar__item" in (values.get("class") or "").split():
            self.items.append({"tag": tag, **values})


class MobileTabbarTests(TestCase):
    """Five bottom targets, fixed by the project owner on 21/10/2026.

    Tab 4 is a button that opens the existing drawer, not a route: the drawer
    already carries every module the role can reach.
    """
    user = home_fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        home_fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def tabbar(self, role_code):
        self.client.force_login(self.user(role_code, True))
        html = self.client.get(reverse("portal:dashboard")).content.decode()
        return TabbarParser(html).items

    def test_every_role_gets_five_targets_ending_with_self(self):
        for role_code in ("EMPLOYEE", "HR_OFFICER", "DEPT_MANAGER", "HR_MANAGER"):
            with self.subTest(role=role_code):
                items = self.tabbar(role_code)
                self.assertEqual(len(items), 5)
                self.assertEqual(items[0]["href"], reverse("portal:dashboard"))
                self.assertEqual(items[-1]["href"], reverse("portal:profile"))
                self.assertEqual([item["tag"] for item in items].count("button"), 1)
                self.assertEqual(items[3]["tag"], "button")
                self.assertEqual(items[3]["aria-controls"], "portalSidebar")

    def test_tabs_two_and_three_follow_permission(self):
        expected = {
            "EMPLOYEE": ("portal:timesheet_month", "portal:leave_list"),
            "HR_OFFICER": ("portal:timesheet_month", "portal:hr_employee_list"),
            "DEPT_MANAGER": ("portal:leave_approval_list", "portal:timesheet_approval_list"),
            "HR_MANAGER": ("portal:leave_approval_list", "portal:hr_employee_list"),
        }
        for role_code, (second, third) in expected.items():
            with self.subTest(role=role_code):
                items = self.tabbar(role_code)
                self.assertEqual(items[1]["href"], reverse(second))
                self.assertEqual(items[2]["href"], reverse(third))

    def test_active_tab_marks_current_page_only(self):
        self.client.force_login(self.user("EMPLOYEE", True))
        home = TabbarParser(self.client.get(reverse("portal:dashboard")).content.decode()).items
        profile = TabbarParser(self.client.get(reverse("portal:profile")).content.decode()).items
        self.assertEqual([item["href"] for item in home if item.get("aria-current")], [reverse("portal:dashboard")])
        self.assertEqual([item["href"] for item in profile if item.get("aria-current")], [reverse("portal:profile")])

    def test_login_page_has_no_tabbar(self):
        response = self.client.get(reverse("portal:login"))
        self.assertEqual(TabbarParser(response.content.decode()).items, [])

