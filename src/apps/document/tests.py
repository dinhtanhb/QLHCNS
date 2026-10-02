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
    def make_user(cls, role_code, username):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        return User.objects.create_user(
            username=username, password="test-password", employee=cls.employee, role=role
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
