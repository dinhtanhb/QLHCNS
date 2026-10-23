"""Phương án B, quyết định 23/10: dải tab trạng thái + biểu mẫu hai cột.

Ba thứ được khoá ở đây, vì cả ba đều dễ trôi mà không ai thấy:
1. Số trên tab là số của từng trạng thái (đếm trước khi lọc), không phải số của
   kết quả đang xem — nếu đếm sau khi lọc thì mọi tab luôn bằng nhau.
2. Tab giữ nguyên từ khóa và loại văn bản, bỏ `page` để không rơi vào trang trống.
3. Cột ngữ cảnh của biểu mẫu chỉ đọc, không chứa trường nhập.
"""
from datetime import date
from hashlib import sha256

from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.contract.models import Contract, ContractType
from apps.document.models import PersonnelDecision
from apps.hrm.models import Employee
from apps.organization.models import Department, Organization, Position
from apps.portal.views.common import _status_tabs
from apps.security.models import Role, User


class StatusTabsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.choices = [("Active", "Đang làm"), ("Probation", "Thử việc")]
        cls.param = "employment_status"
        org = Organization.objects.create(organization_code="TABH", organization_name="Tổ chức tab helper")
        cls.department = Department.objects.create(
            department_code="TABH", department_name="Phòng tab helper", organization=org)
        cls.position = Position.objects.create(position_code="TABH", position_name="Chuyên viên tab helper")

    def _tabs(self, queryset, path="/danh-sach/", **params):
        request = self.factory.get(path, params)
        return _status_tabs(request, queryset, self.choices, param=self.param)

    def test_counts_come_from_unfiltered_queryset(self):
        for index, status in enumerate(("Active", "Active", "Probation")):
            Employee.objects.create(
                employee_code=f"TAB-{index}", first_name="A", last_name="B", full_name=f"Một {index}",
                date_of_birth=date(1990, 1, 1), gender="Other", national_id=f"TAB{index}",
                company_email=f"tab{index}@example.test", mobile_phone="0900000001",
                join_date=date(2020, 1, 1), department=self.department,
                position=self.position, employment_status=status)
        queryset = Employee.objects.filter(employment_status__in=["Active", "Probation"])
        tabs = self._tabs(queryset)
        self.assertEqual(tabs[0]["count"], 3)
        self.assertEqual([tab["count"] for tab in tabs[1:]], [2, 1])

    def test_tab_url_keeps_other_filters_and_drops_page(self):
        tabs = self._tabs(Employee.objects.none(), path="/cong-van/", q="hop dong", type="Incoming", page="3")
        urls = [tab["url"] for tab in tabs]
        self.assertEqual(urls[0], "/cong-van/?q=hop+dong&type=Incoming")
        self.assertEqual(urls[1], "/cong-van/?q=hop+dong&type=Incoming&employment_status=Active")
        self.assertFalse(any("page=" in url for url in urls))

    def test_active_flag_follows_current_value(self):
        tabs = self._tabs(Employee.objects.none(), employment_status="Probation")
        self.assertEqual([tab["active"] for tab in tabs], [False, False, True])
        default_tabs = self._tabs(Employee.objects.none())
        self.assertEqual([tab["active"] for tab in default_tabs], [True, False, False])


