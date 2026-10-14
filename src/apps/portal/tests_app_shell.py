"""Shell regression contracts: keep the old navigation's URL/permission set."""
from collections import Counter
from html.parser import HTMLParser

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from apps.portal import tests as portal_tests
from apps.security.permissions import has_permission


class NavigationLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("class") == "ui-sidebar-nav":
            self.depth += 1
        if tag == "a" and self.depth:
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "nav" and self.depth:
            self.depth -= 1


class AppShellTests(TestCase):
    setUpTestData = classmethod(portal_tests.PortalSensitiveWorkflowTests.setUpTestData.__func__)
    make_user = portal_tests.PortalSensitiveWorkflowTests.make_user
    make_employee = portal_tests.PortalSensitiveWorkflowTests.make_employee

    def render_shell(self, user, path=None, notices=()):
        request = RequestFactory().get(path or reverse("portal:dashboard"))
        request.user = user
        request.resolver_match = resolve(request.path)
        request.session = {}
        request._messages = FallbackStorage(request)
        for level, text in notices:
            messages.add_message(request, level, text, extra_tags="shell-note")
        return render_to_string("base.html", {}, request=request)

    def expected_navigation(self, user):
        """Navigation inventory, excluding unusable personal requests for unlinked accounts."""
        def url(name):
            return reverse("portal:" + name)
        expected = [url(name) for name in (
            "dashboard", "profile", "org_chart",
            "timesheet_month", "leave_list", "kpi_my_list", "payslip_list",
        )]
        if user.employee_id:
            expected.append(url("profile_change_request_list"))
        permission = lambda name: has_permission(user, name)
        if permission("manage_hr"):
            expected += [url(name) for name in ("hr_employee_list", "hr_contract_list", "lifecycle_case_list", "hcns_catalog", "profile_change_request_list")]
        if permission("manage_hr") or permission("approve_personnel_decision"):
            expected.append(url("personnel_decision_list"))
        for perm, name in (
            ("approve_leave", "leave_approval_list"), ("approve_timesheet", "timesheet_approval_list"),
            ("approve_document", "document_approval_list"), ("approve_activity_proposals", "activity_proposal_approval_list"),
        ):
            if permission(perm):
                expected.append(url(name))
        if any(permission(p) for p in ("manage_hr", "request_recruitment", "approve_recruitment")):
            expected.append(url("recruitment_hub"))
        if permission("request_recruitment") or permission("approve_recruitment"):
            expected.append(url("recruitment_list"))
        if permission("manage_hr"):
            expected += [url("hr_candidate_list"), url("hcns_catalog") + "?group=recruitment"]
        if permission("manage_finance"):
            expected += [url(name) for name in ("finance_period_list", "finance_salary_list", "finance_dependent_list", "finance_tax_config")]
        if permission("use_salary_scale_form"):
            expected.append(reverse("portal:hcns_draft", args=("salary-scale",)))
        expected += [url("document_list"), url("dispatch_list") + "?type=Incoming", url("dispatch_list") + "?type=Outgoing"]
        if permission("view_asset"):
            expected += [url(name) for name in ("asset_list", "asset_admin_list", "inventory_session_list", "disposal_request_list")]
        expected += [url(name) for name in ("room_booking_list", "vehicle_booking_list", "supply_request_list", "event_list", "training_my_list")]
        if permission("manage_calendar"):
            expected.append(url("holiday_list"))
        if permission("view_reports"):
            expected.append(url("report_hub"))
        if permission("view_activity_dashboard"):
            expected += [url(name) for name in ("activity_dashboard", "activity_calendar", "task_list")]
        return expected

    def test_menu_preserves_link_multiset_for_all_supported_roles_with_and_without_employee(self):
        roles = ("EMPLOYEE", "DEPT_MANAGER", "HR_OFFICER", "HR_MANAGER", "DIRECTOR", "SYS_ADMIN",
                 "FINANCE_OFFICER", "SUPER_ADMIN", "PROJECT_MANAGER", "PROJECT_COORDINATOR", "CBDA")
        for role in roles:
            for linked in (False, True):
                with self.subTest(role=role, linked=linked):
                    employee = self.make_employee(f"SHELL-{role}") if linked else None
                    user = self.make_user(role, employee, f"shell-{role}-{linked}")
                    parser = NavigationLinks()
                    html = self.render_shell(user)
                    parser.feed(html)
                    self.assertEqual(Counter(parser.links), Counter(self.expected_navigation(user)))
                    self.assertEqual('href="/admin/"' in html, has_permission(user, "view_admin_menu"))
                    self.assertEqual('href="/reports/"' in html, has_permission(user, "view_admin_menu"))

    def test_missing_employee_and_anonymous_shell_render_without_account_data_errors(self):
        user = self.make_user("SYS_ADMIN", None, "shell-missing-profile")
        html = self.render_shell(user)
        self.assertIn("shell-missing-profile", html)
        self.assertIn('id="portalSidebar"', html)
        anonymous = self.render_shell(AnonymousUser())
        self.assertNotIn('id="portalSidebar"', anonymous)
        self.assertNotIn('id="userMenuButton"', anonymous)
        self.assertIn('href="#main-content"', anonymous)

    def test_current_route_and_query_distinguish_outgoing_from_incoming(self):
        user = self.make_user("HR_MANAGER", None, "shell-active-route")
        html = self.render_shell(user, reverse("portal:dispatch_list") + "?type=Outgoing")
        parser = HTMLParser()  # HTML rendering must succeed before checking the contract.
        parser.feed(html)
        import re
        outgoing = re.search(r'<a[^>]+href="[^"]*type=Outgoing"[^>]*>', html)[0]
        incoming = re.search(r'<a[^>]+href="[^"]*type=Incoming"[^>]*>', html)[0]
        self.assertIn('aria-current="page"', outgoing)
        self.assertNotIn('aria-current="page"', incoming)
        default_html = self.render_shell(user, reverse("portal:dispatch_list"))
        default_incoming = re.search(r'<a[^>]+href="[^"]*type=Incoming"[^>]*>', default_html)[0]
        self.assertIn('aria-current="page"', default_incoming)

    def test_messages_use_numeric_levels_even_with_extra_tags(self):
        user = self.make_user("EMPLOYEE", None, "shell-alerts")
        html = self.render_shell(user, notices=((messages.SUCCESS, "Thành công giả"), (messages.ERROR, "Lỗi giả"), (messages.WARNING, "Cảnh báo giả"), (messages.INFO, "Thông tin giả")))
        self.assertEqual(html.count('role="alert"'), 2)
        self.assertEqual(html.count('role="status"'), 2)
        self.assertIn("ui-alert--danger", html)
        self.assertNotIn("data-auto-dismiss", html)

    def test_unlinked_account_menu_targets_keep_existing_http_permissions(self):
        expected = {
            "EMPLOYEE": (302, 403, 302), "DEPT_MANAGER": (302, 403, 302),
            "HR_OFFICER": (302, 200, 302), "HR_MANAGER": (302, 200, 200),
            "DIRECTOR": (302, 200, 200), "SYS_ADMIN": (200, 200, 302),
        }
        for role, statuses in expected.items():
            with self.subTest(role=role):
                user = self.make_user(role, None, "shell-target-" + role)
                user.is_staff = role == "SYS_ADMIN"
                user.save(update_fields=("is_staff",))
                self.client.force_login(user)
                html = self.render_shell(user)
                for url, status in zip(("/admin/", "/reports/", "/portal/reports/"), statuses):
                    self.assertEqual(self.client.get(url).status_code, status)
                self.assertEqual('href="/admin/"' in html, has_permission(user, "view_admin_menu"))
                self.assertEqual('href="/reports/"' in html, has_permission(user, "view_admin_menu"))
        admin = self.make_user("SUPER_ADMIN", None, "shell-unlinked-superuser")
        admin.is_staff = admin.is_superuser = True
        admin.save(update_fields=("is_staff", "is_superuser"))
        self.client.force_login(admin)
        for url in ("/admin/", "/reports/", "/portal/reports/"):
            self.assertEqual(self.client.get(url).status_code, 200)
