"""Invalid HR submissions retain input without mutating persisted employees."""
from django.test import override_settings
from django.urls import reverse

from apps.portal import tests_review_20261008 as fixtures


@override_settings(AXES_ENABLED=False)
class InvalidEmployeePostTests(fixtures.Review20261008Fixtures):
    def setUp(self):
        self.employee = self.make_employee('INVALID-B')
        self.client.force_login(self.make_user('HR_MANAGER', self.make_employee('HR-B'), 'invalid-b-hr'))
        self.url = reverse('portal:hr_employee_edit', args=[self.employee.pk])

    def test_empty_post_renders_errors_without_changing_employee(self):
        before = type(self.employee).objects.filter(pk=self.employee.pk).values().get()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Không thể cập nhật.')
        self.assertEqual(type(self.employee).objects.filter(pk=self.employee.pk).values().get(), before)

    def test_invalid_foreign_keys_types_and_missing_fields_retain_input(self):
        before = type(self.employee).objects.filter(pk=self.employee.pk).values().get()
        for changed in [{'department': ''}, {'department': '2147483647'}, {'department': 'not-an-id'},
                        {'position': 'not-an-id'}, {'date_of_birth': 'not-a-date'}, {'gender': 'invalid'}]:
            with self.subTest(changed=changed):
                data = self.employee_form_data('B-INPUT', employee_code=self.employee.employee_code)
                data.update(changed)
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Không thể cập nhật.')
                self.assertContains(response, 'value="Nhân viên B-INPUT"', html=False)
                self.assertEqual(type(self.employee).objects.filter(pk=self.employee.pk).values().get(), before)

    def test_valid_post_still_saves_and_redirects(self):
        data = self.employee_form_data('B-VALID', employee_code=self.employee.employee_code)
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('portal:hr_employee_detail', args=[self.employee.pk]))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.full_name, 'Nhân viên B-VALID')
