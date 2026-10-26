"""Hàng rào chống lệch giữa bảng màu Python và token CSS.

Hai module báo cáo giữ bảng màu riêng vì thư viện pptx/openpyxl cần mã hex, không
đọc được biến CSS. Một nguồn Python duy nhất ở report_palette.py, sao chép khối
light của ui_tokens.css cho palette đang cấu hình (UI_PALETTE). Test này chạy cho
CẢ 3 palette và so với token CSS của từng pack: đổi `ui_tokens.css` mà quên bảng
kia sẽ đỏ ngay, thay vì phát hiện khi người dùng mở báo cáo ra thấy màu cũ.
"""
import re
from importlib import reload
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from apps.portal import report_palette, reporting_dashboard, reporting_slides


PALETTES = ("viethealth", "chamdong", "thanam")

# Tên hằng trong bảng Python ← tên token CSS (bỏ tiền tố --ui-).
CONSTANT_TO_TOKEN = {
    "NAVY": "text",
    "TEAL": "brand",
    "MINT": "brand-soft",
    "PAPER": "bg",
    "MUTED": "text-muted",
    "LINE": "card-border",
    "RED": "danger-text",
    "AMBER": "warning-text",
    "BLUE": "info-text",
}

# Selector khối light của từng pack, neo kèm dấu `{` để không dính khối
# OS-fallback (`:root:not([data-theme])`) hay selector pack dark cùng tên.
LIGHT_PATTERN = {
    "viethealth": r'html\[data-theme="light"\]\s*\{([^{}]+)\}',
    "chamdong": r'html\[data-palette="chamdong"\]:root\s*\{([^{}]+)\}',
    "thanam": r'html\[data-palette="thanam"\]:root\s*\{([^{}]+)\}',
}


def light_tokens(palette):
    css = (Path(settings.BASE_DIR) / "static" / "css" / "ui_tokens.css").read_text(encoding="utf-8")
    match = re.search(LIGHT_PATTERN[palette], css)
    if not match:
        raise AssertionError(f"Không tìm thấy khối light của pack {palette} trong ui_tokens.css")
    return {
        name: value.removeprefix("#").upper()
        for name, value in re.findall(r"--ui-([\w-]+):\s*(#[0-9a-fA-F]{6})", match.group(1))
    }


class ReportPaletteTests(SimpleTestCase):
    def tearDown(self):
        # Trả module về palette mặc định để không làm nhiễu test khác cùng tiến trình.
        with override_settings(UI_PALETTE="viethealth"):
            reload(report_palette)
            reload(reporting_slides)
            reload(reporting_dashboard)

    def test_python_table_matches_css_for_every_pack(self):
        for palette in PALETTES:
            tokens = light_tokens(palette)
            for name, token in CONSTANT_TO_TOKEN.items():
                with self.subTest(palette=palette, constant=name):
                    self.assertEqual(report_palette.PALETTES[palette][name], tokens[token])

    def test_slides_follow_the_configured_palette(self):
        for palette in PALETTES:
            with override_settings(UI_PALETTE=palette):
                reload(report_palette)
                reload(reporting_slides)
                tokens = light_tokens(palette)
                for name, token in CONSTANT_TO_TOKEN.items():
                    with self.subTest(palette=palette, constant=name):
                        self.assertEqual(getattr(reporting_slides, name), tokens[token])

    def test_excel_follows_the_configured_palette(self):
        for palette in PALETTES:
            with override_settings(UI_PALETTE=palette):
                reload(report_palette)
                reload(reporting_dashboard)
                tokens = light_tokens(palette)
                expected = {
                    "BLUE": tokens["brand"],
                    "DARK": tokens["text"],
                    "LIGHT": tokens["brand-soft"],
                    "MUTED": tokens["text-muted"],
                }
                for name, value in expected.items():
                    with self.subTest(palette=palette, constant=name):
                        self.assertEqual(getattr(reporting_dashboard, name), value)

    def test_invalid_palette_falls_back_to_default(self):
        # settings.py đã quy giá trị lạ về mặc định kèm cảnh báo log; đây kiểm
        # lớp phòng hộ của report_palette khi nhận giá trị ngoài danh sách.
        with override_settings(UI_PALETTE="xanh-la"):
            reload(report_palette)
            self.assertIs(report_palette.active(), report_palette.PALETTES["viethealth"])

    def test_neutral_colors_shared_across_palettes(self):
        self.assertEqual(report_palette.WHITE, "FFFFFF")
        self.assertEqual(report_palette.GRID, "CBD5E1")

    def test_no_hex_literal_survives_in_export_modules(self):
        # Mọi mã hex phải nằm ở report_palette.py — một nguồn duy nhất.
        for module in (reporting_slides, reporting_dashboard):
            with self.subTest(module=module.__name__):
                source = Path(module.__file__).read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"#[0-9a-fA-F]{6}", source))
