"""Exercise account settings against an explicitly isolated mobile QA backend."""
import argparse
import json
import os
from pathlib import Path
import secrets
import uuid

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8792')
    parser.add_argument('--palette', choices=('viethealth', 'chamdong', 'thanam'), default='viethealth')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fail-after-password-change', action='store_true', help='Inject a QA assertion failure to verify password restoration')
    args = parser.parse_args()
    from mobile_qa import configure
    configure(args.directory.resolve())
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    from apps.hrm.models import EmployeeProfileChangeRequest
    from apps.security.models import User
    password = next(line.split(': ', 1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    args.output.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    original_user = User.objects.get(username='demo-employee')
    assert original_user.check_password(password), 'QA password does not match account manifest'
    original_hash = original_user.password
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 390, 'height': 844}, color_scheme='light')
            page.on('pageerror', lambda e: errors.append(str(e)))
            def login(secret):
                page.goto(args.url)
                page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill('demo-employee')
                page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(secret)
                page.get_by_role('button', name='Đăng nhập', exact=True).click()
                expect(page.get_by_role('heading', name='Trang chủ', exact=True)).to_be_visible()
            def profile():
                page.get_by_role('tab', name='Thêm', exact=True).click()
                page.get_by_role('button', name='Hồ sơ', exact=True).click()
                expect(page.get_by_role('heading', name='Hồ sơ của tôi', exact=True)).to_be_visible()
                page.wait_for_timeout(750)
            def settings():
                if page.get_by_role('heading', name='Hồ sơ của tôi', exact=True).count() == 0:
                    profile()
                page.get_by_role('button', name='Cài đặt', exact=True).click()
                expect(page.get_by_role('radio', name='Theo điện thoại', exact=True)).to_be_visible()
            login(password)
            expect(page.get_by_text('Bản ghi chấm công', exact=True)).to_be_visible()
            expect(page.get_by_text('Giờ làm (30 bản ghi gần nhất)', exact=True)).to_be_visible()
            expect(page.get_by_text('Đơn chờ (30 đơn gần nhất)', exact=True)).to_be_visible()
            expect(page.get_by_text('Chưa đọc (30 thông báo gần nhất)', exact=True)).to_be_visible()
            expect(page.get_by_text('Bản ghi chấm công tính trên toàn bộ dữ liệu. Các số ghi “gần nhất” chỉ tính trên 30 bản ghi mới nhất.', exact=True)).to_have_count(1)
            expect(page.get_by_role('heading', name='Hoạt động gần đây', exact=True)).to_be_visible()
            page.screenshot(path=str(args.output/'home-dashboard.png'), full_page=True)
            checks.append('Home shows account-specific summary metrics and latest attendance hours/date')
            page.get_by_role('tab', name='Thêm', exact=True).click()
            expect(page.get_by_role('heading', name='Nghiệp vụ', exact=True)).to_be_visible()
            expect(page.get_by_role('textbox', name='Tìm nghiệp vụ', exact=True)).to_be_visible()
            assert page.locator('text=Trung tâm Báo cáo (Excel)').count() == 0
            page.get_by_role('textbox', name='Tìm nghiệp vụ', exact=True).fill('Bảng công')
            expect(page.get_by_role('button', name='Bảng công', exact=True)).to_be_visible()
            page.screenshot(path=str(args.output/'business-groups.png'), full_page=True)
            checks.append('Business menu is searchable and grouped, exposes timesheet, and hides Excel report center')
            page.go_back()
            profile()
            settings_button = page.get_by_role('button', name='Cài đặt', exact=True)
            assert settings_button.is_visible()
            checks.append('Settings entry is visible from the account profile')
            settings()
            for width in (390, 768, 1280):
                page.set_viewport_size({'width': width, 'height': 900})
                for mode in ('Tối', 'Sáng'):
                    page.get_by_role('radio', name=mode, exact=True).click()
                    expect(page.get_by_role('radio', name=mode, exact=True)).to_be_checked()
                    palette = json.loads((Path(__file__).resolve().parents[1]/'mobile/src/palettes.json').read_text())
                    color = palette[args.palette]['dark' if mode == 'Tối' else 'light']['surface'].lstrip('#')
                    expected = 'rgb('+', '.join(str(int(color[i:i+2], 16)) for i in (0, 2, 4))+')'
                    expect(page.get_by_role('radio', name=mode, exact=True)).to_have_css('background-color', expected)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                    page.screenshot(path=str(args.output/f'settings-{width}-{mode}.png'), full_page=True)
            checks.append('Explicit light/dark choices checked and no overflow at 390/768/1280')
            page.get_by_role('radio', name='Tối', exact=True).focus()
            page.keyboard.press('Space')
            expect(page.get_by_role('radio', name='Tối', exact=True)).to_be_checked()
            login(password); settings()
            expect(page.get_by_role('radio', name='Tối', exact=True)).to_be_checked()
            checks.append('Theme selection persists across page reload and login, keyboard works')
            page.get_by_role('radio', name='Theo điện thoại', exact=True).click()
            for mode in ('dark', 'light'):
                page.emulate_media(color_scheme=mode)
                expect(page.get_by_role('radio', name='Theo điện thoại', exact=True)).to_be_checked()
                page.screenshot(path=str(args.output/f'settings-system-{mode}.png'), full_page=True)
            checks.append('System mode remains selected as device appearance changes')
            page.get_by_role('button', name='Cập nhật thông tin cá nhân', exact=True).click()
            value = 'QA-ADDRESS-'+uuid.uuid4().hex[:10]
            page.get_by_role('button', name='Địa chỉ', exact=True).click()
            page.get_by_role('textbox', name='Thông tin mới', exact=True).fill(value)
            page.get_by_role('textbox', name='Lý do cập nhật', exact=True).fill('Synthetic settings UAT')
            page.get_by_role('button', name='Gửi yêu cầu cập nhật', exact=True).click()
            expect(page.get_by_text('Đã gửi yêu cầu đến Nhân sự.', exact=True)).to_be_visible()
            expect(page.get_by_text(value, exact=True)).to_be_visible()
            row = EmployeeProfileChangeRequest.objects.get(new_value=value)
            assert row.status == 'Pending' and row.employee.user_account.username == 'demo-employee'
            assert row.employee.address != value
            page.screenshot(path=str(args.output/'profile-request.png'), full_page=True)
            checks.append('Profile update stored as owned Pending request; original profile unchanged; history visible')
            page.get_by_role('button', name='Quay lại cài đặt', exact=True).click()
            page.get_by_role('button', name='Đổi mật khẩu', exact=True).click()
            new = 'QA!'+secrets.token_urlsafe(18)
            page.get_by_role('textbox', name='Mật khẩu hiện tại', exact=True).fill(password)
            page.get_by_role('textbox', name='Mật khẩu mới', exact=True).fill(new)
            page.get_by_role('textbox', name='Nhập lại mật khẩu mới', exact=True).fill('mismatch')
            page.get_by_role('button', name='Lưu mật khẩu mới', exact=True).click()
            expect(page.get_by_text('Hai mật khẩu mới chưa khớp.', exact=True)).to_be_visible()
            page.get_by_role('textbox', name='Nhập lại mật khẩu mới', exact=True).fill(new)
            page.get_by_role('button', name='Lưu mật khẩu mới', exact=True).click()
            expect(page.get_by_role('button', name='Đăng nhập', exact=True)).to_be_visible()
            assert User.objects.get(username='demo-employee').check_password(new)
            login(new)
            checks.append('Password mismatch blocked; successful change logs out and new password logs in')
            if args.fail_after_password_change:
                raise AssertionError('QA injected failure after password change')
            finance_page = browser.new_page(viewport={'width': 390, 'height': 844}, color_scheme='light')
            finance_page.on('pageerror', lambda e: errors.append(str(e)))
            finance_page.goto(args.url)
            finance_page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill('demo-finance')
            finance_page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
            finance_page.get_by_role('button', name='Đăng nhập', exact=True).click()
            expect(finance_page.get_by_role('heading', name='Trang chủ', exact=True)).to_be_visible()
            finance_page.get_by_role('tab', name='Thêm', exact=True).click()
            expect(finance_page.get_by_role('heading', name='Nghiệp vụ', exact=True)).to_be_visible()
            hidden_mobile = ('Trang Quản Trị (Admin) ADMIN', 'Trung tâm Báo cáo (Excel)', 'Báo cáo',
                'Chạy lương hàng tháng', 'Lương cơ bản NV', 'Người phụ thuộc', 'Cấu hình Thuế/BH',
                'Thang bảng lương', 'Quản lý Tài sản', 'Kiểm kê Tài sản', 'Thanh lý Tài sản')
            for label in hidden_mobile:
                assert finance_page.get_by_text(label, exact=True).count() == 0, f'Desktop-only entry visible in mobile menu: {label}'
            finance_page.get_by_role('textbox', name='Tìm nghiệp vụ', exact=True).fill('Phiếu lương')
            expect(finance_page.get_by_role('button', name='Phiếu lương', exact=True)).to_be_visible()
            finance_page.screenshot(path=str(args.output/'finance-mobile-menu.png'), full_page=True)
            checks.append('Finance role retains payslip view while Admin, reports, payroll setup, and asset admin stay off the mobile menu')
            finance_page.close()
            assert not errors, errors
            browser.close()
    finally:
        # Restore even when a Playwright assertion fails after the password POST.
        user = User.objects.get(username='demo-employee')
        if user.password != original_hash:
            user.password = original_hash
            user.save(update_fields=['password'])
        user.refresh_from_db()
        restored = user.password == original_hash and user.check_password(password)
        (args.output/'password-restoration.json').write_text(json.dumps({'synthetic_only': True, 'restored': restored}), encoding='utf-8')
        assert restored, 'QA password restoration failed'
    (args.output/'validation.json').write_text(json.dumps({'checks': checks, 'count': len(checks), 'browser_errors': errors, 'synthetic_only': True}, indent=2), encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'browser_errors': len(errors)}))


if __name__ == '__main__':
    main()
