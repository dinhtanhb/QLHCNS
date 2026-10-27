"""CI guard for installed Django submit colors and the screen-only admin fix.

Unknown color syntax fails closed so dependency upgrades require review rather
than silently omitting a declaration. No browser, QA database or ops imports.
"""
from pathlib import Path
import re

import django.contrib.admin
from django.conf import settings
from django.test import SimpleTestCase


VARIABLES = (
    '--delete-button-bg', '--delete-button-hover-bg',
    '--close-button-bg', '--close-button-hover-bg',
)
DECLARATION = re.compile(r'(--[\w-]+)\s*:\s*([^;{}]+)(?:;|$)')


def css_blocks(source, parents=()):
    """Yield every declaration block with its enclosing selector/media path."""
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
    cursor = 0
    while cursor < len(source):
        opening = source.find('{', cursor)
        if opening < 0:
            return
        # Ignore preceding @import statements when naming the next block.
        header = source[cursor:opening].rsplit(';', 1)[-1].strip()
        depth, end = 1, opening + 1
        while end < len(source) and depth:
            depth += (source[end] == '{') - (source[end] == '}')
            end += 1
        if depth:
            raise AssertionError(f'Unbalanced CSS block: {header}')
        body = source[opening + 1:end - 1]
        path = (*parents, header)
        # Grouping rules have children, not declarations. Recurse without
        # assigning nested declarations to the enclosing media block as well.
        if '{' in body:
            yield from css_blocks(body, path)
        else:
            yield path, body
        cursor = end


def luminance(color):
    color = re.sub(r'\s*!important\s*$', '', color, flags=re.I).strip().lower()
    if color == 'white':
        color = '#ffffff'
    if not re.fullmatch(r'#[0-9a-f]{3}(?:[0-9a-f]{3})?', color):
        raise ValueError(f'Unsupported opaque CSS color: {color}')
    digits = color[1:]
    if len(digits) == 3:
        digits = ''.join(channel * 2 for channel in digits)
    channels = [int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
    return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))


def contrast(foreground, background):
    a, b = sorted((luminance(foreground), luminance(background)))
    return (b + .05) / (a + .05)


def assert_background_contrast(sources):
    seen = set()
    for filename, source in sources.items():
        for path, body in css_blocks(source):
            for variable, value in DECLARATION.findall(body):
                if variable not in VARIABLES:
                    continue
                seen.add(variable)
                block = filename + ' > ' + ' > '.join(path)
                try:
                    ratio = contrast('white', value)
                except ValueError as error:
                    raise AssertionError(f'{variable}={value}; ratio=unresolved; block={block}: {error}') from error
                if ratio < 4.5:
                    raise AssertionError(f'{variable}={value}; ratio={ratio:.4f}:1 < 4.5:1; block={block}')
    missing = set(VARIABLES) - seen
    if missing:
        raise AssertionError(f'{sorted(missing)}; value=<missing>; ratio=unresolved; block=<none>')


def assert_admin_contract(source):
    brand_rules, white_screen_rules = [], []
    brand_selector = re.compile(r':is\s*\([^)]*\.app-main\b[^)]*\)\s+a\b', re.S)
    white_selector = re.compile(
        r'\.submit-row\s+a\s*:is\s*\(\s*'
        r'(?:\.deletelink\s*,\s*\.closelink|\.closelink\s*,\s*\.deletelink)'
        r'\s*\)\s*:any-link\b', re.S,
    )
    for path, body in css_blocks(source):
        # Ordinary properties intentionally allow any order and whitespace.
        colors = re.findall(r'(?:^|;)\s*color\s*:\s*([^;]+)(?:;|$)', body, re.I)
        selector = path[-1]
        if brand_selector.search(selector) and any(re.fullmatch(r'var\(\s*--ui-link\s*\)', c.strip()) for c in colors):
            brand_rules.append(path)
            for name in ('deletelink', 'closelink'):
                if not re.search(r':not\s*\(\s*\.' + name + r'\s*\)', selector):
                    raise AssertionError(f'Brand link rule missing :not(.{name}): {path}')
        if white_selector.search(selector):
            in_screen = any(re.match(r'@media\b', p) and re.search(r'\bscreen\b', p) and not re.search(r'\bprint\b', p) for p in path[:-1])
            if in_screen and colors:
                try:
                    is_white = luminance(colors[-1]) == 1.0
                except ValueError:
                    is_white = False
                if is_white:
                    white_screen_rules.append(path)
    if not brand_rules:
        raise AssertionError('Missing brand link rule using var(--ui-link)')
    if not white_screen_rules:
        raise AssertionError('Missing white .submit-row Delete/Close :any-link rule inside @media screen')


