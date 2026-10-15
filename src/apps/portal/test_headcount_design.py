"""Report presentation preserves raw counts, filters and print values."""
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase


class HeadcountDesignTests(SimpleTestCase):
    def test_gap_labels_keep_raw_values_and_filter_contract(self):
        from django.http import QueryDict
        request = SimpleNamespace(path='/portal/reports/headcount/', GET=QueryDict('year=2026'))
        plans = [SimpleNamespace(department='Phòng giả', planned_headcount=3,
                                 actual_headcount=3-gap, gap=gap) for gap in (-30, 5, 0)]
        html = render_to_string('portal/report_headcount.html', {
            'request': request, 'plans': plans, 'year': 2026, 'years': [2025, 2026, 2027],
        })
        for label in ('Vượt 30', 'Thiếu 5', 'Đủ'):
            self.assertIn(label, html)
        for raw in ('-30', '5', '0'):
            self.assertIn('data-value="'+raw+'"', html)
            self.assertIn('class="headcount-gap-raw">'+raw+'</span>', html)
        self.assertIn('name="year"', html)
        self.assertIn('value="2026" selected', html)
        self.assertIn('tabindex="0"', html)
        self.assertIn('aria-label="Bảng định biên nhân sự;', html)
        self.assertEqual(html.count('scope="col"'), 4)
