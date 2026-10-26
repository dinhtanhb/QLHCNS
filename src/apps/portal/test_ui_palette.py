"""Ràng buộc chọn palette bằng cấu hình máy chủ (UI_PALETTE).

- Mọi thẻ <html> của template phải mang data-palette="{{ ui_palette }}".
- context processor trả đúng giá trị settings.UI_PALETTE.
- settings quy giá trị lạ về viethealth kèm cảnh báo log; mặc định = viethealth.
- ui_tokens.css thật phải vượt cổng tương phản cho CẢ 3 palette (220 cặp/palette).
"""
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, RequestFactory, override_settings

from apps.portal.context_processors import ui_palette


class UiPaletteContextTests(SimpleTestCase):
    def test_context_processor_returns_configured_palette(self):
        request = RequestFactory().get("/")
        for palette in ("viethealth", "chamdong", "thanam"):
            with override_settings(UI_PALETTE=palette):
                with self.subTest(palette=palette):
                    self.assertEqual(ui_palette(request), {"ui_palette": palette})

    def test_every_html_tag_carries_data_palette(self):
        roots = [Path(settings.BASE_DIR) / "templates"]
        for app in settings.INSTALLED_APPS:
            if not app.startswith("apps."):
                continue
            templates = Path(settings.BASE_DIR) / app.replace(".", "/") / "templates"
            if templates.is_dir():
                roots.append(templates)
        checked = []
        for root in roots:
            for template in root.rglob("*.html"):
                source = template.read_text(encoding="utf-8")
                for tag in re.findall(r"<html[^>]*>", source):
                    checked.append(str(template))
                    self.assertIn('data-palette="{{ ui_palette }}"', tag,
                                  f"Thẻ <html> thiếu data-palette trong {template}")
        self.assertTrue(checked, "Không tìm thấy thẻ <html> nào để kiểm tra")


class RepoCssContrastGateTests(SimpleTestCase):
    """Chạy chính cổng ops/check_ui_contrast.py trên ui_tokens.css thật."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ops = Path(__file__).resolve().parents[3] / "ops"
        with patch.object(sys, "path", [str(ops), *sys.path]):
            spec = importlib.util.spec_from_file_location("repo_contrast_gate", ops / "check_ui_contrast.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        cls.gate = module

    def test_repo_css_passes_gate_for_all_three_palettes(self):
        css = (Path(settings.BASE_DIR) / "static" / "css" / "ui_tokens.css").read_text(encoding="utf-8")
        blocks = self.gate.palette_blocks(css)
        self.assertEqual(set(blocks), {"viethealth", "chamdong", "thanam"})
        self.assertEqual(self.gate.fallback_mismatches(blocks), [])
        rows = self.gate.measure(blocks)
        self.assertEqual(len(rows), 660)
        for palette in ("viethealth", "chamdong", "thanam"):
            palette_rows = [row for row in rows if row[0] == palette]
            with self.subTest(palette=palette):
                self.assertEqual(len(palette_rows), 220)
                failures = [row for row in palette_rows if row[-2] < row[-1]]
                self.assertEqual(failures, [])


class UiPaletteSettingsTests(SimpleTestCase):
    """settings.UI_PALETTE đọc từ env qua tiến trình con (không reload settings)."""

    def run_settings(self, **overrides):
        root = Path(__file__).resolve().parents[2]
        env = {**os.environ, "PYTHONUTF8": "1", **overrides}
        return subprocess.run(
            [sys.executable, "-c", "import config.settings as s; print(s.UI_PALETTE)"],
            cwd=root, env=env, capture_output=True, text=True, timeout=60,
        )

    def test_default_is_viethealth(self):
        result = self.run_settings(UI_PALETTE="")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("viethealth", result.stdout)

    def test_valid_values_are_used(self):
        for value, expected in (("chamdong", "chamdong"), (" THANAM ", "thanam")):
            with self.subTest(value=value):
                result = self.run_settings(UI_PALETTE=value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, result.stdout)

    def test_invalid_value_falls_back_to_viethealth_with_warning(self):
        result = self.run_settings(UI_PALETTE="xanh-la")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("viethealth", result.stdout)
        self.assertIn("UI_PALETTE", result.stderr)
