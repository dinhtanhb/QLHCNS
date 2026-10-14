"""Regression tests for the form wire comparator, independent of UI markup."""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

from django.test import SimpleTestCase


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
