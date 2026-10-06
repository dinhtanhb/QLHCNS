import io
from datetime import date
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from django import forms
from django.test import TestCase
from django.urls import reverse
from apps.asset.models import Asset, AssetType
from apps.project.models import Project
from apps.recruitment.models import Candidate
from . import tests_hcns as fixtures
from .hcns.catalog import FORMS
from .hcns.choices import ReferenceField


class HCNSChoiceTests(TestCase):
    user = classmethod(fixtures.HCNSFormTests.user.__func__)
    data = fixtures.HCNSFormTests.data

    @classmethod
    def setUpTestData(cls):
        fixtures.HCNSFormTests.setUpTestData.__func__(cls)
        cls.project = Project.objects.create(project_code='CHOICE', project_name='Synthetic project', department=cls.department)
        cls.candidates = [Candidate.objects.create(candidate_code=f'CHOICE-{i}', full_name='Same applicant name',
                                                  phone_number=f'000{i}', email=f'candidate{i}@example.test') for i in range(2)]
        kind = AssetType.objects.create(asset_type_code='CHOICE', asset_type_name='Synthetic type')
        cls.assets = [Asset.objects.create(asset_code=f'CHOICE-{i}', asset_name='Same asset name', asset_type=kind) for i in range(2)]

    def setUp(self):
        self.client.force_login(self.hr)

    def url(self, slug):
        return reverse('portal:hcns_draft', args=[slug])

    def test_every_template_uses_reference_selectors_and_exports_selected_labels(self):
        for slug in FORMS:
            with self.subTest(slug=slug):
                response = self.client.get(self.url(slug))
                self.assertEqual(response.status_code, 200)
                form = response.context['form']
                data = self.data(slug, action='export')
                for key, field in form.fields.items():
                    if isinstance(field, ReferenceField):
                        self.assertIsInstance(field.widget, forms.Select)
                        obj = field.queryset.first()
                        data[key] = obj.pk if obj else ''
                for section in response.context['editor_sections']:
                    if section['table']:
                        for row_form in section['table']['formset'].forms:
                            for key, field in row_form.fields.items():
                                if isinstance(field, ReferenceField):
                                    self.assertIsInstance(field.widget, forms.Select)
                                    obj = field.queryset.first()
                                    data[f'{row_form.prefix}-{key}'] = obj.pk if obj else ''
                exported = self.client.post(self.url(slug), data)
                self.assertEqual(exported.status_code, 200)
                self.assertIn('Content-Disposition', exported)
                if slug == 'salary-decision':
                    with ZipFile(io.BytesIO(exported.content)) as archive:
                        content = ''.join(ET.fromstring(archive.read('word/document.xml')).itertext())
                        self.assertIn(self.employees[0].full_name, content)
                        self.assertIn(self.position.position_name, content)

    def test_foreign_deleted_and_arbitrary_values_cannot_be_exported(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url('resignation'), self.data('resignation', full_name=self.employees[0].pk, action='export'))
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('Content-Disposition', response)
        response = self.client.get(self.url('employee-information'), {'employee_id': self.employees[1].pk})
        refs = response.context['reference_data']['employees']
        self.assertEqual(set(refs), {str(self.employees[1].pk)})
        self.client.force_login(self.hr)
        self.employees[2].delete()
        for key, value in [('full_name', self.employees[2].pk), ('signer', self.employees[2].pk), ('project', 'free text'), ('department', 999999)]:
            response = self.client.post(self.url('salary-decision'), self.data('salary-decision', **{key: value, 'action': 'export'}))
            self.assertEqual(response.status_code, 422)
            self.assertNotIn('Content-Disposition', response)

    def test_candidate_source_uses_identity_and_never_confuses_employee_with_applicant(self):
        candidate = self.candidates[1]
        response = self.client.get(self.url('candidate-interview'), {'candidate_id': candidate.pk})
        self.assertEqual(response.context['form']['full_name'].value(), candidate.pk)
        self.assertEqual(response.context['form']['email'].value(), candidate.email)
        exported = self.client.get(self.url('candidate-interview'), {'candidate_id': candidate.pk, 'export': '1'})
        self.assertIn('Content-Disposition', exported)
        response = self.client.get(self.url('candidate-interview'), {'employee_id': self.employees[0].pk})
        self.assertEqual(response.context['form']['full_name'].value(), '')
        self.assertEqual(response.context['form']['email'].value(), '')
        response = self.client.post(self.url('candidate-interview') + f'?candidate_id={self.candidates[0].pk}',
                                    self.data('candidate-interview', full_name=candidate.pk, email=candidate.email))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['source_query'], f'candidate_id={candidate.pk}')

    def test_mismatched_asset_and_candidate_identity_is_rejected(self):
        for slug, overrides in [
            ('asset-inventory', {'assets-0-name': self.assets[0].pk, 'assets-0-code': self.assets[1].pk}),
            ('candidate-score-summary', {'results-0-candidate': self.candidates[0].pk, 'results-0-candidate_code': self.candidates[1].pk,
                                         'results-0-interviewer': self.employees[0].pk}),
        ]:
            response = self.client.post(self.url(slug), self.data(slug, action='export', **overrides))
            self.assertEqual(response.status_code, 422)
            self.assertNotIn('Content-Disposition', response)

    def test_salary_source_keeps_recorded_amount_and_dropdown_selection(self):
        from apps.payroll.models import EmployeeSalary
        employee = self.employees[1]
        salary = EmployeeSalary.objects.create(employee=employee, current_basic_salary=23000000, effective_date=date(2090, 1, 1))
        response = self.client.get(self.url('salary-decision'), {'salary_id': salary.pk})
        form = response.context['form']
        self.assertEqual(form['full_name'].value(), employee.pk)
        self.assertEqual(form['position'].value(), employee.position_id)
        self.assertEqual(form['department'].value(), employee.department_id)
        self.assertEqual(form['salary'].value(), 23000000)
        response = self.client.post(self.url('salary-decision') + f'?salary_id={salary.pk}',
                                    self.data('salary-decision', full_name=employee.pk, salary=23000000, effective_date='2090-01-01'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'salary_id={salary.pk}', response.context['source_query'])

    def test_asset_source_committee_is_readable_without_hr_directory_access(self):
        from django.utils import timezone
        from apps.asset.models import InventorySession, InventoryMember
        viewer = self.user('choice-asset-viewer', 'PROJECT_COORDINATOR', None)
        session = InventorySession.objects.create(session_name='Synthetic session', office_name='Synthetic office', inventory_datetime=timezone.now())
        InventoryMember.objects.create(session=session, employee=self.employees[1], role='Member')
        self.client.force_login(viewer)
        response = self.client.get(self.url('asset-inventory'), {'inventory_id': session.pk})
        self.assertEqual(response.status_code, 200)
        data = response.context['reference_data']['employees']
        self.assertEqual(data, {str(self.employees[1].pk): {'position': str(self.position.pk)}})
        exported = self.client.get(self.url('asset-inventory'), {'inventory_id': session.pk, 'export': '1'})
        self.assertIn('Content-Disposition', exported)
