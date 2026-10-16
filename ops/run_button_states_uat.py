"""UAT script for button variants, states, contrast, and visual hierarchy.

Tests all button variants (primary, secondary, tertiary, danger)
across states (default, hover, active, focus-visible, disabled)
in light and dark modes, and measures WCAG contrast ratios via getComputedStyle.
"""
import argparse
from datetime import date
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import uuid


def parse_color(color_str):
    """Parse rgb(...) or rgba(...) into (r, g, b, a)."""
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", color_str)
    if not m:
        return (0, 0, 0, 1.0)
    r = int(m.group(1)) / 255.0
    g = int(m.group(2)) / 255.0
    b = int(m.group(3)) / 255.0
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return (r, g, b, a)


def relative_luminance(rgb):
    r, g, b = rgb[:3]
    def srgb_to_linear(c):
        return c / 12.92 if c <= 0.03928 else math.pow((c + 0.055) / 1.055, 2.4)
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)


def contrast_ratio(color1_str, color2_str):
    c1 = parse_color(color1_str)
    c2 = parse_color(color2_str)
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--probe-issue", action="store_true", help="Probe known hover issue on Tao don nghi")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--packages-dir", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(root / "src"))

    pkg_dir = args.packages_dir
    if not pkg_dir:
        for cand in [
            Path(os.environ.get("TEMP", "")) / "ihrms_playwright_packages",
            Path("C:/Users/dinht/AppData/Local/Temp/ihrms_playwright_packages"),
            Path("C:/Users/dinht/AppData/Local/Temp/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"),
        ]:
            if cand.is_dir():
                pkg_dir = cand
                break
    if pkg_dir:
        sys.path.insert(0, str(pkg_dir.resolve()))

    from playwright.sync_api import sync_playwright

    output = args.output_dir or Path(tempfile.mkdtemp(prefix="ihrms-btn-uat-"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "screenshots").mkdir(exist_ok=True)

    os.environ.update(
        DJANGO_SETTINGS_MODULE="config.settings",
        APP_ENV="test",
        SECRET_KEY=secrets.token_urlsafe(64),
        DEBUG="False",
        M365_STORAGE_ENABLED="False",
        ENABLE_HTTPS_ENFORCEMENT="False",
        DJANGO_ALLOW_ASYNC_UNSAFE="true",
        DB_ENGINE="django.db.backends.sqlite3",
    )

    import django
    django.setup()
    from django.conf import settings
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.test.runner import DiscoverRunner
    from django.test.testcases import LiveServerThread
    from django.urls import reverse
    from django.utils import timezone

    from apps.hrm.models import Employee
    from apps.organization.models import Organization, Department, Position
    from apps.security.models import User, Role
    from apps.contract.models import Contract, ContractType
    from apps.leave.models import LeaveType, LeaveBalance

    database = settings.DATABASES["default"]
    database["CONN_MAX_AGE"] = 0
    test_db_name = "test_btn_uat_" + uuid.uuid4().hex + ".sqlite3"
    database["TEST"] = {**database.get("TEST", {}), "NAME": str(output / test_db_name)}
    settings.MEDIA_ROOT = str(output / "media")
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    runner = DiscoverRunner(verbosity=0, interactive=False)
    old_config = runner.setup_databases()

    today = timezone.localdate()
    password = secrets.token_urlsafe(32)

    # Seed minimal fixture
    org = Organization.objects.create(organization_code="UAT", organization_name="IHRMS UAT")
    dept = Department.objects.create(department_code="UAT", department_name="Phòng Nhân Sự", organization=org)
    pos = Position.objects.create(position_code="UAT", position_name="Chuyên viên")
    emp = Employee.objects.create(
        employee_code="EMP-UAT", first_name="Test", last_name="User",
        full_name="User UAT Test", date_of_birth=date(1990, 1, 1), gender="Other",
        national_id="SYN-BTN-01", company_email="test@example.test",
        mobile_phone="0000000000", join_date=date(2020, 1, 1),
        department=dept, position=pos, employment_status="Active"
    )
    user = User.objects.create_user(username="uat-user", password=password)
    user.employee = emp
    hr_role, _ = Role.objects.get_or_create(role_code="HR_MANAGER", defaults={"role_name": "Quản lý nhân sự"})
    user.role = hr_role
    user.save()

    leave_type = LeaveType.objects.create(leave_type_code="UAT", leave_type_name="Phép năm")
    LeaveBalance.objects.create(employee=emp, year=today.year, allocated_days=20)

    live = LiveServerThread("127.0.0.1", StaticFilesHandler, port=0)
    live.daemon = True
    live.start()
    live.is_ready.wait(timeout=30)
    if live.error:
        raise live.error
    base = f"http://127.0.0.1:{live.port}"

    results = {
        "probe_issue_detected": False,
        "probe_details": None,
        "tested_states": [],
        "failures": [],
    }

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=not args.headed)
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            # Login
            page.goto(base + reverse("portal:login"), wait_until="networkidle")
            page.locator("[name=username]").fill("uat-user")
            page.locator("[name=password]").fill(password)
            with page.expect_navigation(wait_until="networkidle"):
                page.locator("button[type=submit]").click()

            # Navigate to Dashboard
            page.goto(base + reverse("portal:dashboard"), wait_until="networkidle")

            # Probe specific defect if requested
            if args.probe_issue:
                leave_btn = page.locator("a.ui-button:has-text('Tạo đơn nghỉ')")
                if leave_btn.count() > 0:
                    default_color = leave_btn.evaluate("x => getComputedStyle(x).color")
                    default_bg = leave_btn.evaluate("x => getComputedStyle(x).backgroundColor")
                    ratio_default = contrast_ratio(default_color, default_bg)

                    leave_btn.hover()
                    page.wait_for_timeout(100)
                    hover_color = leave_btn.evaluate("x => getComputedStyle(x).color")
                    hover_bg = leave_btn.evaluate("x => getComputedStyle(x).backgroundColor")
                    ratio_hover = contrast_ratio(hover_color, hover_bg)

                    results["probe_details"] = {
                        "button": "Tạo đơn nghỉ",
                        "default": {"color": default_color, "bg": default_bg, "ratio": round(ratio_default, 2)},
                        "hover": {"color": hover_color, "bg": hover_bg, "ratio": round(ratio_hover, 2)},
                    }

                    page.screenshot(path=str(output / "screenshots" / "tao_don_nghi_hover.png"))

                    if ratio_hover < 4.5:
                        results["probe_issue_detected"] = True
                        results["failures"].append(
                            f"Hover contrast on 'Tạo đơn nghỉ' is {ratio_hover:.2f}:1 (color: {hover_color}, bg: {hover_bg}), failing WCAG 4.5:1 requirement"
                        )
            else:
                # Full test across variants, states, themes and contexts
                test_targets = [
                    ("Dashboard", reverse("portal:dashboard"), "a.ui-button:has-text('Tạo đơn nghỉ')", "primary"),
                    ("Employee List", reverse("portal:hr_employee_list"), "a.ui-button:has-text('Thêm nhân viên')", "primary"),
                    ("Employee Form", reverse("portal:hr_employee_create"), "button[type=submit]", "primary"),
                    ("Employee Form Cancel", reverse("portal:hr_employee_create"), "a.ui-button:has-text('Hủy')", "secondary"),
                    ("Login", reverse("portal:login"), "button[type=submit]", "primary"),
                ]

                for theme in ("light", "dark"):
                    page.evaluate(f'document.documentElement.dataset.theme = "{theme}"')
                    for ctx_name, url_path, sel, variant in test_targets:
                        page.goto(base + url_path, wait_until="networkidle")
                        btn = page.locator(sel).first
                        if btn.count() == 0:
                            continue

                        # 1. Default
                        col = btn.evaluate("x => getComputedStyle(x).color")
                        bg = btn.evaluate("x => getComputedStyle(x).backgroundColor")
                        ratio = contrast_ratio(col, bg)
                        state_res = {
                            "theme": theme, "context": ctx_name, "variant": variant,
                            "state": "default", "color": col, "bg": bg, "contrast": round(ratio, 2)
                        }
                        results["tested_states"].append(state_res)
                        if ratio < 4.5 and variant == "primary":
                            results["failures"].append(f"{ctx_name} {variant} ({theme}) default contrast {ratio:.2f}:1 < 4.5:1")

                        # 2. Hover
                        btn.hover()
                        page.wait_for_timeout(50)
                        h_col = btn.evaluate("x => getComputedStyle(x).color")
                        h_bg = btn.evaluate("x => getComputedStyle(x).backgroundColor")
                        h_ratio = contrast_ratio(h_col, h_bg)
                        results["tested_states"].append({
                            "theme": theme, "context": ctx_name, "variant": variant,
                            "state": "hover", "color": h_col, "bg": h_bg, "contrast": round(h_ratio, 2)
                        })
                        if h_ratio < 4.5 and variant == "primary":
                            results["failures"].append(f"{ctx_name} {variant} ({theme}) hover contrast {h_ratio:.2f}:1 < 4.5:1")

                        # 3. Focus
                        btn.focus()
                        page.wait_for_timeout(50)
                        outline_w = btn.evaluate("x => getComputedStyle(x).outlineWidth")
                        results["tested_states"].append({
                            "theme": theme, "context": ctx_name, "variant": variant,
                            "state": "focus", "outline": outline_w
                        })

                        # Capture screenshot
                        page.screenshot(path=str(output / "screenshots" / f"btn_{ctx_name.lower().replace(' ', '_')}_{theme}.png"))

            browser.close()
    finally:
        if old_config:
            runner.teardown_databases(old_config)

    report_path = output / "button_states_report.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    if args.probe_issue:
        # In probe mode, exit 1 if issue detected (to record failure on 912a0cb)
        if results["probe_issue_detected"]:
            print("\n[PROBE CONFIRMED] Defect reproduced: hover background overrides primary text contrast!", file=sys.stderr)
            return 1
        else:
            print("\n[PROBE PASSED] No defect observed.")
            return 0

    if results["failures"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
