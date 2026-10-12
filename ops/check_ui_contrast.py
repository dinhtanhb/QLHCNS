"""Measure the supported token pairings using WCAG sRGB luminance (stdlib only).

python ops/check_ui_contrast.py
python ops/check_ui_contrast.py --write-doc
Pairs outside this contract, gradients, alpha layers and rendered pages need
their own measurements. This check does not certify the application as WCAG AA.
"""
import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "src/static/css/ui_tokens.css"
DOC = ROOT / "docs/UI_DESIGN_SYSTEM_PHASE1.md"
BEGIN = "<!-- UI_CONTRAST_BEGIN -->"
END = "<!-- UI_CONTRAST_END -->"


def declarations(body):
    return dict(re.findall(r"(--ui-[\w-]+)\s*:\s*([^;]+);", body))


def palettes():
    css = TOKENS.read_text(encoding="utf-8")
    light = declarations(re.search(r'html\[data-theme="light"\]\s*\{([^}]+)', css).group(1))
    dark = {**light, **declarations(re.search(r'html\[data-theme="dark"\]\s*\{([^}]+)', css).group(1))}
    return {"light": light, "dark": dark}


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
    pairs = []
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
        pairs.extend((("sidebar-text", bg, 4.5), ("sidebar-border", bg, 3), ("focus", bg, 3)))
    pairs.extend((("sidebar-active-text", "sidebar-active-bg", 4.5),
                  ("sidebar-marker", "sidebar-active-bg", 3),
                  ("sidebar-hover-text", "sidebar-hover-bg", 4.5),
                  ("sidebar-marker", "sidebar-hover-bg", 3)))
    for bg in ("bg", "surface", "surface-raised"):
        pairs.extend((fg, bg, 3) for fg in ("chart-series", "chart-series-soft", "chart-series-strong", "chart-grid"))
        pairs.extend((fg, bg, 4.5) for fg in ("chart-axis", "chart-label"))
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-doc", action="store_true")
    args = parser.parse_args()
    rows = []
    for theme, values in palettes().items():
        for fg, bg, minimum in pairings():
            foreground = resolve(values, "--ui-" + fg)
            background = resolve(values, "--ui-" + bg)
            actual = ratio(foreground, background)
            rows.append((theme, fg, bg, foreground, background, actual, minimum))
    failed = [row for row in rows if row[-2] < row[-1]]
    if args.write_doc:
        header = "| Theme | Chữ/UI | Nền | Màu trước | Màu nền | Tỷ lệ | Ngưỡng | Kết quả |\n|---|---|---|---|---|---:|---:|---|\n"
        table = header + "".join(f"| {theme} | `--ui-{fg}` | `--ui-{bg}` | `{front}` | `{back}` | {actual:.3f}:1 | {minimum:g}:1 | {'Đạt' if actual >= minimum else 'Không đạt'} |\n" for theme, fg, bg, front, back, actual, minimum in rows)
        text = DOC.read_text(encoding="utf-8")
        section = BEGIN + "\n" + table + END
        if BEGIN in text and END in text:
            start = text.index(BEGIN)
            stop = text.index(END, start) + len(END)
            text = text[:start] + section + text[stop:]
        else:
            text += "\n\n" + section + "\n"
        DOC.write_text(text, encoding="utf-8")
    for theme in ("light", "dark"):
        subset = [row for row in rows if row[0] == theme]
        print(f"{theme}: {len(subset)} pairs; min text={min(r[-2] for r in subset if r[-1] == 4.5):.3f}:1; min UI={min(r[-2] for r in subset if r[-1] == 3):.3f}:1")
    print(f"{len(rows)} pairs; failures={len(failed)}; rendered/alpha layers not certified.")
    for row in failed:
        print("FAIL:", row)
    return bool(failed)


if __name__ == "__main__":
    raise SystemExit(main())
