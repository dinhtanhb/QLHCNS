"""Recruitment presentation contracts, using synthetic data and existing guards."""
from datetime import date
from django.test import TestCase, RequestFactory
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from apps.portal import test_home_dashboard as fixtures
from apps.portal.test_personal_ui import Forms
from apps.recruitment.models import Candidate, Interview, Offer, RecruitmentRequest


class RecruitmentUITests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.candidate = Candidate.objects.create(candidate_code="UI-FAKE", full_name="Ứng viên giả",
            phone_number="0900000000", email="candidate@example.test")

    def test_activity_approval_menu_keeps_permission_and_project_scope(self):
        user = self.user("DIRECTOR", True)
        self.client.force_login(user)
        response = self.client.get(reverse("portal:dashboard"))
        html = response.content.decode().split('id="portalSidebar"', 1)[1].split('</nav>', 1)[0]
        href = 'href="' + reverse("portal:activity_proposal_approval_list") + '"'
        self.assertEqual(html.count(href), 1)
        self.assertGreater(html.index(href), html.index('id="menu-hoatdongduan"'))
        self.assertNotIn(href, html.split('id="menu-nhansu"')[1].split('</div>', 1)[0])
        # Approve-only context must expose only the authorized project destination.
        request = RequestFactory().get("/portal/")
        request.user = user
        html = render_to_string("base.html", {"user":user, "request":request,
            "can_approve_activity_proposals":True, "pending_activity_proposal_count":2})
        self.assertIn('id="menu-hoatdongduan"', html)
        self.assertIn(href, html)
        self.assertNotIn('id="menu-nhansu"', html)
        self.assertNotIn('href="'+reverse("portal:activity_dashboard")+'"', html)
        html = render_to_string("base.html", {"user":user, "request":request})
        self.assertNotIn(href, html)

    def test_create_fields_preserve_constraints_and_access(self):
        hr = self.user("HR_MANAGER", True)
        self.client.force_login(hr)
        for route, expected in [
            ("recruitment_create", {"request_code", "department", "position", "required_quantity", "required_date", "request_reason"}),
            ("hr_candidate_create", {"candidate_code", "full_name", "phone_number", "email", "current_address", "source"})]:
            response = self.client.get(reverse("portal:"+route))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'class="ui-page ui-recruitment"')
            form = next(f for f in Forms(response.content.decode()).forms if "data-ui-form" in f["attrs"])
            fields = {x["name"]: x for x in form["fields"]}
            self.assertEqual(set(fields), expected | {"csrfmiddlewaretoken"})
            self.assertIn('data-ui-errors', response.content.decode())
            for name in expected:
                self.assertContains(response, 'for="'+fields[name]["id"]+'"')
            if route == "recruitment_create":
                self.assertEqual(fields["required_quantity"]["min"], "1")
                self.assertEqual(fields["required_quantity"]["value"], "1")
                self.assertNotIn("required", fields["request_reason"])
            else:
                self.assertNotIn("required", fields["source"])
                self.assertEqual(fields["email"]["type"], "email")
        employee = self.user("EMPLOYEE", True)
        self.client.force_login(employee)
        self.assertEqual(self.client.get(reverse("portal:hr_candidate_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("portal:hr_candidate_create")).status_code, 302)

    def test_approval_values_and_pending_guard(self):
        hr = self.user("HR_MANAGER", True)
        req = RecruitmentRequest.objects.create(request_code="UI-FAKE", department=self.department,
            position=self.position, required_quantity=3, required_date=date(2026,12,1))
        self.client.force_login(hr)
        response = self.client.get(reverse("portal:recruitment_list"))
        action = reverse("portal:recruitment_approve", args=[req.pk])
        forms = [f for f in Forms(response.content.decode()).forms if f["attrs"].get("action")==action]
        self.assertEqual(len(forms), 2)
        self.assertEqual([next(x["value"] for x in f["fields"] if x.get("name")=="decision") for f in forms], ["Approved", "Rejected"])
        self.assertTrue(all("data-ui-confirm" in f["attrs"] for f in forms))
        self.assertContains(response, 'id="ui-confirm-dialog"', count=1)
        req.status="Approved"; req.save(update_fields=["status"])
        self.assertNotContains(self.client.get(reverse("portal:recruitment_list")), 'action="'+action+'"')

    def test_candidate_detail_conditional_actions_and_keyboard_link(self):
        hr = self.user("HR_MANAGER", True)
        interview = Interview.objects.create(candidate=self.candidate, interviewer=hr.employee,
            interview_date=timezone.now(), interview_type="Trực tiếp")
        offer = Offer.objects.create(candidate=self.candidate, offer_date=date(2026,10,1),
            expected_join_date=date(2026,12,1), salary_offer="12345678")
        self.client.force_login(hr)
        detail = reverse("portal:hr_candidate_detail", args=[self.candidate.pk])
        listing = self.client.get(reverse("portal:hr_candidate_list"))
        self.assertContains(listing, 'href="'+detail+'"')
        self.assertNotContains(listing, 'onclick=')
        response = self.client.get(detail)
        self.assertContains(response, "12.345.678 đ")
        self.assertContains(response, "Chưa có kết quả")
        for route, pk in [("hr_interview_result",interview.pk), ("hr_offer_update_status",offer.pk)]:
            self.assertContains(response, 'action="'+reverse("portal:"+route,args=[pk])+'"')
        interview.result="Pass"; interview.save(update_fields=["result"])
        offer.status="Accepted"; offer.save(update_fields=["status"])
        self.candidate.status="Hired"; self.candidate.save(update_fields=["status"])
        response = self.client.get(detail)
        for route, pk in [("hr_interview_result",interview.pk), ("hr_offer_update_status",offer.pk), ("hr_candidate_onboard",self.candidate.pk)]:
            self.assertNotContains(response, 'action="'+reverse("portal:"+route,args=[pk])+'"')
