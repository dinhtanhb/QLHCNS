from datetime import date, datetime, timedelta
import tempfile
from urllib.parse import parse_qs, urlsplit

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.activity.models import Activity, ActivityProposal
from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
from apps.activity.services import (
    add_company_workdays,
    build_activity_proposal_email_draft,
    find_schedule_conflicts,
    send_activity_report_reminders,
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
        activity = self.make_activity()
        activity.end_date = date(2026, 10, 31)
        activity.outgoing_document = self.dispatch
        activity.save()

        task = Task.objects.get(activity=activity)
        self.assertEqual(task.assigned_to_employee, self.cbda)
        self.assertEqual(task.assigned_by_employee, self.coordinator)
        self.assertEqual(task.start_date, date(2026, 10, 1))
        self.assertEqual(task.due_date, date(2026, 11, 13))
        self.assertEqual(task.status, "Todo")
        self.assertEqual(Notification.objects.filter(employee=self.cbda).count(), 1)


        activity.purpose = "Cập nhật thông tin"
        activity.save()
        self.assertEqual(Task.objects.filter(activity=activity).count(), 1)
        self.assertEqual(Notification.objects.filter(employee=self.cbda).count(), 1)

    def test_report_task_schedule_uses_activity_dates_not_dispatch_issue_date(self):
        self.dispatch.issue_date = date(2026, 6, 18)
        self.dispatch.save(update_fields=("issue_date",))
        activity = self.make_activity()
        activity.start_date = date(2026, 9, 19)
        activity.end_date = date(2026, 9, 20)
        activity.outgoing_document = self.dispatch

        activity.save()

        task = Task.objects.get(activity=activity)
        self.assertEqual(task.start_date, date(2026, 9, 19))
        # Ten Monday-Friday workdays after the Sunday end date; 20/09 is day zero.
        self.assertEqual(task.due_date, date(2026, 10, 2))

    def test_rescheduling_activity_updates_task_dates_and_reopens_early_completion(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        task.status = "Done"
        task.completed_date = date(2026, 9, 26)
        task.report_file = "activity_reports/old-report.pdf"
        task.save()

        activity.end_date = date(2026, 10, 31)
        activity.save()

        task.refresh_from_db()
        self.assertEqual(Task.objects.filter(activity=activity).count(), 1)
        self.assertEqual(task.start_date, date(2026, 10, 1))
        self.assertEqual(task.due_date, date(2026, 11, 13))
        self.assertEqual(task.status, "Todo")
        self.assertIsNone(task.completed_date)
        self.assertFalse(task.report_file)
        self.assertEqual(
            Notification.objects.filter(
                employee=self.cbda, notification_type="ActivityTaskScheduleChanged"
            ).count(),
            1,
        )

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

        with patch("apps.task.models.timezone.localdate", return_value=date(2026, 10, 2)):
            with self.assertRaises(ValidationError):
                task.full_clean()

        task.report_file = SimpleUploadedFile("bao-cao.pdf", b"test report", content_type="application/pdf")
        with patch("apps.task.models.timezone.localdate", return_value=date(2026, 10, 2)):
            task.full_clean()

    def test_activity_report_task_cannot_be_completed_before_activity_ends(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        task.status = "Done"
        task.completed_date = date(2026, 9, 30)
        task.report_file = SimpleUploadedFile("report.pdf", b"test report", content_type="application/pdf")

        with patch("apps.task.models.timezone.localdate", return_value=date(2026, 9, 30)):
            with self.assertRaises(ValidationError) as raised:
                task.full_clean()

        self.assertIn("status", raised.exception.message_dict)

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

        # Mốc cố định (thứ Hai) thay vì date.today(): bản cũ dùng ngày chạy
        # thật nên tự fail vào cuối tuần (thứ Bảy/Chủ nhật) vì
        # is_company_workday() luôn trả False cho ngày đó — không liên quan
        # gì đến logic đang kiểm thử.
        #
        # send_activity_report_reminders() chống gửi trùng bằng cách so
        # created_date__date=today, nhưng created_date của Notification luôn
        # lấy giờ hệ thống thật (auto_now_add), không phải tham số `today`.
        # Ngoài production hai giá trị này luôn khớp (lệnh chạy hằng ngày
        # không truyền `today`); trong test phải "đóng băng" đồng hồ hệ
        # thống về đúng mốc cố định thì mới tái hiện đúng hành vi thật —
        # nếu không, first_run/repeated_run sẽ tự lệch bất kể ngày nào chạy.
        today = date(2026, 10, 5)
        frozen_now = timezone.make_aware(datetime(2026, 10, 5, 9, 0, 0))
        task.due_date = add_company_workdays(today, 1)
        task.save()

        with patch("django.utils.timezone.now", return_value=frozen_now):
            first_run = send_activity_report_reminders(today=today)
            repeated_run = send_activity_report_reminders(today=today)

        weekend = today + timedelta(days=(5 - today.weekday()) % 7)
        weekend_now = timezone.make_aware(datetime(weekend.year, weekend.month, weekend.day, 9, 0, 0))
        with patch("django.utils.timezone.now", return_value=weekend_now):
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
            created_by=self.cbda_user,
            proposal_pdf=SimpleUploadedFile("proposal.pdf", b"PROPOSAL PDF"),
            budget_pdf=SimpleUploadedFile("budget.pdf", b"BUDGET PDF"),
        )

    def test_package_requires_only_the_two_pdf_exports_before_submission(self):
        package = ActivityProposal.objects.create(activity=self.activity)
        self.assertFalse(package.has_required_files())
        package.proposal_pdf = SimpleUploadedFile("proposal.pdf", b"PDF")
        package.budget_pdf = SimpleUploadedFile("budget.pdf", b"PDF")
        package.save()
        self.assertTrue(package.has_required_files())

    def test_coordinator_sees_send_action_with_only_two_pdf_files(self):
        self.make_package()
        self.client.force_login(self.coordinator_user)

        response = self.client.get(reverse("portal:activity_proposal", args=(self.activity.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Soạn thư trong Outlook")
        self.assertContains(response, 'name="proposal_pdf"')
        self.assertContains(response, 'name="budget_pdf"')
        self.assertNotContains(response, 'name="proposal_excel"')
        self.assertNotContains(response, 'name="budget_excel"')

    def test_outlook_draft_prefills_recipient_subject_body_and_sender_hint(self):
        package = self.make_package()
        draft = build_activity_proposal_email_draft(
            package, self.director, self.coordinator_user, "https://ihrms.example.test/proposal/"
        )

        parsed = urlsplit(draft["mailto_url"])
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.scheme, "mailto")
        self.assertEqual(parsed.path, self.director_employee.company_email)
        self.assertEqual(draft["recipient"], self.director_employee.company_email)
        self.assertEqual(draft["sender_email"], self.coordinator.company_email)
        self.assertEqual(params["subject"][0], draft["subject"])
        self.assertIn("https://ihrms.example.test/proposal/", params["body"][0])

    def test_pdf_attachment_link_can_download_file_for_outlook(self):
        package = self.make_package()
        self.client.force_login(self.coordinator_user)

        response = self.client.get(
            reverse("portal:activity_proposal_file", args=(package.pk, "proposal_pdf")),
            {"download": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        response.close()

    def test_cbda_can_upload_files_for_own_activity(self):
        self.client.force_login(self.cbda_user)
        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {
                "action": "upload",
                "proposal_pdf": SimpleUploadedFile("proposal.pdf", b"PDF"),
                "budget_pdf": SimpleUploadedFile("budget.pdf", b"PDF"),
            },
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        package = ActivityProposal.objects.get(activity=self.activity)
        self.assertTrue(package.has_required_files())
        self.assertEqual(package.created_by, self.cbda_user)

    def test_invalid_upload_rerenders_without_reversing_unsaved_package_file_links(self):
        self.client.force_login(self.cbda_user)
        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {
                "action": "upload",
                "proposal_pdf": SimpleUploadedFile("proposal.txt", b"not a PDF"),
                "budget_pdf": SimpleUploadedFile("budget.pdf", b"PDF"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tệp không đúng định dạng")
        self.assertIsNone(response.context["package"])
        self.assertFalse(ActivityProposal.objects.filter(activity=self.activity).exists())

    def test_coordinator_prepares_outlook_draft_and_confirms_sent_before_director_decides(self):
        package = self.make_package()
        self.client.force_login(self.coordinator_user)
        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {"action": "prepare_email", "approver": self.director.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "activity/proposal_email_draft.html")
        self.assertContains(response, "mailto:director@example.test")
        self.assertContains(response, "Tôi xác nhận đã tự bấm Gửi trong Outlook.")
        self.assertEqual(len(response.context["pdf_files"]), 2)
        self.assertIn("proposal_pdf/", response.context["pdf_files"][0]["url"])
        self.assertIn("budget_pdf/", response.context["pdf_files"][1]["url"])
        package.refresh_from_db()
        self.assertEqual(package.status, "Draft")

        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {"action": "confirm_sent", "approver": self.director.pk},
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        package.refresh_from_db()
        self.assertEqual(package.status, "Draft")

        response = self.client.post(
            reverse("portal:activity_proposal", args=(self.activity.pk,)),
            {"action": "confirm_sent", "approver": self.director.pk, "confirm_sent": "yes"},
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        package.refresh_from_db()
        self.assertEqual(package.status, "Submitted")
        self.assertEqual(package.approver, self.director)
        self.assertEqual(package.sent_to, self.director_employee.company_email)
        director_notice = Notification.objects.get(
            employee=self.director_employee, notification_type="ActivityProposalSubmitted"
        )
        self.assertIn("ACT-PROPOSAL-1", director_notice.message)
        self.assertEqual(director_notice.link, reverse("portal:activity_proposal", args=(self.activity.pk,)))

        self.client.force_login(self.director)
        inbox = self.client.get(reverse("portal:activity_proposal_approval_list"))
        self.assertEqual(inbox.status_code, 200)
        self.assertContains(inbox, "ACT-PROPOSAL-1")
        self.assertContains(inbox, "Xem và xử lý")
        response = self.client.post(
            reverse("portal:activity_proposal_decide", args=(package.pk,)),
            {"decision": "ChangesRequested", "comment": "Vui lòng cập nhật mục tiêu."},
        )
        self.assertRedirects(response, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        package.refresh_from_db()
        self.assertEqual(package.status, "ChangesRequested")
        self.assertEqual(package.decision_by, self.director)
        requester_notice = Notification.objects.get(
            employee=self.coordinator, notification_type="ActivityProposalChangesRequested"
        )
        self.assertIn("Vui lòng cập nhật mục tiêu.", requester_notice.message)
        self.assertEqual(requester_notice.link, reverse("portal:activity_proposal", args=(self.activity.pk,)))
        cbda_notice = Notification.objects.get(
            employee=self.cbda, notification_type="ActivityProposalChangesRequested"
        )
        self.assertIn("Vui lòng cập nhật mục tiêu.", cbda_notice.message)
        dashboard = self.client.get(reverse("portal:activity_dashboard"), {"month": "2026-10"})
        self.assertContains(dashboard, "Yêu cầu chỉnh sửa")
        self.assertContains(dashboard, "Vui lòng cập nhật mục tiêu.")

    def test_only_director_can_open_proposal_approval_inbox(self):
        self.client.force_login(self.cbda_user)
        response = self.client.get(reverse("portal:activity_proposal_approval_list"))
        self.assertEqual(response.status_code, 403)

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
        self.client.post("/portal/login/", {"username": "cbda_a", "password": "test-password"})

        response = self.client.get(reverse("portal:activity_dashboard"), {"month": "2026-10"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_activity.activity_code)
        self.assertNotContains(response, self.other_activity.activity_code)

    def test_project_coordinator_can_see_report_task_assigned_to_cbda(self):
        activity = self.make_activity("ACT-TASK-COORD", dispatch=self.dispatch)
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator_task_list", self.coordinator, coordinator_role)
        self.client.post("/portal/login/", {"username": "coordinator_task_list", "password": "test-password"})

        response = self.client.get(reverse("portal:task_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Giao việc &amp; hoàn tất")
        self.assertContains(response, activity.activity_code)
        self.assertContains(response, self.cbda.full_name)
        self.assertEqual(list(response.context["tasks"]), [Task.objects.get(activity=activity)])

    def test_cbda_task_list_shows_only_activities_in_own_scope(self):
        own_activity = self.make_activity("ACT-TASK-OWN", dispatch=self.dispatch)
        other_activity = self.make_activity("ACT-TASK-OTHER", dispatch=self.dispatch, lead=self.other_cbda)
        self.create_user("cbda_task_list", self.cbda, self.cbda_role)
        self.client.post("/portal/login/", {"username": "cbda_task_list", "password": "test-password"})

        response = self.client.get(reverse("portal:task_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_activity.activity_code)
        self.assertNotContains(response, other_activity.activity_code)

    def test_cbda_filter_limits_activity_dashboard_rows(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator_filter", self.coordinator, coordinator_role)
        self.client.post("/portal/login/", {"username": "coordinator_filter", "password": "test-password"})

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
        self.client.post("/portal/login/", {"username": "cbda_calendar", "password": "test-password"})

        response = self.client.get(reverse("portal:activity_calendar"), {"month": "2026-10"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lịch hoạt động tháng 10/2026")
        self.assertContains(response, self.own_activity.activity_code)
        self.assertContains(response, "Hạn báo cáo")
        self.assertNotContains(response, "min-w-[980px]")
        self.assertContains(response, "overflow-hidden rounded-xl")
        self.assertContains(response, 'id="menu-hoatdongduan"')
        self.assertContains(response, "Theo dõi hoạt động")
        self.assertContains(response, "Lịch hoạt động</a>")
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
        self.client.post("/portal/login/", {"username": "director_home", "password": "test-password"})

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
        # Both fixtures are in the managed department. Keep the second outside
        # the tested month so this assertion is independent of the real date.
        other_month = date(today.year + 1, today.month, 1)
        self.other_activity.start_date = other_month
        self.other_activity.end_date = other_month
        self.other_activity.save()
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
        self.client.post("/portal/login/", {"username": "department_manager_home", "password": "test-password"})

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
        self.client.post("/portal/login/", {"username": "coordinator", "password": "test-password"})

        response = self.client.get(reverse("portal:activity_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tạo hoạt động dự án")

    def test_coordinator_creates_activity_linked_to_official_dispatch(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator", self.coordinator, coordinator_role)
        self.client.post("/portal/login/", {"username": "coordinator", "password": "test-password"})

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
        self.assertEqual(task.start_date, date(2026, 10, 1))
        self.assertEqual(task.due_date, date(2026, 10, 15))

    def test_activity_form_warns_about_overlap_but_keeps_the_activity(self):
        coordinator_role, _ = Role.objects.get_or_create(
            role_code="PROJECT_COORDINATOR", defaults={"role_name": "Điều phối dự án"}
        )
        self.create_user("coordinator_overlap", self.coordinator, coordinator_role)
        self.client.post("/portal/login/", {"username": "coordinator_overlap", "password": "test-password"})

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
        self.client.post("/portal/login/", {"username": "cbda_create", "password": "test-password"})

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
        self.client.post("/portal/login/", {"username": "cbda_a", "password": "test-password"})

        response = self.client.get(reverse("portal:task_detail", args=[task.pk]))

        self.assertEqual(response.status_code, 302)

    def test_task_requires_report_before_completion_and_accepts_report_upload(self):
        activity = self.make_activity("ACT-REPORT", dispatch=self.dispatch)
        task = Task.objects.get(activity=activity)
        self.create_user("cbda_a", self.cbda, self.cbda_role)
        self.client.post("/portal/login/", {"username": "cbda_a", "password": "test-password"})

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

        with patch("apps.portal.views.tasks_kpi.timezone.localdate", return_value=date(2026, 10, 2)):
            self.client.post(
                reverse("portal:task_detail", args=[task.pk]),
                {"action": "update_status", "status": "Done"},
            )
        task.refresh_from_db()
        self.assertEqual(task.status, "Done")

