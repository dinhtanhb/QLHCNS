from datetime import date, timedelta
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.activity.models import Activity, ActivityProposal
from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
from apps.activity.services import (
    add_company_workdays,
    find_schedule_conflicts,
    send_activity_report_reminders,
    send_activity_proposal_for_approval,
)
from apps.attendance.models import Holiday
from apps.hrm.models import Employee
from apps.notification.models import Notification
from apps.document.models import DispatchBook, OfficialDispatch
from apps.organization.models import Department, Organization, Position
from apps.project.models import Project
from apps.security.models import Role, User
from apps.task.models import Task
from unittest.mock import patch


class ActivityTestDataMixin:
    def setUp(self):
        self.organization = Organization.objects.create(
            organization_code="ORG-ACT", organization_name="Tổ chức kiểm thử"
        )
        self.department = Department.objects.create(
            department_code="DEP-ACT", department_name="Chương trình",
            organization=self.organization,
        )
        self.position = Position.objects.create(
            position_code="POS-ACT", position_name="Cán bộ dự án"
        )
        self.cbda = self.make_employee("A")
        self.coordinator = self.make_employee("COORD")
        self.project = Project.objects.create(
            project_code="PRJ-ACT", project_name="Dự án thử", department=self.department
        )
        self.dispatch_book = DispatchBook.objects.create(
            book_code="BOOK-ACT-2026", book_name="Sổ công văn đi 2026",
            book_type="Outgoing", year=2026,
        )
        self.dispatch = OfficialDispatch.objects.create(
            dispatch_type="Outgoing", dispatch_book=self.dispatch_book,
            dispatch_no="CV-ACT-001", title="Kế hoạch hoạt động",
            issuing_organization="IHRMS", issue_date=date(2026, 9, 25),
            received_or_sent_date=date(2026, 9, 25), signer=self.coordinator,
        )

    def make_employee(self, suffix):
        return Employee.objects.create(
            employee_code=f"EMP-ACT-{suffix}", first_name=suffix, last_name="Test",
            full_name=f"{suffix} Test", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=f"TESTID{suffix}", company_email=f"{suffix.lower()}@example.test",
            mobile_phone="0000000000", join_date=date(2020, 1, 1),
            department=self.department, position=self.position,
        )

    def make_activity(self, code="ACT-001", dispatch=None, lead=None):
        return Activity.objects.create(
            activity_code=code, activity_name=f"Hoạt động {code}", project=self.project,
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 1),
            lead_cbda=lead or self.cbda, coordinator=self.coordinator,
            outgoing_document=dispatch,
        )


