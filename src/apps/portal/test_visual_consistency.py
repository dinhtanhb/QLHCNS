"""CI checks for the authored UI rules; Edge checks geometry separately."""
import importlib.util
from pathlib import Path
import re
import tempfile

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    'visual_consistency', ROOT / 'ops/run_visual_consistency_audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class VisualConsistencyTests(SimpleTestCase):
    def test_authored_ui_uses_tokens_and_decorative_css_arrows(self):
        self.assertEqual(audit.lint_source(ROOT), [])

    def test_nested_screen_literal_is_rejected_with_context(self):
        result = audit.literal_font_sizes('''/* { font-size: 2px } */
            @layer pages { @media screen and (min-width: 20rem) {
              .card::after { content: "}"; font-size: 18px; }
            }}''')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], '18px')
        self.assertIn('@media screen', result[0]['context'])
        self.assertIn('.card::after', result[0]['context'])

    def test_print_geometry_is_excluded_but_screen_points_are_rejected(self):
        self.assertEqual(audit.literal_font_sizes('''
            @media print { .paper { font-size: 12pt; } }
            .hcns-signatures { font-size: 11pt; }
            .screen { font-size: 11pt; }
        '''), [{'context': '.screen', 'value': '11pt'}])

    def test_token_and_inherited_sizes_are_allowed(self):
        self.assertEqual(audit.literal_font_sizes('''
            .card { font-size: var(--ui-type-card); }
            .child { font-size: inherit; }
        '''), [])

    def test_arrow_label_negative_control_includes_nested_markup(self):
        self.assertEqual(len(audit.arrow_labels(
            '<a href="/allowed/"><span>Mở lịch</span> \u2192</a>')), 1)
        self.assertEqual(len(audit.arrow_labels('<button>Tiếp \u2192</button>')), 1)
        self.assertEqual(audit.arrow_labels(
            '<!-- <a>not rendered \u2192</a> --><p>A \u2192 B</p>'), [])

    def test_lint_finds_inline_template_literal_and_label(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'src/static/css').mkdir(parents=True)
            templates = root / 'src/templates'
            templates.mkdir()
            (root / 'src/apps').mkdir()
            (templates / 'bad.html').write_text(
                '<a style="font-size:18px">Mở \u2192</a>', encoding='utf-8')
            errors = audit.lint_source(root)
            self.assertEqual(len(errors), 2)
            self.assertTrue(any(error.get('value') == '18px' for error in errors))
            self.assertTrue(any('label' in error for error in errors))

    def test_dashboard_uses_common_header_and_link_families(self):
        directory = ROOT / 'src/apps/portal/templates/portal/dashboard'
        text = '\n'.join(path.read_text(encoding='utf-8') for path in directory.glob('*.html'))
        self.assertNotRegex(text, r'home-(?:card-header|group-header|text-link|header-actions)')
        self.assertIn('ui-section-header', text)
        self.assertIn('ui-card-header', text)
        self.assertIn('ui-link-action', text)
        for name in ('_my_work.html','_group_hr.html','_group_projects.html',
                     '_group_admin.html','_group_recruitment.html'):
            self.assertEqual((directory / name).read_text(encoding='utf-8').count('class="ui-section-content"'), 1, name)

    def test_screen_type_family_has_exactly_six_roles(self):
        text = (ROOT / 'src/static/css/ui_tokens.css').read_text(encoding='utf-8')
        roles = dict(re.findall(r'--ui-type-(\w+)\s*:\s*([\d.]+rem)', text))
        self.assertEqual(roles, dict(page='1.5rem', group='1.25rem', card='1rem',
                                     body='.875rem', kpi='2.25rem', stat='1.5rem'))
        self.assertIn('@media screen and (min-width:770px) and (pointer:fine)', text)

    def test_density_tokens_are_bound_to_screen_table_rows(self):
        text = (ROOT / 'src/static/css/components.css').read_text(encoding='utf-8')
        bindings = [(context, body) for context, body in audit.css_blocks(text)
                    if '.ui-table :is(thead,tbody) tr' in context[-1]]
        self.assertEqual(len(bindings), 1)
        context, body = bindings[0]
        self.assertIn('@media screen', context)
        self.assertRegex(body, r'block-size:\s*var\(--ui-table-row-min\)')
