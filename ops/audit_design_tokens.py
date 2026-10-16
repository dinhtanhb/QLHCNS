"""Static audit tool for design tokens, CSS architecture, and visual hierarchy.

Scans all project CSS files and templates, producing JSON and Markdown reports.
Exits with non-zero code if thresholds are exceeded (when run with --check).
"""
import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Paths to scan (screen CSS; print and vendor stylesheets excluded from screen token audit)
EXCLUDE_CSS = {"tailwind.css", "admin.css", "print_forms.css", "hcns_forms.css"}
ALLOWED_TYPE_SCALE_PX = {14, 16, 18, 20, 24, 30, 36, 48, 60, 72}
ALLOWED_TYPE_SCALE_REM = {0.875, 1.0, 1.125, 1.25, 1.5, 1.875, 2.25, 3.0, 3.75, 4.5}
ALLOWED_SPACING_PX = {0, 1, 2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 640, 768}


def parse_css_file(file_path):
    content = file_path.read_text(encoding="utf-8")
    # Strip comments
    content_no_comments = re.sub(r"/\*[\s\S]*?\*/", "", content)
    return content, content_no_comments


def audit_tokens(repo_root):
    css_dir = repo_root / "src" / "static" / "css"
    templates_dir = repo_root / "src" / "templates"
    apps_dir = repo_root / "src" / "apps"

    css_files = [
        f for f in css_dir.glob("*.css")
        if f.name not in EXCLUDE_CSS
    ]

    report = {
        "css_file_count": len(css_files),
        "css_total_bytes": sum(f.stat().st_size for f in css_files),
        "important_count": 0,
        "important_locations": [],
        "portal_app_ui_main_count": 0,
        "id_selectors_count": 0,
        "has_selectors_count": 0,
        "hex_outside_tokens": [],
        "em_in_font_size": [],
        "distinct_font_sizes": set(),
        "off_scale_font_sizes": set(),
        "distinct_paddings": set(),
        "distinct_gaps": set(),
        "distinct_radii": set(),
        "component_definitions": {
            "ui-button": [],
            "ui-field": [],
            "ui-card": [],
            "ui-badge": [],
            "ui-table": [],
        },
        "template_inline_styles": 0,
        "template_style_locations": [],
    }

    # 1. Scan CSS
    for css_file in css_files:
        rel_path = css_file.relative_to(repo_root).as_posix()
        is_tokens_file = css_file.name in ("ui_tokens.css", "design_tokens.css")
        raw, text = parse_css_file(css_file)

        # Count !important
        for match in re.finditer(r"([^{};]+:[^{};]+!important;?)", text, re.I):
            report["important_count"] += 1
            prop_str = match.group(1).strip()
            # find line number
            line_no = raw[:match.start()].count("\n") + 1
            report["important_locations"].append(f"{rel_path}:{line_no} ({prop_str[:60]})")

        # Selectors tethered to .portal-app .ui-main
        matches = re.findall(r"\.portal-app\s+\.ui-main", text)
        report["portal_app_ui_main_count"] += len(matches)

        # ID selectors in rules
        # Matches #ident followed by space, comma, {, :, etc.
        id_matches = re.findall(r"(?<![a-fA-F0-9])#([a-zA-Z][a-zA-Z0-9_-]*)\b(?![^{]*})", text)
        report["id_selectors_count"] += len(id_matches)

        # Fragile :has()
        has_matches = re.findall(r":has\([^)]+\)", text)
        report["has_selectors_count"] += len(has_matches)

        # Hex outside tokens
        if not is_tokens_file:
            hex_matches = re.findall(r"#[0-9a-fA-F]{3,8}\b", text)
            for h in hex_matches:
                report["hex_outside_tokens"].append(f"{rel_path}: {h}")

        # Font sizes and em in font size
        font_size_matches = re.findall(r"font-size:\s*([^;!}]+)", text)
        for fs in font_size_matches:
            val = fs.strip()
            report["distinct_font_sizes"].add(val)
            if "em" in val and "rem" not in val:
                report["em_in_font_size"].append(f"{rel_path}: {val}")
            
            # Check if off-scale px or rem
            px_m = re.match(r"^(\d+(?:\.\d+)?)px$", val)
            if px_m:
                px_val = float(px_m.group(1))
                if px_val not in ALLOWED_TYPE_SCALE_PX:
                    report["off_scale_font_sizes"].add(val)
            rem_m = re.match(r"^(\d+(?:\.\d+)?)rem$", val)
            if rem_m:
                rem_val = float(rem_m.group(1))
                if rem_val not in ALLOWED_TYPE_SCALE_REM:
                    report["off_scale_font_sizes"].add(val)
            if re.match(r"^\d+pt$", val) and "print_forms.css" not in css_file.name:
                report["off_scale_font_sizes"].add(val)

        # Padding
        padding_matches = re.findall(r"(?:^|[;{])\s*padding(?:-[a-z]+)?:\s*([^;!}]+)", text)
        for p in padding_matches:
            report["distinct_paddings"].add(p.strip())

        # Gap
        gap_matches = re.findall(r"(?:^|[;{])\s*(?:row-|column-)?gap:\s*([^;!}]+)", text)
        for g in gap_matches:
            report["distinct_gaps"].add(g.strip())

        # Border-radius
        radius_matches = re.findall(r"border-radius:\s*([^;!}]+)", text)
        for r in radius_matches:
            report["distinct_radii"].add(r.strip())

        # Component definition locations
        for comp in report["component_definitions"]:
            # Find rules defining the component
            pattern = re.compile(r"([^{}]*\." + re.escape(comp) + r"[^{}]*)\{([^{}]+)\}", re.MULTILINE)
            for m in pattern.finditer(text):
                sel = m.group(1).strip()
                # filter out simple modifier usage inside templates
                line_no = raw[:m.start()].count("\n") + 1
                report["component_definitions"][comp].append(f"{rel_path}:{line_no} ({sel})")

    # 2. Scan templates for style=""
    template_files = list(templates_dir.rglob("*.html")) + list(apps_dir.rglob("*.html"))
    for tf in template_files:
        rel_tf = tf.relative_to(repo_root).as_posix()
        t_content = tf.read_text(encoding="utf-8")
        style_matches = list(re.finditer(r'\bstyle="([^"]*)"', t_content))
        for sm in style_matches:
            val = sm.group(1).strip()
            # exempt dynamic width/percentages used in charts if variable
            if "display:none" in val or "display: none" in val:
                continue
            report["template_inline_styles"] += 1
            line_no = t_content[:sm.start()].count("\n") + 1
            report["template_style_locations"].append(f"{rel_tf}:{line_no} style=\"{val[:40]}\"")

    # Convert sets to sorted lists for JSON serialization
    report["distinct_font_sizes"] = sorted(list(report["distinct_font_sizes"]))
    report["off_scale_font_sizes"] = sorted(list(report["off_scale_font_sizes"]))
    report["distinct_paddings"] = sorted(list(report["distinct_paddings"]))
    report["distinct_gaps"] = sorted(list(report["distinct_gaps"]))
    report["distinct_radii"] = sorted(list(report["distinct_radii"]))

    return report


