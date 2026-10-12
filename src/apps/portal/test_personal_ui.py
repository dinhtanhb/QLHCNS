"""Personal UI regressions; all fixtures are synthetic and tests use isolated DBs."""
from html.parser import HTMLParser
from types import SimpleNamespace
from decimal import Decimal

from django.test import TestCase
from django.template.loader import render_to_string
from django.urls import reverse

from apps.portal import test_home_dashboard as home_fixtures
from apps.attendance.models import MonthlyAttendanceSummary
from apps.hrm.models import EmployeeProfileChangeRequest
from apps.notification.models import Notification


class Forms(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.forms = []
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current = {"attrs": attrs, "fields": [], "buttons": []}
            self.forms.append(self.current)
        elif self.current and tag in ("input", "select", "textarea"):
            self.current["fields"].append(attrs)
        elif self.current and tag == "button":
            self.current["buttons"].append(attrs)

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


class PersonalUITests(TestCase):
    user = home_fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        home_fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_personal_pages_and_sensitive_scope(self):
        user = self.user("EMPLOYEE", True)
        other = self.user("DIRECTOR", True)
        Notification.objects.create(employee=other.employee, notification_type="Test", title="PRIVATE-OTHER", message="Not visible")
        self.client.force_login(user)
        for name in ("profile", "profile_change_request_list", "profile_change_request_create", "org_chart", "timesheet_month", "leave_list", "leave_create", "kpi_my_list", "payslip_list", "notification_list"):
            with self.subTest(name=name):
                response = self.client.get(reverse("portal:"+name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="ui-page ui-personal"')
                self.assertNotContains(response, user.employee.national_id)
                self.assertNotContains(response, "PRIVATE-OTHER")
                for form in Forms(response.content.decode()).forms:
                    if form["attrs"].get("method", "get").lower() == "post":
                        self.assertIn("csrfmiddlewaretoken", {f.get("name") for f in form["fields"]})
        self.assertNotContains(self.client.get(reverse("portal:kpi_my_list")), 'Chấm điểm KPI nhân viên')

    def test_leave_and_profile_form_constraints_are_preserved(self):
        user = self.user("EMPLOYEE", True)
        self.client.force_login(user)
        response = self.client.get(reverse("portal:leave_create"))
        forms = Forms(response.content.decode()).forms
        form = next(f for f in forms if "leave_type" in {x.get("name") for x in f["fields"]})
        fields = {x["name"]: x for x in form["fields"]}
        self.assertEqual(set(fields), {"csrfmiddlewaretoken", "leave_type", "from_date", "to_date", "reason"})
        self.assertTrue(all("required" in fields[n] for n in ("leave_type", "from_date", "to_date")))
        self.assertNotIn("required", fields["reason"])
        self.assertNotIn("min", fields["from_date"])
        response = self.client.get(reverse("portal:profile_change_request_create"))
        form = next(f for f in Forms(response.content.decode()).forms if f["attrs"].get("enctype") == "multipart/form-data")
        fields = {x["name"]: x for x in form["fields"]}
        self.assertEqual(set(fields), {"csrfmiddlewaretoken", "field_name", "new_value", "reason", "attachment"})
        self.assertEqual(fields["new_value"]["maxlength"], "500")
        self.assertNotIn("required", fields["attachment"])

    def test_profile_decision_visibility_and_submitter_values(self):
        owner = self.user("EMPLOYEE", True)
        hr = self.user("HR_OFFICER", True)
        EmployeeProfileChangeRequest.objects.create(employee=owner.employee, field_name="address", old_value="FAKE-OLD", new_value="FAKE-NEW", submitted_snapshot="FAKE-OLD")
        self.client.force_login(owner)
        response = self.client.get(reverse("portal:profile_change_request_list"))
        self.assertContains(response, "FAKE-NEW")
        self.assertNotContains(response, 'name="decision"')
        self.client.force_login(hr)
        response = self.client.get(reverse("portal:profile_change_request_list"))
        form = next(f for f in Forms(response.content.decode()).forms if "data-ui-confirm" in f["attrs"])
        self.assertEqual([(b["name"], b["value"]) for b in form["buttons"]], [("decision", "approve"), ("decision", "more_info"), ("decision", "reject")])
        self.assertContains(response, 'id="ui-confirm-dialog"', count=1)

    def test_attendance_approved_guard_and_field_names(self):
        user = self.user("EMPLOYEE", True)
        MonthlyAttendanceSummary.objects.create(employee=user.employee, year=2026, month=10, status="Approved")
        self.client.force_login(user)
        response = self.client.get(reverse("portal:timesheet_month"), {"month":10,"year":2026})
        self.assertContains(response, '<fieldset class="ui-form-fieldset" disabled>')
        self.assertContains(response, 'Đã duyệt — không thể tự sửa')
        self.assertContains(response, 'ui-print-only')
        self.assertContains(response, 'id="ui-confirm-dialog"', count=1)
        form = next(f for f in Forms(response.content.decode()).forms if f["attrs"].get("action") == reverse("portal:timesheet_summary_update"))
        self.assertEqual({f.get("name") for f in form["fields"]}, {"csrfmiddlewaretoken", "month", "year", "sick_days", "maternity_days", "compensatory_days", "annual_leave_days", "unpaid_leave_days"})

    def test_kpi_zero_is_a_valid_actual_and_existing_thresholds(self):
        for achievement, tone in ((Decimal("0"), "danger"), (Decimal("70"), "warning"), (Decimal("100"), "success")):
            result = SimpleNamespace(kpi_period="Kỳ giả", kpi_template=SimpleNamespace(weight=10), target=100, actual=Decimal("0"), achievement=achievement, score=0)
            html = render_to_string("portal/kpi_my_list.html", {"results":[result]})
            self.assertNotIn("Chưa cập nhật", html)
            self.assertIn('<td class="ui-number">0</td>', html)
            self.assertIn("ui-badge--"+tone, html)
