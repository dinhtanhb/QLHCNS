"""Regression tests for the form wire comparator, independent of UI markup."""
import importlib.util
from pathlib import Path
import sys
import re
from unittest.mock import patch

from django.test import SimpleTestCase
from django.template.loader import render_to_string
from django import forms


class FormContractToolTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ops=Path(__file__).resolve().parents[3]/'ops'
        with patch.object(sys,'path',[str(ops),*sys.path]):
            spec=importlib.util.spec_from_file_location('form_contract_audit_test',ops/'run_form_contract_uat.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        cls.parser=module.FormContract

    def test_presentation_and_csrf_rotation_do_not_change_wire_contract(self):
        old='<form method="post"><input name="csrfmiddlewaretoken" value="old"><label for="a">Tên</label><input id="a" name="name" required value="Giả"></form>'
        new='<form method="post" class="ui-form-stack"><fieldset><legend>Danh tính</legend><div><input name="csrfmiddlewaretoken" value="new"><label for="b">Tên</label><input id="b" class="ui-field" name="name" required value="Giả" aria-describedby="hint"></div></fieldset></form>'
        self.assertEqual(self.parser(old).forms,self.parser(new).forms)

    def test_order_required_default_action_and_options_are_business_contract(self):
        original='<form method="post" action="/save/"><input name="a" required value="0"><select name="b"><option value="x" selected>Giả</option></select></form>'
        baseline=self.parser(original).forms
        for altered in (original.replace(' required',''),original.replace('value="0"','value="1"'),
                        original.replace('/save/','/other/'),original.replace('value="x"','value="y"'),
                        original.replace('<input name="a" required value="0">','').replace('</select>','</select><input name="a" required value="0">')):
            with self.subTest(html=altered):self.assertNotEqual(baseline,self.parser(altered).forms)


class FormGridComponentTests(SimpleTestCase):
    def test_grid_columns_have_one_source_and_no_legacy_template_classes(self):
        source = Path(__file__).resolve().parents[2]
        owners = []
        for path in (source / 'static/css').glob('*.css'):
            if path.name == 'tailwind.css':
                continue
            for selector, body in re.findall(r'([^{}]+)\{([^{}]*)\}', path.read_text(encoding='utf-8')):
                if '.ui-form-grid' in selector and 'grid-template-columns:' in body:
                    owners.append(path.name)
        self.assertEqual(owners, ['shared_components.css'])
        for path in (source / 'static/css').glob('*.css'):
            if path.name == 'tailwind.css':
                continue
            content = path.read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'\b(?:ui-form-lines|ui-form-line)\b', content))
        for path in (source / 'apps').rglob('*.html'):
            if 'hcns' in path.parts or 'print' in path.stem:
                continue
            with self.subTest(template=path.name):
                self.assertIsNone(re.search(r'\b(?:ui-hr-input|ui-hr-form|ui-form-grid--three|ui-form-lines|ui-form-line)\b', path.read_text(encoding='utf-8')))

    def test_optional_hint_error_and_spans_keep_accessible_controls(self):
        output = render_to_string('ui/field.html', {'id':'example', 'name':'unchanged', 'label':'Name'})
        self.assertIn('ui-field--4', output)
        self.assertIn('name="unchanged"', output)
        output = render_to_string('ui/field.html', {'id':'example', 'name':'unchanged', 'label':'Name',
            'span':6, 'hint':'Helpful text', 'error':'Invalid <value>', 'required':True})
        self.assertIn('ui-field--6', output)
        self.assertIn('aria-describedby="example-help example-error"', output)
        self.assertIn('aria-invalid="true"', output)
        self.assertIn('Invalid &lt;value&gt;', output)
        self.assertNotIn('id="example-error" hidden', output)

    def test_bound_field_keeps_validation_and_uses_its_help_and_error_ids(self):
        class Example(forms.Form):
            amount = forms.DecimalField(help_text='A number', min_value=0)
        form = Example({'amount':'-1'})
        output = render_to_string('ui/field.html', {'field':form['amount']})
        self.assertIn('ui-field--3', output)
        self.assertIn('aria-describedby="id_amount-help id_amount-error"', output)
        self.assertIn('name="amount"', output)
        self.assertIn('value="-1"', output)
        self.assertIn('required', output)