def generate_markdown(report):
    md = []
    md.append("# Baseline Đánh giá Hệ Thống Thiết Kế & Token CSS (IHRMS)\n")
    md.append(f"- **Số tệp CSS quét**: {report['css_file_count']} tệp")
    md.append(f"- **Tổng dung lượng CSS**: {report['css_total_bytes'] / 1024:.1f} KB")
    md.append(f"- **Số lượng `!important`**: {report['important_count']}")
    md.append(f"- **Selector bám `.portal-app .ui-main`**: {report['portal_app_ui_main_count']}")
    md.append(f"- **Số selector chứa ID (`#...`)**: {report['id_selectors_count']}")
    md.append(f"- **Số bộ chọn `:has()`**: {report['has_selectors_count']}")
    md.append(f"- **Mã màu hex ngoài token**: {len(report['hex_outside_tokens'])}")
    md.append(f"- **Số giá trị `font-size` phân biệt**: {len(report['distinct_font_sizes'])}")
    md.append(f"- **Số giá trị `font-size` lệch thang**: {len(report['off_scale_font_sizes'])} ({', '.join(report['off_scale_font_sizes'][:10])}...)")
    md.append(f"- **Số kiểu `padding` phân biệt**: {len(report['distinct_paddings'])}")
    md.append(f"- **Số kiểu `gap` phân biệt**: {len(report['distinct_gaps'])}")
    md.append(f"- **Số giá trị `border-radius` phân biệt**: {len(report['distinct_radii'])}")
    md.append(f"- **Thuộc tính `style=\"...\"` trong template**: {report['template_inline_styles']}\n")

    md.append("## Đa định nghĩa thành phần nền (Single-source violations)\n")
    for comp, locs in report["component_definitions"].items():
        md.append(f"### Thành phần `.{comp}` ({len(locs)} định nghĩa)")
        for loc in locs[:6]:
            md.append(f"- `{loc}`")
        if len(locs) > 6:
            md.append(f"- ... và {len(locs) - 6} định nghĩa khác")
        md.append("")

    md.append("## Mục tiêu chất lượng sau chuẩn hóa (Target Thresholds)\n")
    md.append("| Chỉ số | Hiện tại (Baseline) | Ngưỡng mục tiêu |")
    md.append("|---|---|---|")
    md.append(f"| Giá trị font-size phân biệt | {len(report['distinct_font_sizes'])} | ≤ 9 (100% trong thang) |")
    md.append(f"| font-size lệch thang | {len(report['off_scale_font_sizes'])} | 0 |")
    md.append(f"| `!important` | {report['important_count']} | ≤ 10 (chú thích lý do) |")
    md.append(f"| Tiền tố `.portal-app .ui-main` | {report['portal_app_ui_main_count']} | 0 (nhờ `@layer`) |")
    md.append(f"| Hex literal ngoài token | {len(report['hex_outside_tokens'])} | 0 |")
    md.append(f"| Định nghĩa nút `.ui-button` | {len(report['component_definitions']['ui-button'])} | 1 khối chuẩn duy nhất |")
    md.append(f"| Định nghĩa ô `.ui-field` | {len(report['component_definitions']['ui-field'])} | 1 khối chuẩn duy nhất |")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Audit design tokens and CSS architecture.")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--output", type=Path, help="Write markdown output to file")
    parser.add_argument("--check", action="store_true", help="Fail if target thresholds are violated")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    report = audit_tokens(repo_root)

    if args.output:
        md_text = generate_markdown(report)
        args.output.write_text(md_text, encoding="utf-8")
        print(f"Audit report written to {args.output}")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(generate_markdown(report))

    if args.check:
        # Check thresholds for post-refactor gate
        errors = []
        if len(report["off_scale_font_sizes"]) > 0:
            errors.append(f"Off-scale font-sizes found: {report['off_scale_font_sizes']}")
        if report["important_count"] > 10:
            errors.append(f"!important count ({report['important_count']}) exceeds threshold 10")
        if len(report["hex_outside_tokens"]) > 0:
            errors.append(f"Hex literals outside tokens found: {len(report['hex_outside_tokens'])}")
        if errors:
            print("\n[FAIL] Audit thresholds exceeded:", file=sys.stderr)
            for err in errors:
                print(f" - {err}", file=sys.stderr)
            return 1
        print("\n[PASS] All design token audit thresholds satisfied!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
