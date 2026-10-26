"""Measure the supported token pairings using WCAG sRGB luminance (stdlib only).

python ops/check_ui_contrast.py
python ops/check_ui_contrast.py --write-doc
Reads the default palette (viethealth) and the two fallback packs (chamdong,
thanam) from src/static/css/ui_tokens.css. Every palette is measured in light
and dark, and each palette's OS-fallback block must match its dark block
exactly. Pairs outside this contract, gradients, alpha layers and rendered
pages need their own measurements. This check does not certify the application
as WCAG AA.
"""
import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "src/static/css/ui_tokens.css"
DOC = ROOT / "docs/UI_DESIGN_SYSTEM_PHASE1.md"
BEGIN = "<!-- UI_CONTRAST_BEGIN -->"
END = "<!-- UI_CONTRAST_END -->"

PALETTES = ("viethealth", "chamdong", "thanam")
PACKS = PALETTES[1:]
BODY = r"\{([^{}]+)\}"


def declarations(body):
    return dict(re.findall(r"(--ui-[\w-]+)\s*:\s*([^;]+);", body))


def _block(css, pattern, label):
    match = re.search(pattern, css)
    if not match:
        raise ValueError(f"Missing {label} block in ui_tokens.css")
    return declarations(match.group(1))


def palette_blocks(css=None):
    """Parse ui_tokens.css into {palette: {light, dark, fallback: declarations}}."""
    if css is None:
        css = TOKENS.read_text(encoding="utf-8")
    blocks = {"viethealth": {
        "light": _block(css, r':root\s*,\s*html\[data-theme="light"\]\s*' + BODY, "default light"),
        "dark": _block(css, r'(?:^|\n)\s*html\[data-theme="dark"\]\s*' + BODY, "default dark"),
        "fallback": _block(css, r'(?:^|\n)\s*:root:not\(\[data-theme\]\)\s*' + BODY, "default OS-fallback"),
    }}
    for palette in PACKS:
        blocks[palette] = {
            "light": _block(css, r'html\[data-palette="' + palette + r'"\]:root\s*' + BODY, f"{palette} pack light"),
            "dark": _block(css, r'html\[data-palette="' + palette + r'"\]\[data-theme="dark"\]\s*' + BODY, f"{palette} pack dark"),
            "fallback": _block(css, r'html\[data-palette="' + palette + r'"\]:root:not\(\[data-theme\]\)\s*' + BODY, f"{palette} pack OS-fallback"),
        }
    return blocks


def fallback_mismatches(blocks):
    """Return [(palette, token)] where a palette's OS-fallback differs from its dark."""
    mismatches = []
    for palette, themes in blocks.items():
        for name in sorted(set(themes["dark"]) | set(themes["fallback"])):
            if themes["dark"].get(name) != themes["fallback"].get(name):
                mismatches.append((palette, name))
    return mismatches


def resolve(values, name, seen=()):
    if name in seen:
        raise ValueError(f"Circular token: {name}")
    value = values[name].strip()
    alias = re.fullmatch(r"var\((--ui-[\w-]+)\)", value)
    return resolve(values, alias[1], (*seen, name)) if alias else value


def luminance(color):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError(f"Unsupported color (no silent alpha assumption): {color}")
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def ratio(foreground, background):
    low, high = sorted((luminance(foreground), luminance(background)))
    return (high + 0.05) / (low + 0.05)


