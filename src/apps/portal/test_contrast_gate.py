"""Tests for ops/check_ui_contrast.py (the palette contrast gate itself)."""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

from django.test import SimpleTestCase


LIGHT = "--ui-bg: #e7ecf4; --ui-text: #101828; --ui-brand: #3a4fd0;"
DARK = "--ui-bg: #080c18; --ui-text: #eef2ff; --ui-brand: #93a7ff;"


def synthetic_css(dark=None, fallback=None, pack_fallback=None, packs=True):
    dark = DARK if dark is None else dark
    fallback = dark if fallback is None else fallback
    pack_fallback = dark if pack_fallback is None else pack_fallback
    css = [
        ":root,",
        'html[data-theme="light"] {',
        LIGHT,
        "}",
        'html[data-theme="dark"] {',
        dark,
        "}",
        "@media screen and (prefers-color-scheme: dark) {",
        ":root:not([data-theme]) {",
        fallback,
        "}",
        "}",
    ]
    if packs:
        for palette in ("chamdong", "thanam"):
            css += [
                f'html[data-palette="{palette}"]:root {{',
                LIGHT,
                "}",
                f'html[data-palette="{palette}"][data-theme="dark"] {{',
                dark,
                "}",
                f'html[data-palette="{palette}"]:root:not([data-theme]) {{',
                pack_fallback,
                "}",
            ]
    return "\n".join(css)


class ContrastGateToolTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ops = Path(__file__).resolve().parents[3] / "ops"
        with patch.object(sys, "path", [str(ops), *sys.path]):
            spec = importlib.util.spec_from_file_location("contrast_gate_under_test", ops / "check_ui_contrast.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        cls.gate = module

    def test_ratio_extremes(self):
        self.assertAlmostEqual(self.gate.ratio("#000000", "#ffffff"), 21.0)
        self.assertAlmostEqual(self.gate.ratio("#ffffff", "#ffffff"), 1.0)

    def test_resolve_follows_alias(self):
        values = {"--ui-bg": "#ffffff", "--ui-brand": "#3a4fd0",
                  "--ui-chart-series": "var(--ui-brand)"}
        self.assertEqual(self.gate.resolve(values, "--ui-chart-series"), "#3a4fd0")

    def test_all_three_palettes_parse_light_dark_and_fallback(self):
        blocks = self.gate.palette_blocks(synthetic_css())
        self.assertEqual(set(blocks), {"viethealth", "chamdong", "thanam"})
        for themes in blocks.values():
            self.assertEqual(set(themes), {"light", "dark", "fallback"})
            self.assertEqual(themes["light"]["--ui-bg"], "#e7ecf4")
            self.assertEqual(themes["dark"]["--ui-bg"], "#080c18")

    def test_missing_pack_block_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "pack light"):
            self.gate.palette_blocks(synthetic_css(packs=False))

    def test_fallback_equal_to_dark_passes(self):
        blocks = self.gate.palette_blocks(synthetic_css())
        self.assertEqual(self.gate.fallback_mismatches(blocks), [])

    def test_one_offset_default_token_is_reported(self):
        offset = DARK.replace("--ui-bg: #080c18", "--ui-bg: #080c19")
        blocks = self.gate.palette_blocks(synthetic_css(fallback=offset))
        self.assertEqual(self.gate.fallback_mismatches(blocks), [("viethealth", "--ui-bg")])

    def test_one_offset_pack_token_is_reported_per_pack(self):
        offset = DARK.replace("--ui-text: #eef2ff", "--ui-text: #eef2fe")
        blocks = self.gate.palette_blocks(synthetic_css(pack_fallback=offset))
        self.assertEqual(self.gate.fallback_mismatches(blocks),
                         [("chamdong", "--ui-text"), ("thanam", "--ui-text")])

    def test_measure_covers_every_palette_and_theme(self):
        blocks = self.gate.palette_blocks(synthetic_css())
        rows = self.gate.measure(blocks, pairs=[("text", "bg", 4.5), ("brand", "bg", 3)])
        self.assertEqual(len(rows), 12)
        self.assertEqual({(row[0], row[1]) for row in rows},
                         {(p, t) for p in ("viethealth", "chamdong", "thanam") for t in ("light", "dark")})
        for row in rows:
            self.assertGreaterEqual(row[-2], row[-1], row)

    def test_failing_pair_is_reported(self):
        blocks = self.gate.palette_blocks(synthetic_css())
        rows = self.gate.measure(blocks, pairs=[("text", "brand", 4.5)])
        # #101828 text on #3a4fd0 brand in light is far below 4.5:1.
        self.assertLess(rows[0][-2], rows[0][-1])
