from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from django import forms
from django.apps import apps
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.translation import override
from apps.common.ui_status import STATUS_BADGES, status_badge
from apps.common.templatetags.ui_components import ui_date, ui_vnd

class SharedComponentTests(SimpleTestCase):
    def test_registry_covers_existing_model_status_choices(self):
        covered=0
        for model in apps.get_models():
            if model._meta.app_label in {"admin","auth","sessions","axes","contenttypes"}:continue
            for field in model._meta.fields:
                if field.choices and field.name in {"status","employment_status","condition"}:
                    family=model._meta.label_lower+":"+field.name
                    self.assertEqual({k:v["label"] for k,v in STATUS_BADGES[family].items()},dict(field.flatchoices))
                    covered+=1
        self.assertEqual(covered,32)

    def test_badges_include_text_icon_and_safe_unknown_fallback(self):
        for family,states in STATUS_BADGES.items():
            for code,data in states.items():
                with self.subTest(family=family,code=code):
                    html=Template('{% load ui_components %}{% ui_badge family code %}').render(Context(dict(family=family,code=code)))
                    self.assertIn(data["label"],html)
                    self.assertIn('<svg',html)
                    self.assertIn('aria-hidden="true"',html)
        self.assertEqual(status_badge("unknown","<bad>")["tone"],"neutral")
        html=Template('{% load ui_components %}{% ui_badge "unknown" value %}').render(Context({"value":"<script>"}))
        self.assertNotIn('<script>',html)

    def test_display_helpers_preserve_floatformat_rounding_and_local_date(self):
        self.assertEqual(ui_vnd(Decimal("5000000")),"5.000.000 đ")
        self.assertEqual(ui_vnd(Decimal("2.5")),"3 đ")
        self.assertEqual(ui_vnd(None),"—")
        with override("en"):
            self.assertEqual(ui_vnd(Decimal("1234")),"1.234 đ")
        self.assertEqual(ui_date(date(2026,10,12)),"12/10/2026")
        self.assertEqual(ui_date(datetime(2026,10,11,18,tzinfo=dt_timezone.utc)),"12/10/2026")

    def test_bound_field_errors_and_summary_link_to_field(self):
        class Example(forms.Form):
            amount=forms.DecimalField(label="Số tiền",help_text="Đơn vị VND")
        form=Example({"amount":"wrong"})
        self.assertFalse(form.is_valid())
        field=render_to_string("ui/field.html",{"field":form["amount"]})
        self.assertIn('aria-invalid="true"',field)
        self.assertIn('aria-describedby="id_amount-help id_amount-error"',field)
        summary=render_to_string("ui/error_summary.html",{"form":form})
        self.assertIn('href="#id_amount"',summary)
        self.assertNotIn(' hidden',summary)
        class HiddenExample(forms.Form):
            token=forms.CharField(widget=forms.HiddenInput)
        hidden=render_to_string("ui/field.html",{"field":HiddenExample(initial={"token":"synthetic"})["token"]})
        self.assertIn('type="hidden"',hidden)
        self.assertNotIn('<label',hidden)


    def test_shared_partials_render_without_custom_context(self):
        for name in ['page_header','empty_state','alert','error_summary','confirm_dialog','kpi','detail_item']:
            with self.subTest(name=name):
                self.assertTrue(render_to_string('ui/'+name+'.html',{'title':'Mẫu giả','label':'Nhãn','value':0}).strip())
