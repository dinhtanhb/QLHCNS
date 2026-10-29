"""Verify mobile employee profile/directory and the shared HR decision command."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import uuid

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8793')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from mobile_qa import configure
    configure(args.directory.resolve())
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    from apps.hrm.models import EmployeeProfileChangeRequest, EmployeeReward
    from apps.security.models import User
    from apps.notification.models import Notification
    password = next(line.split(': ', 1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    employee = User.objects.get(username='demo-employee').employee
    employee.full_name = ('QA kiểm thử họ tên dài trên điện thoại ' * 8)[:200]
    employee.save(update_fields=['full_name'])
    marker = 'QA-PROFILE-'+uuid.uuid4().hex[:8]
    EmployeeReward.objects.create(employee=employee, reward_type=marker, reward_date=date.today(), amount='123456.78')
    args.output.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.add_init_script("""const originalFetch = window.fetch.bind(window);
            window.fetch = async (...args) => {
                const response = await originalFetch(...args);
                if (String(args[0]).includes('profile-history/?kind=transfers'))
                    await new Promise(resolve => setTimeout(resolve, 1000));
                return response;
            };""")
        page.on('pageerror', lambda e: errors.append(str(e)))
        def login(username):
            page.goto(args.url)
            page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill(username)
            page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
            page.get_by_role('button', name='Đăng nhập', exact=True).click()
            expect(page.get_by_text('Hồ sơ của tôi', exact=True)).to_be_visible()
        def services():
            page.get_by_role('button', name='Nghiệp vụ', exact=True).click()
        login('demo-employee'); services()
        expect(page.get_by_role('button', name='Duyệt cập nhật hồ sơ', exact=True)).to_have_count(0)
        page.get_by_role('button', name='Hồ sơ chi tiết', exact=True).click()
        expect(page.get_by_text(employee.full_name, exact=True).last).to_be_visible()
        page.get_by_role('button', name='Khen thưởng', exact=True).click()
        expect(page.get_by_text(marker, exact=True)).to_be_visible()
        page.wait_for_timeout(1200)  # The earlier real transfers response must not replace the newly selected rewards.
        expect(page.get_by_text(marker, exact=True)).to_be_visible()
        expect(page.get_by_text('123.456,78 đồng', exact=True).first).to_be_visible()
        for width in (390, 1280):
            page.set_viewport_size({'width': width, 'height': 900})
            for mode in ('light', 'dark'):
                page.emulate_media(color_scheme=mode)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                page.screenshot(path=str(args.output/f'profile-{width}-{mode}.png'), full_page=True)
        checks.append('Own profile/history and exact decimal display; no HR menu for employee; wide/narrow light/dark')
        page.get_by_role('button', name='Quay lại nghiệp vụ', exact=True).click()
        page.get_by_role('button', name='Sơ đồ tổ chức', exact=True).click()
        expect(page.get_by_text(employee.full_name, exact=True).last).to_be_visible()
        expect(page.get_by_text('Quản lý trực tiếp: '+employee.manager.full_name, exact=True)).to_be_visible()
        checks.append('Active directory and direct manager displayed')
        page.set_viewport_size({'width': 390, 'height': 844})
        for action, label, status in [('approve', 'Duyệt', 'Approved'), ('reject', 'Từ chối', 'Rejected'), ('more_info', 'Yêu cầu bổ sung', 'NeedsMoreInfo')]:
            login('demo-employee'); services()
            page.get_by_role('button', name='Yêu cầu cập nhật hồ sơ', exact=True).click()
            page.get_by_role('button', name='Địa chỉ', exact=True).click()
            value = (marker+'-'+action+' '+'QA kiểm thử địa chỉ dài. '*25)[:500].rstrip()
            page.get_by_role('textbox', name='Thông tin mới', exact=True).fill(value)
            page.get_by_role('button', name='Gửi yêu cầu cập nhật', exact=True).click()
            expect(page.get_by_text('Đã gửi yêu cầu đến Nhân sự.', exact=True)).to_be_visible()
            row = EmployeeProfileChangeRequest.objects.get(employee=employee, new_value=value)
            previous = row.old_value
            login('demo-hr'); services()
            page.get_by_role('button', name='Duyệt cập nhật hồ sơ', exact=True).click()
            page.screenshot(path=str(args.output/f'decision-{action}-pending.png'), full_page=True)
            page.get_by_role('button', name=f'{label} yêu cầu #{row.pk}', exact=True).click()
            page.get_by_role('textbox', name='Ý kiến xử lý', exact=True).fill(marker+' note')
            page.wait_for_timeout(400)  # Capture the settled Modal fade, not an intermediate translucent frame.
            page.screenshot(path=str(args.output/f'decision-{action}-confirm.png'), full_page=True)
            page.get_by_role('button', name='Xác nhận', exact=True).click()
            expect(page.get_by_text('Đã xử lý yêu cầu cập nhật hồ sơ.', exact=True)).to_be_visible()
            row.refresh_from_db(); employee.refresh_from_db()
            assert row.status == status and row.decision_note == marker+' note'
            assert employee.address == (value if action == 'approve' else previous)
            assert Notification.objects.filter(employee=employee, notification_type='profile-change').exists()
            page.screenshot(path=str(args.output/f'decision-{action}.png'), full_page=True)
            login('demo-employee')
            page.get_by_role('tab', name='Thông báo', exact=True).click()
            notice = Notification.objects.filter(employee=employee, notification_type='profile-change').latest('pk')
            page.get_by_role('button', name=f'Mở thông báo #{notice.pk}', exact=True).click()
            expect(page.get_by_text(value, exact=True)).to_be_visible()
            checks.append('Employee request → HR '+action+' → owned notification opens history; saved state checked')
        employee.refresh_from_db()
        row = EmployeeProfileChangeRequest.objects.create(employee=employee, field_name='address',
            old_value=employee.address or '', submitted_snapshot=employee.address or '', new_value=marker+'-web')
        page.goto(args.url+'/portal/login/')
        page.locator('input[name="username"]').fill('demo-hr')
        page.locator('input[name="password"]').fill(password)
        page.get_by_role('button', name='Đăng nhập', exact=True).click()
        page.goto(args.url+'/portal/profile/requests/')
        page.locator(f'form[action$="/profile/requests/{row.pk}/decide/"]').get_by_role('button', name='Duyệt cập nhật', exact=True).click()
        page.get_by_role('button', name='Gửi quyết định', exact=True).click()
        expect(page.get_by_text('Đã ghi nhận quyết định xử lý yêu cầu.', exact=True)).to_be_visible()
        row.refresh_from_db(); employee.refresh_from_db()
        assert row.status == 'Approved' and employee.address == marker+'-web'
        page.screenshot(path=str(args.output/'portal-shared-command.png'), full_page=True)
        checks.append('Portal HR approval still uses shared command and saves employee/profile decision')
        assert not errors, errors
        browser.close()
    (args.output/'validation.json').write_text(json.dumps({'checks': checks, 'count': len(checks), 'page_errors': errors, 'synthetic_only': True}, indent=2), encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'page_errors': len(errors)}))


if __name__ == '__main__':
    main()
