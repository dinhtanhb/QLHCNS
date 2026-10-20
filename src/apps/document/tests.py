from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.document.models import DispatchBook, Document, DocumentCategory, OfficialDispatch
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.security.models import Role, User


class DocumentTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        org = Organization.objects.create(organization_code="DOC-ORG", organization_name="Tổ chức")
        cls.department = Department.objects.create(
            organization=org, department_code="DOC-DEPT", department_name="Phòng kiểm thử"
        )
        cls.position = Position.objects.create(position_code="DOC-POS", position_name="Nhân viên")
        cls.employee = Employee.objects.create(
            employee_code="DOC-EMP", first_name="An", last_name="Kiểm thử", full_name="DOC-EMP",
            date_of_birth=date(1990, 1, 1), gender="Other", national_id="DOC-EMP",
            company_email="doc-emp@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
        )
        cls.category = DocumentCategory.objects.create(
            category_code="DOC-CAT", category_name="Quy trình"
        )

    @classmethod
    def make_user(cls, role_code, username, employee=None):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        if employee is None:
            employee = Employee.objects.create(
                employee_code=f"EMP-{username.upper()[:12]}", first_name="User", last_name=username, full_name=username,
                date_of_birth=date(1990, 1, 1), gender="Other", national_id=f"ID-{username.upper()[:12]}",
                company_email=f"{username.lower()}@example.test", mobile_phone="0900000000",
                join_date=date(2020, 1, 1), department=cls.department, position=cls.position,
            )
        return User.objects.create_user(
            username=username, password="test-password", employee=employee, role=role
        )


class DocumentConstraintAndUploadTests(DocumentTestBase):
    def test_dispatch_book_is_unique_by_type_and_year(self):
        DispatchBook.objects.create(
            book_code="DOC-BOOK-2026", book_name="Sổ công văn đến 2026",
            book_type="Incoming", year=2026,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DispatchBook.objects.create(
                    book_code="DOC-BOOK-2026-2", book_name="Sổ công văn đến trùng",
                    book_type="Incoming", year=2026,
                )

    def test_document_and_dispatch_attachments_reject_executable_uploads(self):
        for model, field_name in (
            (Document, "uploaded_file"),
            (OfficialDispatch, "attachment"),
        ):
            field = model._meta.get_field(field_name)
            with self.subTest(model=model.__name__, field=field_name):
                with self.assertRaises(ValidationError):
                    field.validators[0](SimpleUploadedFile("virus.exe", b"not executable"))


class DocumentViewPermissionTests(DocumentTestBase):
    def test_employee_cannot_approve_document_by_direct_post(self):
        document = Document.objects.create(
            document_no="DOC-PENDING-1", document_name="Quy trình chờ duyệt",
            category=self.category, status="PendingApproval",
        )
        self.client.force_login(self.make_user("EMPLOYEE", "doc-employee-approver"))

        response = self.client.post(
            reverse("portal:document_approve", args=(document.pk,)),
            {"decision": "Approved"},
        )

        document.refresh_from_db()
        self.assertRedirects(response, reverse("portal:dashboard"))
        self.assertEqual(document.status, "PendingApproval")
        self.assertFalse(document.approvals.exists())


from apps.document.admin import DispatchTrackingAdmin, DocumentAdmin
from apps.document.models import DispatchTracking
from django.contrib.admin.sites import AdminSite


class MockRequest:
    def __init__(self, user):
        self.user = user
        self.GET = {}


class DocumentAdminScopeTests(DocumentTestBase):
    def test_dispatch_tracking_admin_scope_excludes_confidential_dispatch(self):
        dept_manager = self.make_user("DEPT_MANAGER", "doc-dept-mgr")
        hr_manager = self.make_user("HR_MANAGER", "doc-hr-mgr")

        book = DispatchBook.objects.create(
            book_code="DOC-BOOK-INTERNAL", book_name="Sổ nội bộ",
            book_type="Incoming", year=2026,
        )
        confidential_dispatch = OfficialDispatch.objects.create(
            dispatch_type="Internal",
            dispatch_book=book,
            dispatch_no="CV-INTERNAL-CONFIDENTIAL",
            title="Công văn mật",
            security_level="Confidential",
            issue_date=date(2026, 9, 25),
            received_or_sent_date=date(2026, 9, 25),
            created_by=hr_manager,
        )
        tracking = DispatchTracking.objects.create(
            dispatch=confidential_dispatch,
            actor=self.employee,
            action_type="Created",
            comment="Ghi chú xử lý mật",
        )

        admin = DispatchTrackingAdmin(DispatchTracking, AdminSite())
        request = MockRequest(dept_manager)
        qs = admin.get_queryset(request)
        self.assertNotIn(tracking, qs)

    def test_document_admin_scope_excludes_other_users_drafts_for_dept_manager(self):
        dept_manager = self.make_user("DEPT_MANAGER", "doc-dept-mgr-2")
        hr_user = self.make_user("HR_MANAGER", "doc-hr-user-2")

        draft_doc = Document.objects.create(
            document_no="DOC-DRAFT-OTHER",
            document_name="Tài liệu nháp của HR",
            category=self.category,
            status="Draft",
            created_by=hr_user,
        )
        my_draft = Document.objects.create(
            document_no="DOC-DRAFT-MINE",
            document_name="Tài liệu nháp của tôi",
            category=self.category,
            status="Draft",
            created_by=dept_manager,
        )
        approved_doc = Document.objects.create(
            document_no="DOC-APPROVED-ALL",
            document_name="Tài liệu đã ban hành",
            category=self.category,
            status="Approved",
            created_by=hr_user,
        )

        admin = DocumentAdmin(Document, AdminSite())
        request = MockRequest(dept_manager)
        qs = admin.get_queryset(request)
        self.assertIn(approved_doc, qs)
        self.assertIn(my_draft, qs)
        self.assertNotIn(draft_doc, qs)
