"""Mobile shell must opt in to tab navigation at its existing breakpoint."""
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class TabbarVisibilityTests(SimpleTestCase):
    def test_tabbar_has_a_hidden_default_before_mobile_breakpoint(self):
        css = (Path(settings.BASE_DIR) / 'static/css/mobile_shell.css').read_text(encoding='utf-8')
        default = css.split('@media screen and (max-width: 1023px)', 1)[0]
        self.assertRegex(default, r'\.ui-tabbar\s*\{[^}]*display\s*:\s*none\s*;')
        mobile = css.split('@media screen and (max-width: 1023px)', 1)[1]
        self.assertRegex(mobile, r'\.ui-tabbar\s*\{[^}]*display\s*:\s*grid\s*;')
