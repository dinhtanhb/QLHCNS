"""Policy approved by the project owner on 20 October 2026."""
from datetime import date
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.portal import tests as fixtures
from apps.document.models import DispatchBook, OfficialDispatch, PersonnelDecision
from apps.leave.models import LeaveRequest, LeaveType
from apps.recruitment.models import Candidate
from apps.security.data_access import can_read_file, visible_leave_requests_for, visible_personnel_decisions_for
from apps.security.permissions import has_permission
from apps.assistant.nlp import parse
from apps.assistant.db_search import search_database
from apps.assistant.tests_m365_search import _FakeClient, _in, _hit, SITE, ASSISTANT_SETTINGS
from apps.assistant.m365_search import search_sharepoint


class DocumentPolicyTests(TestCase):
    make_employee = fixtures.PortalSensitiveWorkflowTests.make_employee
    make_user = fixtures.PortalSensitiveWorkflowTests.make_user

    @classmethod
    def setUpTestData(cls):
        fixtures.PortalSensitiveWorkflowTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.owner = self.make_employee("POL-OWNER")
        self.child = self.make_employee("POL-CHILD")
        self.grandchild = self.make_employee("POL-GRANDCHILD")
        self.other = self.make_employee("POL-OTHER")
        self.child.manager = self.owner
        self.child.save(update_fields=["manager"])
        self.grandchild.manager = self.child
        self.grandchild.save(update_fields=["manager"])
        self.kind = LeaveType.objects.create(leave_type_code="POL", leave_type_name="Synthetic")
        self.leaves = [LeaveRequest.objects.create(employee=e, leave_type=self.kind,
            from_date=date(2026, 11, 2), to_date=date(2026, 11, 2))
            for e in (self.owner, self.child, self.grandchild, self.other)]
        self.decisions = [PersonnelDecision.objects.create(employee=e, template_slug="synthetic",
            decision_no=f"POL-{i}", status="Issued")
            for i, e in enumerate((self.owner, self.child, self.grandchild, self.other))]

    def test_leave_read_scope_is_reporting_line_even_for_hr_and_director(self):
        for role in ("EMPLOYEE", "HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER", "SYS_ADMIN"):
            user = self.make_user(role, self.owner, "pol-leave-" + role)
            with self.subTest(role=role):
                self.assertEqual(set(visible_leave_requests_for(user).values_list("pk", flat=True)),
                                 {obj.pk for obj in self.leaves[:3]})
                self.assertTrue(can_read_file(user, self.leaves[2]))
                self.assertFalse(can_read_file(user, self.leaves[3]))
                self.client.force_login(user)
                page = self.client.get(reverse("portal:leave_list"))
                self.assertNotContains(page, self.other.full_name)
                self.assertEqual({r["url"] for r in search_database(parse("đơn xin nghỉ"), user)},
                                 {reverse("portal:leave_list")})
            user.employee = None
            user.save(update_fields=["employee"])

    def test_decision_list_detail_search_and_file_use_same_scope(self):
        for role in ("EMPLOYEE", "HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER", "PROJECT_MANAGER", "SYS_ADMIN"):
            user = self.make_user(role, self.owner, "pol-decision-" + role)
            count = 4 if role in ("HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER") else 3
            with self.subTest(role=role):
                self.assertEqual(visible_personnel_decisions_for(user).count(), count)
                self.assertEqual(can_read_file(user, self.decisions[3]), count == 4)
                self.client.force_login(user)
                self.assertEqual(self.client.get(reverse("portal:personnel_decision_list")).status_code, 200)
                self.assertEqual(self.client.get(reverse("portal:personnel_decision_detail", args=[self.decisions[3].pk])).status_code,
                                 200 if count == 4 else 403)
                self.assertEqual(len(search_database(parse("quyết định"), user)), count)
                user.is_active = False
                self.assertFalse(visible_personnel_decisions_for(user).exists())
            user.is_active = True
            user.employee = None
            user.save(update_fields=["employee", "is_active"])

    def test_candidate_and_asset_role_matrix_and_write_denial(self):
        candidate = Candidate.objects.create(candidate_code="POL-CV", full_name="Synthetic Candidate",
                                              email="qa@example.test", phone_number="000")
        for role in ("EMPLOYEE", "SYS_ADMIN", "HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER", "PROJECT_MANAGER", "PROJECT_COORDINATOR"):
            user = self.make_user(role, self.owner, "pol-matrix-" + role)
            cv = role in ("HR_MANAGER", "HR_OFFICER", "DIRECTOR", "PROJECT_MANAGER", "PROJECT_COORDINATOR")
            asset = role in ("HR_MANAGER", "HR_OFFICER", "DIRECTOR", "FINANCE_OFFICER")
            with self.subTest(role=role):
                self.assertEqual(has_permission(user, "view_candidate"), cv)
                self.assertEqual(has_permission(user, "view_asset"), asset)
                self.assertEqual(can_read_file(user, candidate), cv)
                self.client.force_login(user)
                page = self.client.get(reverse("portal:hr_candidate_detail", args=[candidate.pk]))
                self.assertEqual(page.status_code, 200 if cv else 403)
                if cv and role not in ("HR_MANAGER", "HR_OFFICER"):
                    self.assertNotContains(page, 'action="' + reverse("portal:hr_interview_create", args=[candidate.pk]) + '"')
                    self.client.post(reverse("portal:hr_candidate_onboard", args=[candidate.pk]))
                    candidate.refresh_from_db()
                    self.assertEqual(candidate.status, "New")
            user.employee = None
            user.save(update_fields=["employee"])

    @override_settings(**{**ASSISTANT_SETTINGS, "M365_FOLDER_MAP": {
        **ASSISTANT_SETTINGS["M365_FOLDER_MAP"], "activity_reports": "BaoCaoHoatDong"}})
    def test_graph_type_only_month_queries_and_private_boundaries(self):
        user = self.make_user("EMPLOYEE", self.owner, "pol-graph")
        for question, folder, allowed in (
            ("tìm công văn đến tháng 10/2026", "CongVanDen", True),
            ("tìm công văn đi tháng 9/2026", "CongVanDi", True),
            ("tìm báo cáo hoạt động tháng 9/2026", "BaoCaoHoatDong", True),
        ):
            parsed = parse(question)
            month = parsed.date_from.month
            hit = _hit("Synthetic.pdf", f"{SITE}/{folder}/Synthetic.pdf", f"2026-{month:02}-25T00:00:00Z")
            fake = _FakeClient(listings={folder: [hit, _in("HoSoUngVien", "secret.pdf")]})
            with patch("apps.assistant.m365_search.get_graph_client", return_value=fake):
                rows, note = search_sharepoint(parsed, user)
            self.assertEqual([r["title"] for r in rows], ["Synthetic.pdf"])
            self.assertEqual([r[1] for r in fake.list_calls], [folder])

    @override_settings(**{**ASSISTANT_SETTINGS, "M365_FOLDER_MAP": {
        **ASSISTANT_SETTINGS["M365_FOLDER_MAP"], "activity_reports": "BaoCaoHoatDong"}})
    def test_sharepoint_file_rechecks_role_and_rejects_forged_or_private_paths(self):
        from django.core import signing
        from unittest.mock import Mock
        user = self.make_user("EMPLOYEE", self.owner, "pol-download")
        fake = _FakeClient()
        fake.download_file = Mock(return_value=b"%PDF-1.4 synthetic")
        self.client.force_login(user)
        with patch("apps.m365.graph_client.get_graph_client", return_value=fake):
            for folder, allowed in (("CongVanDen", True), ("CongVanDi", True),
                                    ("BaoCaoHoatDong", True), ("HoSoUngVien", False),
                                    ("DonNghiPhep", False), ("CongVan", False)):
                token = signing.dumps(f"{SITE}/{folder}/test.pdf", salt="assistant-file", compress=True)
                url = reverse("assistant:sharepoint_file", args=[token])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200 if allowed else 404)
                if allowed:
                    self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 synthetic")
                    self.assertIn("no-store", response["Cache-Control"])
            fake.download_file.reset_mock()
            invalid = signing.dumps(f"{SITE}/CongVanDen/%2e%2e/secret.pdf", salt="assistant-file")
            self.assertEqual(self.client.get(reverse("assistant:sharepoint_file", args=[invalid])).status_code, 404)
            self.assertEqual(self.client.get(reverse("assistant:sharepoint_file", args=["forged"])).status_code, 404)
            fake.download_file.assert_not_called()
            token = signing.dumps(f"{SITE}/HoSoUngVien/test.pdf", salt="assistant-file")
            from apps.security.models import Role
            user.role = Role.objects.get_or_create(role_code="DIRECTOR", defaults={"role_name": "DIRECTOR"})[0]
            user.save(update_fields=["role"])
            response = self.client.get(reverse("assistant:sharepoint_file", args=[token]))
            self.assertEqual(response.status_code, 200)
            list(response.streaming_content)
            user.role = Role.objects.get(role_code="EMPLOYEE")
            user.save(update_fields=["role"])
            self.assertEqual(self.client.get(reverse("assistant:sharepoint_file", args=[token])).status_code, 404)
