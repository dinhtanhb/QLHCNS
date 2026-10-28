"""Screen layout contracts; geometry/scroll/zoom are exercised in Edge."""
from html.parser import HTMLParser
from pathlib import Path

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from apps.portal.test_visual_consistency import audit


ROOT = Path(__file__).resolve().parents[3]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.nodes.append((tag, attrs, tuple(self.stack)))
        if tag not in ('input', 'br', 'hr', 'img', 'meta', 'link', 'path', 'circle'):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ('path', 'circle'):
            return
        if not self.stack or self.stack[-1] != tag:
            raise AssertionError(f'Unbalanced {tag}: {self.stack}')
        self.stack.pop()


class HeaderReportLayoutTests(SimpleTestCase):
    def test_kpi_link_label_number_and_metadata_remain_in_one_card(self):
        html = render_to_string('ui/kpi.html', dict(
            label='Nhãn dài cần xuống dòng', value=1234567, period='nhân viên',
            href='/portal/reports/?from_date=2026-01-01', warning=True))
        parser = Markup()
        parser.feed(html)
        self.assertEqual(parser.stack, [])
        self.assertEqual(parser.nodes[0][0], 'a')
        self.assertEqual(parser.nodes[0][1]['href'], '/portal/reports/?from_date=2026-01-01')
        self.assertIn('ui-kpi-heading', html)
        self.assertIn('ui-kpi-symbol', html)
        self.assertIn('ui-kpi-meta', html)
        self.assertIn('Nhãn dài cần xuống dòng', html)
        self.assertIn('1.234.567', html)
        self.assertIn('Cần xử lý', html)

    def test_zero_does_not_gain_a_warning_and_missing_value_keeps_its_label(self):
        zero = render_to_string('ui/kpi.html', dict(label='Zero', value=0, danger=True))
        missing = render_to_string('ui/kpi.html', dict(label='Missing', value=None))
        self.assertNotIn('ui-kpi--danger', zero)
        self.assertNotIn('Cần xử lý', zero)
        self.assertIn('Chưa có dữ liệu', missing)

    def test_persistent_topbar_and_reservation_apply_only_to_screen(self):
        css = (ROOT/'src/static/css/app_shell.css').read_text(encoding='utf-8')
        blocks = list(audit.css_blocks(css))
        fixed = [(ctx, body) for ctx, body in blocks
                 if ctx[-1] == '.ui-topbar' and 'position:fixed' in body]
        self.assertEqual(len(fixed), 1)
        self.assertTrue(any('@media screen' in item for item in fixed[0][0]))
        self.assertTrue(any(ctx[-1] == '.portal-app' and
                            'padding-block-start:var(--ui-shell-header-height)' in body
                            and any('@media screen' in item for item in ctx)
                            for ctx, body in blocks))

    def test_section_bar_keeps_background_border_and_compact_padding(self):
        css = (ROOT/'src/static/css/components.css').read_text(encoding='utf-8')
        blocks = [(ctx, body) for ctx, body in audit.css_blocks(css)
                  if ctx[-1] == '.ui-section-header']
        self.assertTrue(any('background:var(--ui-surface)' in body and
                            'var(--ui-border-subtle)' in body and
                            'padding:var(--ui-space-1) var(--ui-space-6)' in body
                            for _, body in blocks))

    def test_shared_kpi_tracks_are_screen_only_and_paper_metadata_is_flat(self):
        blocks = list(audit.css_blocks((ROOT/'src/static/css/components.css').read_text(encoding='utf-8')))
        shared = [(ctx, body) for ctx, body in blocks if ctx[-1] == '.ui-kpi-grid>.ui-kpi']
        self.assertEqual(len(shared), 1)
        self.assertIn('@media screen', shared[0][0])
        self.assertIn('grid-template-rows:subgrid', shared[0][1])
        self.assertTrue(any(ctx[-1] == '.ui-kpi-meta' and 'display:contents' in body
                            for ctx, body in blocks))

    def test_report_uses_actual_kpi_container_and_keeps_get_and_export_fields(self):
        source = (ROOT/'src/apps/portal/templates/portal/report_hub.html').read_text(encoding='utf-8')
        self.assertIn('class="report-kpis"', source)
        self.assertIn('method="get"', source)
        for field in ('from_date', 'to_date'):
            self.assertIn(f'name="{field}"', source)
        for kind in ('xlsx', 'docx', 'pptx'):
            self.assertIn(f"'portal:report_hub_export' '{kind}'", source)
        self.assertEqual(source.count('with label='), 6)

    def test_report_spacing_and_column_breakpoints_target_live_controls(self):
        css = (ROOT/'src/static/css/report_dashboard.css').read_text(encoding='utf-8')
        blocks = list(audit.css_blocks(css))
        self.assertTrue(any(ctx[-1] == '.report-toolbar .ui-query-bar--date-echo :is(.ui-field,.ui-query-actions)'
                            and '@media screen' in ctx
                            and 'margin-bottom:var(--ui-report-echo-reserve,' in body
                            for ctx, body in blocks))
        for width, columns in ((23, 2), (35, 3), (71, 6)):
            self.assertTrue(any(f'@container report-kpis (min-width:{width}rem)' in ctx
                                and ctx[-1] == '.report-kpis>.ui-kpi-grid'
                                and f'repeat({columns},minmax(0,1fr))' in body
                                for ctx, body in blocks))
