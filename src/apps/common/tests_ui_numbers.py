from decimal import Decimal
from django.test import SimpleTestCase
from django.template import Template, Context
from apps.common.number_format import vi_number

class NumberPresentationTests(SimpleTestCase):
    def test_exact_decimal_and_grouping(self):
        self.assertEqual(vi_number(Decimal("1234567890123.0700")), "1.234.567.890.123,07")
        self.assertEqual(vi_number(Decimal("-1234.5"), 2), "-1.234,50")
        self.assertEqual(vi_number(0), "0")
        from types import SimpleNamespace
        from unittest.mock import patch
        from django.core.exceptions import ValidationError
        from apps.common.uploads import validate_upload
        with patch.multiple("apps.common.uploads", MAX_UPLOAD_SIZE_MB=1, MAX_UPLOAD_SIZE=1048576):
            with self.assertRaisesMessage(ValidationError, "Tệp nặng 1,5 MB"):
                validate_upload(SimpleNamespace(name="synthetic.pdf", size=1572864))


    def test_template_visible_number_and_canonical_attribute(self):
        rendered = Template('<input value="{{ amount }}">{{ amount|ui_number }} {{ amount|floatformat:"0g" }} {{ year }}').render(Context({"amount":5000000,"year":2026}))
        self.assertEqual(rendered, '<input value="5000000">5.000.000 5.000.000 2026')
        self.assertEqual(Template('{{ text|ui_number }}').render(Context({"text":"Mã 001"})), 'Mã 001')
