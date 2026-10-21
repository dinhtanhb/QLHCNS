"""Bản xuất PowerPoint/Excel phải dùng đúng palette Chàm Đông của giao diện.

Hai module báo cáo giữ bảng màu riêng vì thư viện pptx/openpyxl cần mã hex, không
đọc được biến CSS. Test này là hàng rào chống lệch: đổi `ui_tokens.css` mà quên
hai tệp kia sẽ đỏ ngay, thay vì phát hiện khi người dùng mở báo cáo ra thấy teal.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from apps.portal import reporting_dashboard, reporting_slides


def light_tokens():
    css = (Path(settings.BASE_DIR) / "static" / "css" / "ui_tokens.css").read_text(encoding="utf-8")
    start = css.index('html[data-theme="light"]')
    block = css[start:css.index("\n}", start)]
    return {name: value.upper() for name, value in re.findall(r"--ui-([\w-]+):\s*(#[0-9a-fA-F]{6})", block)}


class ReportPaletteTests(SimpleTestCase):
    def test_slides_use_the_interface_palette(self):
        tokens = light_tokens()
        expected = {
            "NAVY": tokens["text"],
            "TEAL": tokens["brand"],
            "MINT": tokens["brand-soft"],
            "PAPER": tokens["bg"],
            "MUTED": tokens["text-muted"],
            "LINE": tokens["card-border"],
            "RED": tokens["danger-text"],
            "AMBER": tokens["warning-text"],
            "BLUE": tokens["info-text"],
        }
        for name, value in expected.items():
            with self.subTest(constant=name):
                self.assertEqual(getattr(reporting_slides, name), value.removeprefix("#"))

    def test_excel_export_uses_the_interface_palette(self):
        tokens = light_tokens()
        expected = {
            "BLUE": tokens["brand"],
            "DARK": tokens["text"],
            "LIGHT": tokens["brand-soft"],
            "MUTED": tokens["text-muted"],
        }
        for name, value in expected.items():
            with self.subTest(constant=name):
                self.assertEqual(getattr(reporting_dashboard, name), value.removeprefix("#"))

    def test_no_teal_survives_in_export_modules(self):
        for module in (reporting_slides, reporting_dashboard):
            with self.subTest(module=module.__name__):
                source = Path(module.__file__).read_text(encoding="utf-8")
                for legacy in ("0B7461", "63DBC2", "DDF3EB", "F4F7F5", "1D4ED8", "EFF6FF"):
                    self.assertNotIn(legacy, source.upper())