class AdminActionContrastTests(SimpleTestCase):
    @staticmethod
    def admin_css():
        return (Path(settings.BASE_DIR) / 'static/css/admin.css').read_text(encoding='utf-8')

    @staticmethod
    def backgrounds():
        return ':root {' + ''.join(f'{name}: #333;' for name in VARIABLES) + '}'

    def test_wcag_known_pairs(self):
        self.assertEqual(round(contrast('white', '#ba2121'), 4), 6.3114)
        self.assertEqual(round(contrast('white', '#747474'), 4), 4.6740)
        self.assertEqual(contrast('#000', '#fff'), 21)

    def test_all_installed_django_action_backgrounds(self):
        css = Path(django.contrib.admin.__file__).parent / 'static/admin/css'
        # Read Django's own files, never a project/staticfinder override.
        sources = {'base.css': (css / 'base.css').read_text(encoding='utf-8')}
        if (css / 'dark_mode.css').is_file():
            sources['dark_mode.css'] = (css / 'dark_mode.css').read_text(encoding='utf-8')
        assert_background_contrast(sources)

    def test_admin_css_exclusions_and_screen_white_foreground(self):
        assert_admin_contract(self.admin_css())

    def test_parser_keeps_all_light_dark_auto_declarations_and_ignores_comments(self):
        source = self.backgrounds() + '''
        /* --close-button-bg: #fff; } */
        @media (prefers-color-scheme: dark) {
          :root { --close-button-bg: #333; }
        }
        html[data-theme="dark"] { --close-button-bg: #666; }
        '''
        blocks = list(css_blocks(source))
        self.assertEqual(len(blocks), 3)
        self.assertIn('@media (prefers-color-scheme: dark)', blocks[1][0])
        self.assertEqual(sum(name == '--close-button-bg' for _, body in blocks for name, _ in DECLARATION.findall(body)), 3)
        assert_background_contrast({'fixture.css': source})

    def test_missing_variable_fails(self):
        source = self.backgrounds().replace('--close-button-hover-bg: #333;', '')
        with self.assertRaisesRegex(AssertionError, '--close-button-hover-bg.*missing'):
            assert_background_contrast({'fixture.css': source})

    def test_negative_removed_delete_exclusion(self):
        source = self.admin_css()
        broken, count = re.subn(r':not\(\.deletelink\)', '', source)
        self.assertGreater(count, 0)
        with self.assertRaisesRegex(AssertionError, r'missing :not\(\.deletelink\)'):
            assert_admin_contract(broken)

    def test_negative_white_changed_to_brand(self):
        broken, count = re.subn(r'color\s*:\s*white\s*;', 'color:var(--ui-link);', self.admin_css())
        self.assertGreater(count, 0)
        with self.assertRaisesRegex(AssertionError, 'Missing white'):
            assert_admin_contract(broken)

    def test_negative_low_contrast_nested_override(self):
        source = self.backgrounds() + '@media (prefers-color-scheme: dark) { :root { --close-button-bg: #aaa; }}'
        with self.assertRaisesRegex(AssertionError, r'--close-button-bg=#aaa; ratio=.*block=fixture.css > @media.*:root'):
            assert_background_contrast({'fixture.css': source})

    def test_css_contract_accepts_whitespace_newlines_and_property_order(self):
        source = '''@media screen {
          :is( .app-main, .timeline, .login-page )
            a:not( .deletelink ):not( .closelink ) { border: 0; color : var( --ui-link ); }
          :root[data-theme] .submit-row a:is(
              .closelink, .deletelink
          ):any-link { background: inherit; color: #fff; padding: 0; }
        }'''
        assert_admin_contract(source)
