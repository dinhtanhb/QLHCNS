"""Capture before/after audit screenshots for the 6 required sample pages.

Pages:
1. Dashboard Director / HR Manager / Employee view
2. hr_employee_list
3. hr_employee_form
4. Asset Form (portal:asset_admin_list)
5. report_headcount
6. login

Viewports:
- 1440x900
- 1756x1080 (1756px desktop audit width)
- 390x844 (mobile iPhone 12/13/14)
Themes:
- Light
- Dark
"""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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
        ]:
            if cand.is_dir():
                pkg_dir = cand
                break
    if pkg_dir and str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))

    from playwright.sync_api import sync_playwright

    output = args.output_dir or (root / "docs" / "screenshots" / "stage1_samples")
    output.mkdir(parents=True, exist_ok=True)

    os.environ.update(
        DJANGO_SETTINGS_MODULE="config.settings",
        APP_ENV="test",
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
    from apps.leave.models import LeaveType, LeaveBalance
    from apps.asset.models import Asset, AssetType

    database = settings.DATABASES["default"]
    database["CONN_MAX_AGE"] = 0
    test_db_name = "test_ss_uat_" + uuid.uuid4().hex + ".sqlite3"
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
        employee_code="EMP-UAT", first_name="Anh", last_name="Nguyễn",
        full_name="Nguyễn Anh", date_of_birth=date(1990, 1, 1), gender="Other",
        national_id="SYN-SS-01", company_email="anh.nguyen@example.test",
        mobile_phone="0901234567", join_date=date(2020, 1, 1),
        department=dept, position=pos, employment_status="Active"
    )
    user = User.objects.create_user(username="admin-user", password=password)
    user.employee = emp
    hr_role, _ = Role.objects.get_or_create(role_code="HR_MANAGER", defaults={"role_name": "Quản lý nhân sự"})
    user.role = hr_role
    user.is_superuser = True
    user.is_staff = True
    user.save()

    leave_type = LeaveType.objects.create(leave_type_code="AL", leave_type_name="Phép năm")
    LeaveBalance.objects.create(employee=emp, year=today.year, allocated_days=20)

    # Seed sample asset for Asset Form view
    asset_type = AssetType.objects.create(
        asset_type_code="EQ-01", asset_type_name="Máy móc thiết bị văn phòng", asset_group="Machinery"
    )
    Asset.objects.create(
        asset_code="TS-UAT-001", asset_name="Laptop Dell Latitude",
        asset_type=asset_type, status="InUse", location="Văn phòng Hà Nội"
    )

    live = LiveServerThread("127.0.0.1", StaticFilesHandler, port=0)
    live.daemon = True
    live.start()
    live.is_ready.wait(timeout=30)
    if live.error:
        raise live.error
    base = f"http://127.0.0.1:{live.port}"

    pages_to_capture = [
        ("dashboard", reverse("portal:dashboard")),
        ("hr_employee_list", reverse("portal:hr_employee_list")),
        ("hr_employee_form", reverse("portal:hr_employee_create")),
        ("asset_form", reverse("portal:asset_admin_list")),
        ("report_headcount", reverse("portal:report_headcount") + f"?year={today.year}"),
        ("login", reverse("portal:login")),
    ]

    viewports = [
        ("1440x900", {"width": 1440, "height": 900}),
        ("1756px", {"width": 1756, "height": 1080}),
        ("390px", {"width": 390, "height": 844}),
    ]

    manifest = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)

            for theme in ["light", "dark"]:
                for vp_name, vp_dims in viewports:
                    context = browser.new_context(viewport=vp_dims)
                    page = context.new_page()

                    # 1. Capture login unauthenticated
                    page.goto(base + reverse("portal:login"), wait_until="networkidle")
                    page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
                    page.wait_for_timeout(100)
                    login_file = output / f"login_{vp_name}_{theme}.png"
                    page.screenshot(path=str(login_file), full_page=False)
                    manifest.append(str(login_file.name))

                    # 2. Login
                    page.locator("[name=username]").fill("admin-user")
                    page.locator("[name=password]").fill(password)
                    with page.expect_navigation(wait_until="networkidle"):
                        page.locator("button[type=submit]").click()

                    # 3. Capture authenticated pages
                    for page_key, page_url in pages_to_capture:
                        if page_key == "login":
                            continue
                        page.goto(base + page_url, wait_until="networkidle")
                        page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
                        page.wait_for_timeout(150)
                        file_name = f"{page_key}_{vp_name}_{theme}.png"
                        out_path = output / file_name
                        page.screenshot(path=str(out_path), full_page=False)
                        manifest.append(file_name)

                    context.close()
            browser.close()
    finally:
        runner.teardown_databases(old_config)
        live.terminate()
        live.join()

    print(json.dumps({"captured_count": len(manifest), "manifest": manifest}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
