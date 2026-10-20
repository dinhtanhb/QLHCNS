from django.test import TestCase

# Create your tests here.
from datetime import date
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase
from django.urls import reverse

from apps.hrm.models import Employee
from apps.leave.models import LeaveRequest, LeaveType
from apps.document.models import DispatchBook, Document, DocumentCategory, OfficialDispatch
from apps.notification.models import Notification, NotificationEmailOutbox
from apps.notification.services import notify_with_email_draft
from apps.organization.models import Department, Organization, Position
from apps.portal import test_home_dashboard as fixtures
from apps.security.models import Role, User
from apps.payroll.models import PayrollPeriod, Payroll


class NotificationEmailOutboxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(
            organization_code="NOTIF-ORG", organization_name="Tổ chức kiểm thử thông báo"
        )
        cls.department = Department.objects.create(
            department_code="NOTIF-DEPT", department_name="Phòng kiểm thử", organization=organization
        )
        cls.position = Position.objects.create(position_code="NOTIF-STAFF", position_name="Nhân viên")

    def make_employee(self, code, email=None):
        return Employee.objects.create(
            employee_code=code,
            first_name="Nhân",
            last_name="Viên",
            full_name=f"Nhân viên {code}",
            date_of_birth=date(1990, 1, 1),
            gender="Other",
            national_id=sha256(code.encode("utf-8")).hexdigest()[:20],
            tax_code=None,
            social_insurance_no=None,
            personal_email=email,
            company_email=email or f"{code.lower()}@example.test",
            mobile_phone="0900000000",
            address="Địa chỉ thử nghiệm",
            join_date=date(2020, 1, 1),
            department=self.department,
            position=self.position,
            employment_status="Active",
        )

    def make_user(self, code, employee, username):
        role, _ = Role.objects.get_or_create(role_code=code, defaults={"role_name": code})
        return User.objects.create_user(
            username=username, password="test-password", employee=employee, role=role
        )

    def test_notify_with_email_draft_creates_notification_and_outbox_once(self):
        employee = self.make_employee("NOTIF-ONCE")
        kwargs = {
            "employee": employee,
            "notification_type": "TestEvent",
            "title": "Có việc cần xem",
            "message": "Đăng nhập IHRMS để xem.",
            "link": "/portal/",
            "email_subject": "IHRMS: Có cập nhật",
            "email_body": "Vui lòng đăng nhập IHRMS.",
            "idempotency_key": "test-event:sample:recipient",
        }

        first_notification, first_outbox = notify_with_email_draft(**kwargs)
        second_notification, second_outbox = notify_with_email_draft(**kwargs)

        self.assertEqual(first_notification.pk, second_notification.pk)
        self.assertEqual(first_outbox.pk, second_outbox.pk)
        self.assertEqual(Notification.objects.filter(employee=employee, notification_type="TestEvent").count(), 1)
        self.assertEqual(NotificationEmailOutbox.objects.filter(idempotency_key=kwargs["idempotency_key"]).count(), 1)
        self.assertEqual(first_outbox.status, "Draft")
        self.assertTrue(first_outbox.mailto_url.startswith("mailto:"))

    def test_outbox_without_employee_email_skips_gracefully(self):
        employee = self.make_employee("NOTIF-NOEMAIL")
        employee.company_email = ""
        employee.personal_email = ""
        employee.save(update_fields=("company_email", "personal_email"))

        notification, outbox = notify_with_email_draft(
            employee, "TestEvent", "Thông báo", "Nội dung", "/portal/",
            "IHRMS", "Vui lòng đăng nhập.", idempotency_key="test-event:no-email",
        )

        self.assertIsNotNone(notification)
        self.assertIsNone(outbox)
        self.assertFalse(NotificationEmailOutbox.objects.filter(idempotency_key="test-event:no-email").exists())

    def test_mark_sent_requires_recipient_or_hr_permission(self):
        owner = self.make_employee("NOTIF-OWNER")
        owner_user = self.make_user("EMPLOYEE", owner, "notif-owner")
        outsider = self.make_employee("NOTIF-OTHER")
        outsider_user = self.make_user("EMPLOYEE", outsider, "notif-outsider")
        notification, outbox = notify_with_email_draft(
            owner, "TestEvent", "Thông báo", "Nội dung", "/portal/",
            "IHRMS", "Đăng nhập.", idempotency_key="test-event:owner",
        )
        self.client.force_login(outsider_user)

        response = self.client.post(reverse("portal:notification_outbox_mark_sent", args=(outbox.pk,)))

        outbox.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(outbox.status, "Draft")
        self.assertEqual(notification.employee_id, owner.pk)

    def test_recipient_can_confirm_outlook_send_and_outbox_records_audit(self):
        employee = self.make_employee("NOTIF-SENDER")
        user = self.make_user("EMPLOYEE", employee, "notif-sender")
        _, outbox = notify_with_email_draft(
            employee, "TestEvent", "Thông báo", "Nội dung", "/portal/",
            "IHRMS", "Đăng nhập.", idempotency_key="test-event:sent",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("portal:notification_outbox_mark_sent", args=(outbox.pk,)))

        outbox.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(outbox.status, "Sent")
        self.assertEqual(outbox.sent_by, user)
        self.assertIsNotNone(outbox.sent_at)

    def test_locked_payroll_period_creates_safe_drafts_for_finance_and_director(self):
        finance_employee = self.make_employee("NOTIF-FINANCE")
        finance_user = self.make_user("FINANCE_OFFICER", finance_employee, "notif-finance")
        director_employee = self.make_employee("NOTIF-DIRECTOR")
        self.make_user("DIRECTOR", director_employee, "notif-director")
        period = PayrollPeriod.objects.create(
            payroll_month=11, payroll_year=2026,
            start_date=date(2026, 11, 1), end_date=date(2026, 11, 30), status="Open",
        )
        from apps.payroll.test_fixtures import create_calculation_rates
        create_calculation_rates()
        payroll = Payroll.objects.create(payroll_period=period, employee=finance_employee, basic_salary=10000000)
        payroll.calculate()
        payroll.save()
        director_payroll = Payroll.objects.create(payroll_period=period, employee=director_employee, basic_salary=10000000)
        director_payroll.calculate()
        director_payroll.save()
        self.client.force_login(finance_user)

        response = self.client.post(reverse("portal:finance_payroll_lock", args=(period.pk,)))

        outboxes = NotificationEmailOutbox.objects.filter(
            notification__notification_type="payroll-period-locked"
        ).order_by("recipient_email")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(outboxes.count(), 2)
        self.assertTrue(all(item.status == "Draft" for item in outboxes))
        self.assertTrue(all("gross" not in item.body_text.lower() for item in outboxes))

    def test_document_decision_creates_outbox_for_submitter(self):
        requester = self.make_employee("NOTIF-DOC-OWNER")
        requester_user = self.make_user("EMPLOYEE", requester, "notif-doc-owner")
        approver = self.make_employee("NOTIF-DOC-HR")
        approver_user = self.make_user("HR_MANAGER", approver, "notif-doc-hr")
        category = DocumentCategory.objects.create(
            category_code="NOTIF-POLICY", category_name="Quy định kiểm thử"
        )
        document = Document.objects.create(
            document_no="NOTIF-DOC-001", document_name="Quy định an toàn test",
            category=category, status="PendingApproval", created_by=requester_user,
        )
        self.client.force_login(approver_user)

        response = self.client.post(
            reverse("portal:document_approve", args=(document.pk,)), {"decision": "Approved"}
        )

        outbox = NotificationEmailOutbox.objects.get(
            notification__employee=requester, notification__notification_type="document-decision"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(outbox.status, "Draft")
        self.assertNotIn(document.document_name, outbox.body_text)

    def test_leave_approval_creates_outbox_for_requester(self):
        requester = self.make_employee("NOTIF-LEAVE-EMP")
        manager = self.make_employee("NOTIF-LEAVE-MGR")
        requester.manager = manager
        requester.save(update_fields=["manager"])
        self.department.manager = manager
        self.department.save(update_fields=("manager",))
        manager_user = self.make_user("DEPT_MANAGER", manager, "notif-leave-manager")
        leave_type = LeaveType.objects.create(
            leave_type_code="NOTIF-ANNUAL", leave_type_name="Nghỉ năm test", is_paid=True
        )
        leave_request = LeaveRequest.objects.create(
            employee=requester, leave_type=leave_type, from_date=date(2026, 11, 2),
            to_date=date(2026, 11, 2), reason="Kiểm thử thông báo",
        )
        self.client.force_login(manager_user)

        response = self.client.post(
            reverse("portal:leave_approve", args=(leave_request.pk,)), {"decision": "Approved"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(NotificationEmailOutbox.objects.filter(
            notification__employee=requester, notification__notification_type="leave"
        ).exists())

    def test_private_approval_link_still_enforces_server_side_permission(self):
        employee = self.make_employee("NOTIF-NOPRIV")
        user = self.make_user("EMPLOYEE", employee, "notif-no-approval")
        self.client.force_login(user)

        response = self.client.get(reverse("portal:document_approval_list"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("portal:dashboard"))

    def test_mailto_fields_are_url_encoded(self):
        employee = self.make_employee("NOTIF-ENCODE")
        _, outbox = notify_with_email_draft(
            employee, "TestEvent", "Thông báo", "Nội dung", "/portal/",
            "Tiêu đề có dấu & ký tự", "Nội dung có dấu\nDòng thứ hai",
            idempotency_key="test-event:encode",
        )
        parsed = urlsplit(outbox.mailto_url)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.scheme, "mailto")
        self.assertEqual(params["subject"], ["Tiêu đề có dấu & ký tự"])
        self.assertEqual(params["body"], ["Nội dung có dấu\nDòng thứ hai"])


class DispatchNotificationCoverageTests(TestCase):
    """Độ phủ luồng công văn: vào sổ có người xử lý và cập nhật tiến độ phải báo tin."""

    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.clerk = cls.user(cls, "HR_MANAGER", True)
        cls.officer = cls.user(cls, "EMPLOYEE", True)

    def _dispatch(self, **overrides):
        book = DispatchBook.objects.create(
            book_code="IN-2026", book_name="Sổ đến 2026", book_type="Incoming", year=2026,
        )
        defaults = {
            "dispatch_type": "Incoming", "dispatch_book": book, "dispatch_no": "501/CV",
            "title": "CV theo dõi thông báo", "issuing_organization": "Đơn vị B",
            "issue_date": date(2026, 9, 20), "received_or_sent_date": date(2026, 9, 21),
            "assigned_to": self.officer.employee, "created_by": self.clerk,
        }
        defaults.update(overrides)
        return OfficialDispatch.objects.create(**defaults)

    def test_dispatch_create_notifies_assignee(self):
        self.client.force_login(self.clerk)
        response = self.client.post(reverse("portal:dispatch_create"), {
            "dispatch_type": "Incoming", "dispatch_no": "500/CV", "original_doc_no": "",
            "title": "Công văn kiểm thử thông báo", "issuing_organization": "Đơn vị A",
            "issue_date": "2026-09-20", "received_or_sent_date": "2026-09-21",
            "urgency_level": "Normal", "security_level": "Normal", "department": "",
            "assigned_to": str(self.officer.employee_id), "signer": "", "due_date": "",
        })

        self.assertEqual(response.status_code, 302)
        dispatch = OfficialDispatch.objects.get(dispatch_no="500/CV")
        notice = Notification.objects.filter(
            employee=self.officer.employee, notification_type="dispatch",
            link=f"/portal/dispatches/{dispatch.pk}/",
        ).first()
        self.assertIsNotNone(notice, "Vào sổ công văn có người xử lý phải tạo thông báo.")
        self.assertIn("500/CV", notice.message)

    def test_dispatch_created_without_assignee_notifies_nobody(self):
        self.client.force_login(self.clerk)
        response = self.client.post(reverse("portal:dispatch_create"), {
            "dispatch_type": "Incoming", "dispatch_no": "502/CV", "original_doc_no": "",
            "title": "Công văn chưa phân công", "issuing_organization": "Đơn vị A",
            "issue_date": "2026-09-20", "received_or_sent_date": "2026-09-21",
            "urgency_level": "Normal", "security_level": "Normal", "department": "",
            "assigned_to": "", "signer": "", "due_date": "",
        })

        self.assertEqual(response.status_code, 302)
        # Không có người xử lý thì không có ai để báo — nhưng công văn vẫn phải vào sổ,
        # nếu không phép "không thông báo" này chỉ là một redirect bị từ chối quyền.
        self.assertTrue(OfficialDispatch.objects.filter(dispatch_no="502/CV").exists())
        self.assertFalse(Notification.objects.filter(notification_type="dispatch").exists())

    def test_dispatch_progress_by_assignee_notifies_creator(self):
        dispatch = self._dispatch()
        self.client.force_login(self.officer)
        response = self.client.post(
            reverse("portal:dispatch_detail", args=[dispatch.pk]),
            {"action_type": "Đã xử lý", "comment": "Hoàn tất", "new_status": "Completed"},
        )

        self.assertEqual(response.status_code, 302)
        notice = Notification.objects.filter(
            employee=self.clerk.employee, notification_type="dispatch",
            link=f"/portal/dispatches/{dispatch.pk}/",
        ).first()
        self.assertIsNotNone(notice, "Người xử lý cập nhật thì phải báo người vào sổ.")
        self.assertIn(dict(OfficialDispatch.STATUS_CHOICES)["Completed"], notice.message)

    def test_dispatch_progress_update_never_notifies_the_actor(self):
        # Người vào sổ cũng là người xử lý: nhánh "báo phía bên kia" không được tự báo mình.
        dispatch = self._dispatch(assigned_to=self.clerk.employee)
        before = Notification.objects.filter(notification_type="dispatch").count()
        self.client.force_login(self.clerk)
        self.client.post(
            reverse("portal:dispatch_detail", args=[dispatch.pk]),
            {"action_type": "Đang xử lý", "comment": "Đang theo dõi", "new_status": "Processing"},
        )

        dispatch.refresh_from_db()
        self.assertEqual(dispatch.status, "Processing")
        self.assertEqual(Notification.objects.filter(notification_type="dispatch").count(), before)