def pairings():
    pairs = [("text", "divider", 3), ("warning-text", "divider", 3),
             ("chart-series", "divider", 3), ("info-text", "surface", 3),
             ("warning-text", "surface", 3)]
    for bg in ("bg", "surface", "surface-raised", "hover-bg"):
        pairs.extend((fg, bg, 4.5) for fg in ("text", "text-muted", "link"))
        pairs.extend((fg, bg, 3) for fg in ("border", "focus"))
    pairs.extend(("on-brand", bg, 4.5) for bg in ("brand", "brand-hover", "brand-active"))
    pairs.extend((("link", "brand-soft", 4.5), ("selected-text", "selected-bg", 4.5),
                  ("disabled-text", "disabled-bg", 4.5), ("disabled-border", "disabled-bg", 3),
                  ("border", "selected-bg", 3), ("focus", "selected-bg", 3)))
    for status in ("success", "warning", "danger", "info", "error"):
        pairs.extend(((status + "-text", status + "-bg", 4.5),
                      (status + "-border", status + "-bg", 3),
                      (status + "-border", "surface", 3)))
    for bg in ("sidebar-bg", "sidebar-hover-bg"):
        pairs.extend((("sidebar-text", bg, 4.5), ("sidebar-border", bg, 3), ("sidebar-focus", bg, 3)))
    pairs.extend((("sidebar-active-text", "sidebar-active-bg", 4.5),
                  ("sidebar-marker", "sidebar-active-bg", 3),
                  ("sidebar-hover-text", "sidebar-hover-bg", 4.5),
                  ("sidebar-marker", "sidebar-hover-bg", 3)))
    pairs.extend((("sidebar-muted", "sidebar-bg", 4.5), ("sidebar-focus", "sidebar-active-bg", 3)))
    for bg in ("bg", "surface", "surface-raised"):
        pairs.extend((fg, bg, 3) for fg in ("chart-series", "chart-series-soft", "chart-series-strong", "chart-grid", "chart-hire", "chart-departure", "chart-transfer", "chart-promotion"))
        pairs.extend((fg, bg, 4.5) for fg in ("chart-axis", "chart-label"))
    # Phase-one bars/donut direct labels and expiry status components.
    for series in ("chart-series", "chart-series-soft", "chart-series-strong"):
        pairs.append(("on-brand", series, 4.5))
    for status in ("danger", "warning", "info"):
        pairs.extend(((status + "-text", status + "-bg", 4.5),
                      (status + "-border", status + "-bg", 3)))
    # Phase-two bounded lists and timestamp/count text reuse the same tokens.
    pairs.extend((("text", "surface", 4.5), ("text-muted", "surface", 4.5),
                  ("link", "surface", 4.5), ("focus", "surface", 3)))
    # Refactoring UI emphasis tokens & card header tint
    pairs.extend((("brand-700", "surface", 4.5),
                  ("brand-700", "surface-tint", 4.5),
                  ("text", "surface-tint", 4.5),
                  ("text-muted", "surface-tint", 4.5),
                  ("brand-600", "surface", 3),
                  ("brand-600", "surface-tint", 3)))
    return pairs


def measure(blocks, pairs=None):
    """Return rows [(palette, theme, fg, bg, fg-color, bg-color, ratio, minimum)]."""
    pairs = pairings() if pairs is None else pairs
    rows = []
    for palette, themes in blocks.items():
        for theme in ("light", "dark"):
            values = {**themes["light"], **themes[theme]}
            for fg, bg, minimum in pairs:
                foreground = resolve(values, "--ui-" + fg)
                background = resolve(values, "--ui-" + bg)
                rows.append((palette, theme, fg, bg, foreground, background,
                             ratio(foreground, background), minimum))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-doc", action="store_true")
    args = parser.parse_args()
    blocks = palette_blocks()
    mismatches = fallback_mismatches(blocks)
    rows = measure(blocks)
    failed = [row for row in rows if row[-2] < row[-1]]
    if args.write_doc:
        header = "| Palette | Theme | Chữ/UI | Nền | Màu trước | Màu nền | Tỷ lệ | Ngưỡng | Kết quả |\n|---|---|---|---|---|---|---:|---:|---|\n"
        table = header + "".join(f"| {palette} | {theme} | `--ui-{fg}` | `--ui-{bg}` | `{front}` | `{back}` | {actual:.3f}:1 | {minimum:g}:1 | {'Đạt' if actual >= minimum else 'Không đạt'} |\n" for palette, theme, fg, bg, front, back, actual, minimum in rows)
        text = DOC.read_text(encoding="utf-8")
        section = BEGIN + "\n" + table + END
        if BEGIN in text and END in text:
            start = text.index(BEGIN)
            stop = text.index(END, start) + len(END)
            text = text[:start] + section + text[stop:]
        else:
            text += "\n\n" + section + "\n"
        DOC.write_text(text, encoding="utf-8")
    for palette in PALETTES:
        for theme in ("light", "dark"):
            subset = [row for row in rows if row[0] == palette and row[1] == theme]
            print(f"{palette}/{theme}: {len(subset)} pairs; min text={min(r[-2] for r in subset if r[-1] == 4.5):.3f}:1; min UI={min(r[-2] for r in subset if r[-1] == 3):.3f}:1")
    print(f"{len(rows)} pairs; failures={len(failed)}; fallback mismatches={len(mismatches)}; rendered/alpha layers not certified.")
    for row in failed:
        print("FAIL:", row)
    for palette, name in mismatches:
        print(f"FALLBACK MISMATCH: {palette} {name}")
    return bool(failed or mismatches)


if __name__ == "__main__":
    raise SystemExit(main())