class ActivityWorkflowTests(ActivityTestDataMixin, TestCase):
    def test_overlapping_cbda_schedule_is_detected_but_can_be_reviewed(self):
        first = self.make_activity("ACT-OVERLAP-1")
        second = self.make_activity("ACT-OVERLAP-2")

        second.full_clean()
        conflicts = find_schedule_conflicts(
            self.cbda.pk, second.start_date, second.end_date, exclude_activity_id=second.pk
        )

        self.assertEqual([activity.pk for activity in conflicts], [first.pk])

    def test_report_deadline_counts_company_workdays_and_holidays(self):
        Holiday.objects.create(
            holiday_code="HOL-ACT-01", holiday_name="Ngày nghỉ thử",
            holiday_date=date(2026, 10, 2),
        )

        # 25/09/2026 is Friday. 10 workdays after it, skipping weekends and
        # the configured holiday, lands on Monday 12/10/2026.
        self.assertEqual(
            add_company_workdays(date(2026, 9, 25), 10),
            date(2026, 10, 12),
        )

    def test_linking_issued_dispatch_creates_one_assigned_report_task(self):
        activity = self.make_activity(dispatch=self.dispatch)

        task = Task.objects.get(activity=activity)
        self.assertEqual(task.assigned_to_employee, self.cbda)
        self.assertEqual(task.assigned_by_employee, self.coordinator)
        self.assertEqual(task.due_date, date(2026, 10, 9))
        self.assertEqual(task.status, "Todo")
        self.assertEqual(Notification.objects.filter(employee=self.cbda).count(), 1)


        activity.purpose = "Cập nhật thông tin"
        activity.save()
        self.assertEqual(Task.objects.filter(activity=activity).count(), 1)
        self.assertEqual(Notification.objects.filter(employee=self.cbda).count(), 1)

    def test_linking_dispatch_after_activity_creation_creates_task(self):
        activity = self.make_activity()
        self.assertFalse(Task.objects.filter(activity=activity).exists())

        activity.outgoing_document = self.dispatch
        activity.save()

        self.assertTrue(Task.objects.filter(activity=activity).exists())

    def test_activity_task_cannot_be_completed_without_report_file(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        task.status = "Done"

        with self.assertRaises(ValidationError):
            task.full_clean()

        task.report_file = SimpleUploadedFile("bao-cao.pdf", b"test report", content_type="application/pdf")
        task.full_clean()

    def test_linked_dispatch_requires_task_assigner(self):
        activity = self.make_activity(dispatch=self.dispatch)
        activity.coordinator = None
        self.dispatch.signer = None

        with self.assertRaises(ValidationError):
            activity.full_clean()

    def test_reminders_are_sent_once_per_workday_and_skipped_on_weekends(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        task.due_date = date(2026, 9, 30)
        task.save()

        today = date.today()
        task.due_date = add_company_workdays(today, 1)
        task.save()

        first_run = send_activity_report_reminders(today=today)
        repeated_run = send_activity_report_reminders(today=today)
        weekend = today + timedelta(days=(5 - today.weekday()) % 7)
        weekend_run = send_activity_report_reminders(today=weekend)

        self.assertEqual(first_run, 1)
        self.assertEqual(repeated_run, 0)
        self.assertEqual(weekend_run, 0)
        self.assertEqual(
            Notification.objects.filter(
                employee=self.cbda, notification_type="ActivityReportReminder"
            ).count(),
            1,
        )




class ActivityProposalWorkflowTests(ActivityTestDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.storage_settings = override_settings(
            M365_STORAGE_ENABLED=False, MEDIA_ROOT=self.media.name,
            M365_FOLDER_MAP={"activity_proposals": ""}, M365_UPLOAD_PREFIX_MAP={},
        )
        self.storage_settings.enable()
        self.addCleanup(self.storage_settings.disable)
        director_role, _ = Role.objects.get_or_create(
            role_code="DIRECTOR", defaults={"role_name": "Giám đốc"}
        )
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối viên"}
        )
        self.director_employee = self.make_employee("DIRECTOR")
        self.director = User.objects.create_user(
            username="activity-director", email=self.director_employee.company_email,
            role=director_role, employee=self.director_employee,
        )
        self.coordinator_user = User.objects.create_user(
            username="activity-coordinator", email=self.coordinator.company_email,
            role=coordinator_role, employee=self.coordinator,
        )
        cbda_role, _ = Role.objects.get_or_create(
            role_code="CBDA", defaults={"role_name": "Cán bộ dự án"}
        )
        self.cbda_user = User.objects.create_user(
            username="activity-cbda", email=self.cbda.company_email,
            role=cbda_role, employee=self.cbda,
        )
        self.activity = self.make_activity("ACT-PROPOSAL-1")

    def make_package(self):
        return ActivityProposal.objects.create(
            activity=self.activity,
            proposal_excel=SimpleUploadedFile("proposal.xlsx", b"XLSX"),
            proposal_pdf=SimpleUploadedFile("proposal.pdf", b"PROPOSAL PDF"),
            budget_excel=SimpleUploadedFile("budget.xlsx", b"XLSX"),
            budget_pdf=SimpleUploadedFile("budget.pdf", b"BUDGET PDF"),
        )

    def test_package_requires_all_four_template_exports_before_submission(self):
        package = ActivityProposal.objects.create(activity=self.activity)
        self.assertFalse(package.has_required_files())
        package.proposal_excel = SimpleUploadedFile("proposal.xlsx", b"XLSX")
        package.proposal_pdf = SimpleUploadedFile("proposal.pdf", b"PDF")
        package.budget_excel = SimpleUploadedFile("budget.xlsx", b"XLSX")
        package.budget_pdf = SimpleUploadedFile("budget.pdf", b"PDF")
        package.save()
        self.assertTrue(package.has_required_files())

    @patch("apps.m365.graph_client.get_graph_client")
    @override_settings(M365_MAIL_SENDER="ihrms@example.test")
    def test_approval_email_attaches_the_two_pdf_files(self, get_client):
        package = self.make_package()
        recipient = send_activity_proposal_for_approval(package, self.director, self.coordinator_user)

        self.assertEqual(recipient, self.director_employee.company_email)
        get_client.return_value.send_mail.assert_called_once()
        args = get_client.return_value.send_mail.call_args.args
        self.assertEqual(args[0:2], ("ihrms@example.test", self.director_employee.company_email))
        self.assertEqual([item["name"].split("-")[0] for item in args[4]], ["proposal", "budget"])
        self.assertTrue(all(item["content_type"] == "application/pdf" for item in args[4]))

    @patch("apps.m365.graph_client.get_graph_client")
    @override_settings(M365_MAIL_SENDER="")
    def test_missing_mailbox_configuration_fails_without_sending(self, get_client):
        package = self.make_package()
        with self.assertRaisesMessage(Exception, "Thiếu M365_MAIL_SENDER"):
            send_activity_proposal_for_approval(package, self.director, self.coordinator)
        get_client.assert_not_called()

    def test_cbda_can_upload_files_for_own_activity(self):
        self.client.force_login(self.cbda_user)
        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {
                "action": "upload",
                "proposal_excel": SimpleUploadedFile("proposal.xlsx", b"XLSX"),
                "proposal_pdf": SimpleUploadedFile("proposal.pdf", b"PDF"),
                "budget_excel": SimpleUploadedFile("budget.xlsx", b"XLSX"),
                "budget_pdf": SimpleUploadedFile("budget.pdf", b"PDF"),
            },
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        package = ActivityProposal.objects.get(activity=self.activity)
        self.assertTrue(package.has_required_files())
        self.assertEqual(package.created_by, self.cbda_user)

    @patch("apps.activity.views.send_activity_proposal_for_approval", return_value="director@example.test")
    def test_coordinator_sends_to_selected_director_and_director_records_decision(self, send_mail):
        package = self.make_package()
        self.client.force_login(self.coordinator_user)
        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {"action": "send", "approver": self.director.pk},
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        send_mail.assert_called_once()
        package.refresh_from_db()
        self.assertEqual(package.status, "Submitted")
        self.assertEqual(package.approver, self.director)
        self.assertEqual(package.sent_to, "director@example.test")

        self.client.force_login(self.director)
        response = self.client.post(
            reverse("portal:activity_proposal_decide", args=(package.pk,)),
            {"decision": "ChangesRequested", "comment": "Vui lòng cập nhật mục tiêu."},
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        package.refresh_from_db()
        self.assertEqual(package.status, "ChangesRequested")
        self.assertEqual(package.decision_by, self.director)

class ActivityDashboardPermissionTests(ActivityTestDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.other_cbda = self.make_employee("B")
        self.own_activity = self.make_activity("ACT-OWN")
        self.other_activity = self.make_activity("ACT-OTHER", lead=self.other_cbda)
        self.cbda_role, _ = Role.objects.get_or_create(
            role_code="CBDA", defaults={"role_name": "Cán bộ dự án"}
        )

    def create_user(self, username, employee, role):
        user = User.objects.create_user(username=username, password="test-password")
        user.employee = employee
        user.role = role
        user.save(update_fields=["employee", "role"])
        return user

    def test_cbda_sees_only_own_project_activities(self):
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.login(username="cbda_a", password="test-password")

        response = self.client.get(reverse("portal:activity_dashboard"), {"month": "2026-10"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_activity.activity_code)
        self.assertNotContains(response, self.other_activity.activity_code)

    def test_cbda_filter_limits_activity_dashboard_rows(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator_filter", self.coordinator, coordinator_role)
        self.client.login(username="coordinator_filter", password="test-password")

        response = self.client.get(reverse("portal:activity_dashboard"), {
            "month": "2026-10", "cbda": str(self.cbda.pk),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_activity.activity_code)
        self.assertNotContains(response, self.other_activity.activity_code)
        self.assertEqual(response.context["selected_cbda"], str(self.cbda.pk))

    def test_cbda_calendar_shows_assigned_activities_for_selected_month(self):
        self.own_activity.outgoing_document = self.dispatch
        self.own_activity.save()
        self.create_user("cbda_calendar", self.cbda, self.cbda_role)
        self.client.login(username="cbda_calendar", password="test-password")

        response = self.client.get(reverse("portal:activity_calendar"), {"month": "2026-10"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lịch hoạt động tháng 10/2026")
        self.assertContains(response, self.own_activity.activity_code)
        self.assertContains(response, "Hạn báo cáo")
        self.assertNotContains(response, self.other_activity.activity_code)

    def test_director_shared_dashboard_includes_monthly_project_activity_metrics(self):
        today = date.today()
        self.own_activity.start_date = today
        self.own_activity.end_date = today
        self.own_activity.save()
        self.other_activity.start_date = today
        self.other_activity.end_date = today
        self.other_activity.save()
        director_role, _ = Role.objects.get_or_create(
            role_code="DIRECTOR", defaults={"role_name": "Giám đốc"}
        )
        self.create_user("director_home", self.coordinator, director_role)
        self.client.login(username="director_home", password="test-password")

        response = self.client.get(reverse("portal:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_project_activity_summary"])
        self.assertEqual(response.context["activity_total"], 2)
        self.assertContains(response, "Tiến độ hoạt động dự án")
        self.assertContains(response, "Mở Dashboard hoạt động")

    def test_department_manager_sees_only_activities_in_managed_departments(self):
        today = date.today()
        self.own_activity.start_date = today
        self.own_activity.end_date = today
        self.own_activity.save()
        other_department = Department.objects.create(
            department_code="DEP-ACT-OTHER",
            department_name="Phòng khác",
            organization=self.organization,
        )
        other_project = Project.objects.create(
            project_code="PRJ-ACT-OTHER",
            project_name="Dự án phòng khác",
            department=other_department,
        )
        other_department_activity = Activity.objects.create(
            activity_code="ACT-OTHER-DEPT",
            activity_name="Hoạt động phòng khác",
            project=other_project,
            start_date=today,
            end_date=today,
            lead_cbda=self.other_cbda,
        )
        self.department.manager = self.coordinator
        self.department.save(update_fields=["manager"])
        manager_role, _ = Role.objects.get_or_create(
            role_code="DEPT_MANAGER", defaults={"role_name": "Trưởng phòng"}
        )
        self.create_user("department_manager_home", self.coordinator, manager_role)
        self.client.login(username="department_manager_home", password="test-password")

        home_response = self.client.get(reverse("portal:dashboard"))
        activity_response = self.client.get(reverse("portal:activity_dashboard"))

        self.assertEqual(home_response.status_code, 200)
        self.assertEqual(home_response.context["activity_total"], 1)
        self.assertTrue(home_response.context["show_project_activity_summary"])
        self.assertEqual(activity_response.status_code, 200)
        self.assertContains(activity_response, self.own_activity.activity_code)
        self.assertNotContains(activity_response, other_department_activity.activity_code)

    def test_coordinator_can_open_create_activity_form(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator", self.coordinator, coordinator_role)
        self.client.login(username="coordinator", password="test-password")

        response = self.client.get(reverse("portal:activity_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tạo hoạt động dự án")

    def test_coordinator_creates_activity_linked_to_official_dispatch(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator", self.coordinator, coordinator_role)
        self.client.login(username="coordinator", password="test-password")

        response = self.client.post(reverse("portal:activity_create"), {
            "activity_code": "46.9.1.1.2.1",
            "activity_name": "Tập huấn tại điểm A",
            "project": self.project.pk,
            "location": "Điểm A",
            "participants": "Nhóm cộng đồng",
            "purpose": "Tập huấn thử nghiệm",
            "expected_output": "Một buổi tập huấn",
            "start_date": "2026-10-01",
            "end_date": "2026-10-01",
            "lead_cbda": self.cbda.pk,
            "coordinator": self.coordinator.pk,
            "outgoing_document": self.dispatch.pk,
            "status": "DispatchIssued",
        })

        self.assertRedirects(response, reverse("portal:activity_dashboard"))
        activity = Activity.objects.get(activity_code="46.9.1.1.2.1")
        self.assertEqual(activity.activity_name, ACTIVITY_CODE_NAMES[activity.activity_code])
        task = Task.objects.get(activity=activity)
        self.assertEqual(activity.outgoing_document, self.dispatch)
        self.assertEqual(task.assigned_to_employee, self.cbda)
        self.assertEqual(task.due_date, date(2026, 10, 9))

    def test_activity_form_warns_about_overlap_but_keeps_the_activity(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator_overlap", self.coordinator, coordinator_role)
        self.client.login(username="coordinator_overlap", password="test-password")

        response = self.client.post(reverse("portal:activity_create"), {
            "activity_code": "46.9.1.1.2.2",
            "activity_name": "Hoạt động bị trùng lịch",
            "project": self.project.pk,
            "start_date": "2026-10-01",
            "end_date": "2026-10-01",
            "lead_cbda": self.cbda.pk,
            "coordinator": self.coordinator.pk,
            "status": "Planned",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Activity.objects.filter(activity_code="46.9.1.1.2.2").exists())
        self.assertContains(response, "Lịch CBDA bị trùng")

    def test_cbda_cannot_create_activity(self):
        self.create_user("cbda_create", self.cbda, self.cbda_role)
        self.client.login(username="cbda_create", password="test-password")

        response = self.client.get(reverse("portal:activity_create"))

        self.assertEqual(response.status_code, 403)

    def test_cbda_cannot_open_another_employees_activity_task(self):
        task = Task.objects.create(
            task_code="TASK-ACT-OTHER", task_name="Báo cáo riêng",
            assigned_by_employee=self.coordinator, assigned_to_employee=self.other_cbda,
            start_date=date(2026, 9, 25), due_date=date(2026, 10, 9),
            activity=self.other_activity,
        )
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.login(username="cbda_a", password="test-password")

        response = self.client.get(reverse("portal:task_detail", args=[task.pk]))

        self.assertEqual(response.status_code, 302)

    def test_task_requires_report_before_completion_and_accepts_report_upload(self):
        activity = self.make_activity("ACT-REPORT", dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.login(username="cbda_a", password="test-password")

        response = self.client.post(
            reverse("portal:task_detail", args=[task.pk]),
            {"action": "update_status", "status": "Done"},
        )
        task.refresh_from_db()
        self.assertEqual(task.status, "Todo")

        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root, M365_STORAGE_ENABLED=False
        ):
            response = self.client.post(
                reverse("portal:task_detail", args=[task.pk]),
                {
                    "action": "upload_activity_report",
                    "report_file": SimpleUploadedFile(
                        "bao-cao.pdf", b"test report", content_type="application/pdf"
                    ),
                },
            )
            task.refresh_from_db()
            self.assertTrue(task.report_file)

        self.client.post(
            reverse("portal:task_detail", args=[task.pk]),
            {"action": "update_status", "status": "Done"},
        )
        task.refresh_from_db()
        self.assertEqual(task.status, "Done")
