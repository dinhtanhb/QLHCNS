"""Atoms presentation regressions for page-scoped candidate grouping."""
from html.parser import HTMLParser
from types import SimpleNamespace
from django.test import TestCase
from django.urls import reverse
from apps.common.templatetags.ui_components import ui_status_groups
from apps.portal import test_home_dashboard as fixtures
from apps.recruitment.models import Candidate


class BoardLinks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "ui-candidate-link" in attrs.get("class", "").split():
            self.links.append(attrs["href"])


class AtomsUITests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_grouping_preserves_all_rows_order_and_unknown_status_without_queries(self):
        rows = [SimpleNamespace(pk=1,status="New"), SimpleNamespace(pk=2,status="Unknown"),
                SimpleNamespace(pk=3,status="New"), SimpleNamespace(pk=4,status="Hired")]
        with self.assertNumQueries(0):
            groups = ui_status_groups(rows,"recruitment.candidate:status")
        grouped = {g["code"]:[r.pk for r in g["rows"]] for g in groups}
        self.assertEqual(grouped["New"],[1,3])
        self.assertEqual(grouped["Unknown"],[2])
        self.assertEqual(grouped["Hired"],[4])
        self.assertEqual(sum(len(g["rows"]) for g in groups),len(rows))
        self.assertEqual([r.pk for r in rows],[1,2,3,4])
        self.assertEqual(grouped["Screening"],[])

    def test_board_uses_only_current_page_and_preserves_access_and_escape(self):
        Candidate.objects.bulk_create([Candidate(candidate_code=f"ATOMS-{i:02d}",
            full_name="<script>fake</script>",phone_number="0900000000",email="fake@example.test",
            source="<unsafe>",status="New" if i%2 else "Hired") for i in range(21)])
        hr = self.user("HR_MANAGER",True)
        self.client.force_login(hr)
        response = self.client.get(reverse("portal:hr_candidate_list"),{"page":2})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context["page_obj"].number,2)
        expected = [reverse("portal:hr_candidate_detail",args=[r.pk]) for r in response.context["candidates"]]
        self.assertEqual(len(expected),1)
        self.assertEqual(BoardLinks(response.content.decode()).links,expected)
        self.assertContains(response,"Chỉ hiển thị ứng viên trong trang 2 hiện tại")
        self.assertContains(response,"&lt;script&gt;fake&lt;/script&gt;")
        self.assertNotContains(response,"<script>fake</script>")
        self.assertContains(response,'class="ui-table ui-recruitment-table"')
        employee = self.user("EMPLOYEE",True)
        self.client.force_login(employee)
        self.assertEqual(self.client.get(reverse("portal:hr_candidate_list")).status_code,403)
