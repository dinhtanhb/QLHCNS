from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.db.models import F
from django.test import TestCase
from django.urls import reverse

from apps.assistant.db_search import search_database
from apps.assistant.m365_search import can_query_sharepoint
from apps.assistant.nlp import parse
from apps.document.models import (
    DispatchBook,
    Document,
    DocumentCategory,
    OfficialDispatch,
    PersonnelDecision,
)
from apps.hrm.models import Employee
from apps.office.models import IncomingDocument, OutgoingDocument
from apps.portal import test_home_dashboard as fixtures
from apps.security.data_access import can_read_file
from apps.security.models import Role, User
from apps.security.permissions import (
    CBDA,
    DEPT_MANAGER,
    DIRECTOR,
    EMPLOYEE,
    FINANCE_OFFICER,
    HR_MANAGER,
    HR_OFFICER,
    PROJECT_COORDINATOR,
    PROJECT_MANAGER,
    SUPER_ADMIN,
    SYS_ADMIN,
)

ALL_ROLES = (
    SUPER_ADMIN, SYS_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER, DEPT_MANAGER,
    FINANCE_OFFICER, EMPLOYEE, PROJECT_MANAGER, PROJECT_COORDINATOR, CBDA,
)

RESULT_KEYS = {"source", "type", "title", "meta", "url", "date", "score"}


class DbSearchTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user(cls, "HR_MANAGER", True)
        cls.emp = cls.user(cls, "EMPLOYEE", True)

        cls.incoming_book = DispatchBook.objects.create(
            book_code="IN-2026", book_name="Sổ đến 2026", book_type="Incoming", year=2026,
        )
        cls.outgoing_book = DispatchBook.objects.create(
            book_code="OUT-2026", book_name="Sổ đi 2026", book_type="Outgoing", year=2026,
        )
        # department/assigned_to để trống có chủ đích: EMPLOYEE không có
        # access_outgoing_document nên scope của họ chỉ là công văn gắn vào
        # chính mình hoặc phòng của mình, nghĩa là không thấy bản nào.
        cls.dispatch = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=cls.incoming_book,
            dispatch_no="128/CV-ĐN", title="Công văn về nghỉ phép",
            issuing_organization="Sở Y tế", issue_date=date(2026, 9, 15),
            received_or_sent_date=date(2026, 9, 16), security_level="Normal",
        )
        cls.confidential = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=cls.incoming_book,
            dispatch_no="99/TM", title="Tài liệu mật nội bộ",
            issuing_organization="Ban giám đốc", issue_date=date(2026, 9, 1),
            received_or_sent_date=date(2026, 9, 2), security_level="Confidential",
        )
        cls.outgoing = OfficialDispatch.objects.create(
            dispatch_type="Outgoing", dispatch_book=cls.outgoing_book,
            dispatch_no="77/CV", title="Công văn gửi về nghỉ phép",
            issuing_organization="Phòng HCQT", issue_date=date(2026, 9, 20),
            received_or_sent_date=date(2026, 9, 21), security_level="Normal",
        )

        cls.category = DocumentCategory.objects.create(
            category_code="QT", category_name="Quy trình nội bộ",
        )
        cls.approved_doc = Document.objects.create(
            document_no="1234/QC-2026", document_name="Quy trình nghỉ phép không lương",
            category=cls.category, status="Approved", effective_date=date(2026, 9, 10),
        )
        cls.draft_doc = Document.objects.create(
            document_no="9999/QC-2026", document_name="Quy trình nghỉ phép bản nháp",
            category=cls.category, status="Draft", effective_date=date(2026, 9, 11),
        )
        cls.decision = PersonnelDecision.objects.create(
            employee=cls.emp.employee, template_slug="bo-nhiem",
            decision_no="45/QĐ-BN", decision_date=date(2026, 9, 5), status="Issued",
        )

    def _urls(self, results, type_name):
        return [r["url"] for r in results if r["type"] == type_name]

    def _dispatch_url(self, obj):
        return reverse("portal:dispatch_detail", args=[obj.pk])

    def test_hr_finds_dispatch_by_accented_keyword(self):
        results = search_database(parse("nghỉ phép"), self.hr)
        urls = self._urls(results, "official_dispatch")
        self.assertIn(self._dispatch_url(self.dispatch), urls)
        self.assertIn(self._dispatch_url(self.outgoing), urls)

    def test_quoted_phrase_matches_accented_title(self):
        # Ngoặc kép giữ nguyên dấu trong `phrases`, khác đường so khớp của
        # `keywords` (đã bỏ dấu), nên cần case riêng.
        results = search_database(parse('"nghỉ phép không lương"'), self.hr)
        self.assertEqual(
            self._urls(results, "document"), [reverse("portal:document_list")]
        )
        self.assertEqual(self._urls(results, "official_dispatch"), [])

    def test_employee_without_scope_finds_no_dispatch(self):
        results = search_database(parse("nghỉ phép"), self.emp)
        self.assertEqual(self._urls(results, "official_dispatch"), [])

    def test_confidential_hidden_from_employee_by_number(self):
        results = search_database(parse("99/TM"), self.emp)
        self.assertEqual(results, [])

    def test_hr_sees_confidential(self):
        results = search_database(parse("99/TM"), self.hr)
        urls = self._urls(results, "official_dispatch")
        self.assertEqual(urls, [self._dispatch_url(self.confidential)])
        self.assertTrue(results[0]["title"].startswith("[Công văn đến]"))

    def test_doc_number_ranks_first(self):
        results = search_database(parse("128/CV-ĐN nghỉ phép"), self.hr)
        dispatches = [r for r in results if r["type"] == "official_dispatch"]
        self.assertEqual(dispatches[0]["url"], self._dispatch_url(self.dispatch))
        self.assertGreaterEqual(dispatches[0]["score"], 100)

    def test_number_prefilter_does_not_loosen_full_match(self):
        # SQL chỉ chặn trước bằng dãy số ("128"), nên số hiệu sai hậu tố vẫn
        # phải bị loại ở bước đối chiếu trong Python.
        dispatches = self._urls(search_database(parse("128/TM"), self.hr), "official_dispatch")
        self.assertEqual(dispatches, [])

    def test_date_range_filters(self):
        inside = self._urls(search_database(parse("công văn tháng 9 năm 2026"), self.hr), "official_dispatch")
        self.assertIn(self._dispatch_url(self.dispatch), inside)
        outside = self._urls(search_database(parse("công văn tháng 7 năm 2026"), self.hr), "official_dispatch")
        self.assertEqual(outside, [])

    def test_dispatch_type_filter_picks_one_side(self):
        outgoing_only = self._urls(search_database(parse("công văn đi nghỉ phép"), self.hr), "official_dispatch")
        self.assertEqual(outgoing_only, [self._dispatch_url(self.outgoing)])
        incoming_only = self._urls(search_database(parse("công văn đến nghỉ phép"), self.hr), "official_dispatch")
        self.assertIn(self._dispatch_url(self.dispatch), incoming_only)
        self.assertNotIn(self._dispatch_url(self.outgoing), incoming_only)

    def test_only_approved_documents_are_returned(self):
        results = search_database(parse("nghỉ phép"), self.hr)
        self.assertEqual(
            self._urls(results, "document"), [reverse("portal:document_list")]
        )
        titles = " ".join(r["title"] for r in results if r["type"] == "document")
        self.assertIn("1234/QC-2026", titles)
        self.assertNotIn("9999/QC-2026", titles)

    def test_document_branch_url_and_shape(self):
        results = [r for r in search_database(parse("quy trình"), self.hr) if r["type"] == "document"]
        self.assertTrue(results)
        self.assertEqual(results[0]["url"], reverse("portal:document_list"))
        self.assertEqual(results[0]["date"], self.approved_doc.effective_date)

    def test_decisions_hidden_from_role_without_hr_permission(self):
        self.assertEqual(
            self._urls(search_database(parse("45/QĐ-BN"), self.emp), "personnel_decision"), []
        )

    def test_decision_found_by_number_for_hr(self):
        results = search_database(parse("45/QĐ-BN"), self.hr)
        urls = self._urls(results, "personnel_decision")
        self.assertEqual(urls, [reverse("portal:personnel_decision_detail", args=[self.decision.pk])])

    def test_no_constraints_returns_recent(self):
        # C22: câu toàn stopword phải thật sự không ràng buộc và vẫn có kết quả.
        parsed = parse("tìm giúp tôi", today=date(2026, 10, 19))
        self.assertFalse(parsed.has_constraints())
        results = search_database(parsed, self.hr)
        self.assertTrue(results)
        self.assertIn(self._dispatch_url(self.outgoing), self._urls(results, "official_dispatch"))

    def test_result_dict_shape(self):
        for result in search_database(parse("nghỉ phép"), self.hr):
            self.assertEqual(set(result), RESULT_KEYS)
            self.assertEqual(result["source"], "ihrms")
            self.assertIsInstance(result["score"], int)
            self.assertIn(result["type"], {"official_dispatch", "document", "personnel_decision"})

    def test_search_is_bounded(self):
        # Bản cũ chỉ đếm trên fixture ba công văn, nên assertion không bao giờ đỏ
        # kể cả ai đó xóa `MAX_PER_TYPE`. Phải vượt trần thật thì chắn mới được
        # kiểm chứng: 16 công văn khớp "nghỉ phép" nhưng chỉ 15 được trả.
        OfficialDispatch.objects.bulk_create([
            OfficialDispatch(
                dispatch_type="Incoming", dispatch_book=self.incoming_book,
                dispatch_no=f"9{i:02d}/CV-NP", title=f"Công văn nghỉ phép {i}",
                issuing_organization="Sở Y tế", issue_date=date(2026, 9, 1),
                received_or_sent_date=date(2026, 9, 2), security_level="Normal",
            )
            for i in range(16)
        ])
        results = search_database(parse("nghỉ phép"), self.hr)
        self.assertEqual(len(self._urls(results, "official_dispatch")), 15)

    def test_document_without_effective_date_is_not_lost(self):
        # `effective_date` có null=True. Sắp DESC mà không nói rõ NULL đứng đâu thì
        # SQLite để cuối, SQL Server để ĐẦU, và vì cắt theo SCAN_LIMIT sau ORDER BY,
        # sản xuất và test chọn hai tập ứng viên khác nhau. `nulls_last` chốt một
        # nghĩa trên cả hai; test này giữ cho bản không ngày vẫn nằm trong bảng.
        Document.objects.create(
            document_no="5555/QC-NULL", document_name="Quy trình nghỉ phép chưa hiệu lực",
            category=self.category, status="Approved", effective_date=None,
        )
        results = search_database(parse("nghỉ phép"), self.hr)
        self.assertTrue(
            any("chưa hiệu lực" in r["title"] for r in results if r["type"] == "document"),
            "văn bản chưa đặt ngày hiệu lực vẫn phải tìm được bằng từ khóa",
        )
        # Soạn SQL thật cho backend đang chạy, đừng nhìn `str(query)`: SQLite phát
        # ra "NULLS LAST" trực tiếp, SQL Server giả lập bằng "CASE WHEN ... IS NULL
        # THEN 1 ELSE 0 END". Kiểm một chuỗi cố định thì đỏ trên đúng cái backend
        # cần kiểm, còn test vẫn xanh khi nulls_last bị im lặng bỏ qua.
        sql, _ = Document.objects.order_by(
            F("effective_date").desc(nulls_last=True), "-id",
        ).query.sql_with_params()
        sql = sql.upper()
        self.assertTrue(
            "NULLS LAST" in sql or "IS NULL THEN 1 ELSE 0 END" in sql,
            "phải phát ra SQL đẩy NULL xuống cuối chứ không dựa vào mặc định của "
            "từng backend (SQLite để cuối, SQL Server để ĐẦU)",
        )

    def _gate_user(self, role_code):
        # `setUpTestData` đã tạo user HR_MANAGER/EMPLOYEE theo tên cố định, nên
        # dùng lại helper của fixture ở đây sẽ đụng unique trên `username` và biến
        # tám vai trò còn lại thành ERROR không liên quan gì tới quyền.
        role, _ = Role.objects.get_or_create(
            role_code=role_code, defaults={"role_name": role_code},
        )
        return User.objects.create(username=f"gate-{role_code.lower()}", role=role)

    def _gate_objects(self):
        """Một tệp cho MỖI kiểu đối tượng nằm trong ba thư mục allowlist.

        Cổng che ba kiểu này bằng ba quy tắc khác nhau: `OfficialDispatch` theo
        `security_level`, `IncomingDocument` theo `manage_office`,
        `OutgoingDocument` theo `access_outgoing_document`. Người giữ bản là nhân
        viên không liên kết với tài khoản nào dưới đây, để không vai trò nào được
        cộng thêm nhờ đường "đúng người được giao".
        """
        keeper = Employee.objects.create(
            employee_code="gate-keeper", first_name="Dữ", last_name="Liệu",
            full_name="Nhân viên giả giữ hồ sơ", date_of_birth=date(1990, 1, 1),
            gender="Other", national_id="gate0000000000000000",
            company_email="gate-keeper@example.test", mobile_phone="0900000000",
            join_date=date(2020, 1, 1), department=self.department,
            position=self.position, employment_status="Active",
        )
        incoming = IncomingDocument.objects.create(
            incoming_no="501/CVD-GATE", incoming_date=date(2026, 9, 1),
            sender="Sở Nội vụ", subject="Đơn xin nghỉ phép của nhân viên",
            received_by=keeper,
        )
        outgoing = OutgoingDocument.objects.create(
            outgoing_no="502/CVĐ-GATE", outgoing_date=date(2026, 9, 2),
            recipient="Sở Nội vụ", subject="Phản hồi đơn nghỉ phép",
            signed_by=keeper,
        )
        return [self.confidential, incoming, outgoing]

    def test_sharepoint_gate_matches_every_folder_it_reads(self):
        # Graph app-only trả tên tệp + webUrl của cả ba thư mục và không cho biết
        # tệp đó thuộc đối tượng nào, nên không thể lọc từng kết quả như
        # `db_search` làm. Cửa vì vậy phải hẹp bằng NGƯỜI XEM ĐƯỢC CẢ BA kiểu tệp
        # cùng lúc. Tiên đề lấy thẳng từ `can_read_file` - hàm cổng dùng để chặn
        # tải tệp - chứ không chép danh sách vai trò ở đây: thêm một vai trò vào
        # tập cửa mà quên quyền văn thư kèm theo thì đỏ ngay tại vai trò đó.
        objects = self._gate_objects()
        for role_code in ALL_ROLES:
            with self.subTest(role=role_code):
                asking = self._gate_user(role_code)
                may_see_every_file = all(can_read_file(asking, obj) for obj in objects)
                self.assertEqual(
                    can_query_sharepoint(asking), may_see_every_file,
                    f"vai trò {role_code}: nguồn SharePoint phải hẹp đúng bằng phạm vi cổng",
                )

    def test_superuser_may_query_sharepoint_without_a_role_row(self):
        asking = self._gate_user("EMPLOYEE")
        asking.is_superuser = True
        self.assertTrue(can_query_sharepoint(asking))

    def test_dead_session_may_not_query_sharepoint(self):
        # `login_required` chỉ hỏi `is_authenticated`, còn `ModelBackend` không
        # kiểm lại `is_active` sau khi đăng nhập - tài khoản bị vô hiệu hóa giữa
        # phiên vẫn gọi được API. `visible_dispatches_for` đã trả `qs.none()` cho
        # họ, nên nếu cửa SharePoint chỉ nhìn mã vai trò thì một nguồn im lặng
        # trong khi nguồn kia vẫn đọc tên tệp toàn thư viện.
        asking = self._gate_user("HR_MANAGER")
        asking.is_active = False
        self.assertFalse(can_query_sharepoint(asking))
        self.assertFalse(can_query_sharepoint(AnonymousUser()))