class ListToolbarPageTests(TestCase):
    """Ba trang danh sách đã chuyển sang tab phải render đúng thanh dính."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(organization_code="TABS", organization_name="Tổ chức tab")
        cls.department = Department.objects.create(
            department_code="TABS", department_name="Phòng tab", organization=cls.org)
        cls.position = Position.objects.create(position_code="TABS", position_name="Chuyên viên tab")

    def make_user(self, role_code):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        employee = Employee.objects.create(
            employee_code="TABS-" + role_code, first_name="Tab", last_name="Giả",
            full_name="Nhân viên tab", date_of_birth=date(1990, 1, 1), gender="Other",
            national_id=sha256(role_code.encode()).hexdigest()[:20],
            company_email=role_code.lower() + "@example.test", mobile_phone="0900000002",
            join_date=date(2020, 1, 1), department=self.department, position=self.position,
            employment_status="Active")
        return User.objects.create(username="tabs-" + role_code.lower(), role=role, employee=employee)

    def test_contract_list_renders_tabs_with_per_status_counts(self):
        contract_type = ContractType.objects.create(contract_type_code="TABS", contract_type_name="Loại tab")
        employee = self.make_user("HR_MANAGER").employee
        for index, status in enumerate(("Active", "Active", "Draft")):
            Contract.objects.create(
                employee=employee, contract_type=contract_type, contract_no=f"TABS-{index}",
                start_date=date(2024, 1, 1), basic_salary=1000000, status=status)
        self.client.force_login(User.objects.get(username="tabs-hr_manager"))

        response = self.client.get(reverse("portal:hr_contract_list"))
        self.assertEqual(response.status_code, 200)
        tabs = response.context["status_tabs"]
        counts = {tab["value"]: tab["count"] for tab in tabs}
        self.assertEqual(counts[""], 3)
        self.assertEqual(counts["Active"], 2)
        self.assertEqual(counts["Draft"], 1)
        self.assertContains(response, 'class="ui-list-toolbar')

        filtered = self.client.get(reverse("portal:hr_contract_list"), {"status": "Draft"})
        self.assertEqual([c.contract_no for c in filtered.context["contracts"]], ["TABS-2"])
        active_tabs = [tab["value"] for tab in filtered.context["status_tabs"] if tab["active"]]
        self.assertEqual(active_tabs, ["Draft"])

    def test_personnel_decision_list_replaces_status_select_with_tabs(self):
        self.client.force_login(self.make_user("HR_MANAGER"))
        response = self.client.get(reverse("portal:personnel_decision_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ui-status-tabs")
        self.assertNotContains(response, 'id="personnel-decision-list-status"')
        # Tab giữ đủ mọi lựa chọn của model, kể cả trạng thái chưa có bản ghi.
        self.assertEqual(
            [tab["value"] for tab in response.context["status_tabs"]][1:],
            [value for value, _ in PersonnelDecision.STATUS_CHOICES])

    def test_dispatch_list_tab_url_keeps_dispatch_type(self):
        self.client.force_login(self.make_user("HR_MANAGER"))
        response = self.client.get(reverse("portal:dispatch_list"), {"type": "Incoming"})
        self.assertEqual(response.status_code, 200)
        for tab in response.context["status_tabs"]:
            self.assertIn("type=Incoming", tab["url"])
        self.assertContains(response, 'class="ui-list-toolbar')


class FormLayoutTests(TestCase):
    """Biểu mẫu hai cột: cột ngữ cảnh chỉ đọc và luôn có link quay lại."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(organization_code="FORM", organization_name="Tổ chức form")
        cls.department = Department.objects.create(
            department_code="FORM", department_name="Phòng form", organization=cls.org)
        cls.position = Position.objects.create(position_code="FORM", position_name="Chuyên viên form")

    def make_user(self, role_code, linked=True):
        role, _ = Role.objects.get_or_create(role_code=role_code, defaults={"role_name": role_code})
        employee = None
        if linked:
            employee = Employee.objects.create(
                employee_code="FORM-" + role_code, first_name="Form", last_name="Giả",
                full_name="Nhân viên form", date_of_birth=date(1990, 1, 1), gender="Other",
                national_id=sha256(role_code.encode()).hexdigest()[:20],
                company_email=role_code.lower() + "@example.test", mobile_phone="0900000003",
                join_date=date(2020, 1, 1), department=self.department, position=self.position,
                employment_status="Active")
        return User.objects.create(username="form-" + role_code.lower(), role=role, employee=employee)

    def test_leave_form_has_layout_and_balance_rail(self):
        self.client.force_login(self.make_user("EMPLOYEE"))
        response = self.client.get(reverse("portal:leave_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="ui-form-layout"')
        self.assertContains(response, 'class="ui-form-rail"')
        self.assertContains(response, "Quỹ phép của bạn")
        # Cột ngữ cảnh không được chứa trường nhập: nếu có, nó thành cột thứ hai
        # của biểu mẫu và phá hợp đồng 4/3/2/1 của .ui-form-grid.
        rail = response.content.decode().split('class="ui-form-rail"', 1)[1].split("</aside>", 1)[0]
        self.assertNotIn("<input", rail)
        self.assertNotIn("<select", rail)
        self.assertNotIn("<textarea", rail)

    def test_contract_form_rail_shows_selected_employee_and_last_contract(self):
        manager = self.make_user("HR_MANAGER")
        employee = manager.employee
        contract_type = ContractType.objects.create(contract_type_code="FORM", contract_type_name="Loại form")
        Contract.objects.create(
            employee=employee, contract_type=contract_type, contract_no="FORM-01",
            start_date=date(2024, 1, 1), basic_salary=1000000, status="Active")
        self.client.force_login(manager)

        response = self.client.get(reverse("portal:hr_contract_create"), {"employee_id": employee.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nhân viên đang chọn")
        self.assertContains(response, "Hợp đồng gần nhất")
        self.assertContains(response, "FORM-01")

        blank = self.client.get(reverse("portal:hr_contract_create"))
        self.assertContains(blank, "Chọn nhân viên")
        self.assertNotContains(blank, "Hợp đồng gần nhất")

    def test_employee_form_rail_never_contains_inputs(self):
        manager = self.make_user("HR_MANAGER")
        self.client.force_login(manager)
        for url in (reverse("portal:hr_employee_create"),
                    reverse("portal:hr_employee_edit", args=[manager.employee.pk])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="ui-form-layout"')
                rail = response.content.decode().split('class="ui-form-rail"', 1)[1].split("</aside>", 1)[0]
                self.assertNotIn("<input", rail)
                self.assertNotIn("<select", rail)
