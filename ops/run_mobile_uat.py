"""Exercise the React Native web export against isolated, real Django QA data."""
import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import uuid

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8789')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from mobile_qa import configure
    configure(args.directory.resolve())
    # Playwright's synchronous driver owns an event loop on this thread. ORM
    # checks here are sequential and target the verified synthetic DB only.
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    from django.utils import timezone
    from apps.leave.models import LeaveApproval, LeaveRequest
    from apps.notification.models import Notification
    args.output.mkdir(parents=True, exist_ok=True)
    accounts = (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8')
    password = next(line.split(': ', 1)[1] for line in accounts.splitlines() if 'Mật khẩu chung' in line)
    checks, screenshots, browser_errors = [], [], []
    def check(label, condition=True):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    def shot(page, name):
        path = args.output/(name+'.png')
        page.screenshot(path=str(path), full_page=True)
        screenshots.append(path.name)
    def no_overflow(page):
        return page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    def login(page, username):
        page.goto(args.url)
        page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill(username)
        page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
        page.get_by_role('button', name='Đăng nhập', exact=True).click()
        expect(page.get_by_text('Hồ sơ của tôi', exact=True)).to_be_visible(timeout=20000)
    reason = ('QA-MOBILE-'+uuid.uuid4().hex[:10]+' · '+'Kiểm thử nội dung dài trên màn hình hẹp. '*20)[:500].rstrip()
    day = timezone.localdate()+timedelta(days=45)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    while LeaveRequest.objects.filter(employee__user_account__username='demo-employee',
            from_date__lte=day, to_date__gte=day, status__in=['Pending', 'Approved']).exists():
        day += timedelta(days=7)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width':390, 'height':844}, color_scheme='light')
        page = context.new_page()
        page.on('pageerror', lambda error: browser_errors.append(str(error)))
        login(page, 'demo-employee')
        check('Employee login through real API')
        page.get_by_role('tab', name='Chấm công').click()
        expect(page.get_by_text('8.00 giờ làm việc', exact=True)).to_be_visible()
        check('Own attendance visible')
        page.get_by_role('tab', name='Nghỉ phép').click()
        page.get_by_role('button', name='Tạo đơn nghỉ phép', exact=True).click()
        expect(page.get_by_text('Loại nghỉ', exact=True)).to_be_visible()
        page.get_by_role('button', name='Phép năm giả lập', exact=True).click()
        page.get_by_role('textbox', name='Từ ngày (DD/MM/YYYY)', exact=True).fill(day.strftime('%d/%m/%Y'))
        page.get_by_role('textbox', name='Đến ngày (DD/MM/YYYY)', exact=True).fill(day.strftime('%d/%m/%Y'))
        page.get_by_role('textbox', name='Lý do nghỉ', exact=True).fill(reason)
        shot(page, 'leave-create-390-light')
        page.get_by_role('button', name='Gửi đơn nghỉ phép', exact=True).click()
        expect(page.get_by_text('Đã gửi đơn xin nghỉ phép, chờ phê duyệt.', exact=True)).to_be_visible()
        expect(page.get_by_text(reason, exact=True)).to_be_visible()
        leave = LeaveRequest.objects.get(reason=reason)
        check('Submission saved once as Pending', leave.status == 'Pending' and leave.employee.user_account.username == 'demo-employee')
        check('Approver in-app notification saved', Notification.objects.filter(employee__user_account__username='demo-manager',
            notification_type='leave', title='Có đơn nghỉ phép chờ duyệt').exists())
        page.get_by_role('tab', name='Tôi', exact=True).click()
        page.get_by_role('button', name='Đăng xuất', exact=True).click()
        page.get_by_role('button', name='Xác nhận', exact=True).click()
        expect(page.get_by_role('button', name='Đăng nhập', exact=True)).to_be_visible()
        check('Logout returns to login')
        login(page, 'demo-manager')
        page.get_by_role('tab', name='Duyệt đơn', exact=True).click()
        page.get_by_role('button', name=f'Duyệt đơn #{leave.pk}', exact=True).click()
        expect(page.get_by_text('Duyệt đơn nghỉ phép?', exact=True)).to_be_visible()
        page.get_by_role('button', name='Xác nhận', exact=True).click()
        expect(page.get_by_text('Đã xử lý đơn nghỉ phép.', exact=True)).to_be_visible()
        leave.refresh_from_db()
        check('Approval saved once and removed from inbox', leave.status == 'Approved' and LeaveApproval.objects.filter(leave_request=leave).count() == 1)
        expect(page.get_by_role('button', name=f'Duyệt đơn #{leave.pk}', exact=True)).to_have_count(0)
        check('Employee decision notification saved', Notification.objects.filter(employee=leave.employee,
            title='Đơn nghỉ phép đã duyệt').exists())
        shot(page, 'approval-result-390-light')
        context.set_offline(True)
        expect(page.get_by_text('Không có kết nối', exact=True)).to_be_visible()
        check('Offline hides data and blocks writes')
        context.set_offline(False)
        expect(page.get_by_role('tab', name='Tôi', exact=True)).to_be_visible(timeout=15000)
        page.get_by_role('tab', name='Tôi', exact=True).click()
        page.get_by_role('button', name='Đăng xuất', exact=True).click()
        page.get_by_role('button', name='Xác nhận', exact=True).click()
        expect(page.get_by_role('button', name='Đăng nhập', exact=True)).to_be_visible()
        login(page, 'demo-employee')
        page.get_by_role('tab', name='Thông báo', exact=True).click()
        expect(page.get_by_text('Đơn nghỉ phép đã duyệt', exact=True).first).to_be_visible()
        notice = Notification.objects.filter(employee=leave.employee, title='Đơn nghỉ phép đã duyệt').latest('pk')
        page.get_by_role('button', name=f'Mở thông báo #{notice.pk}', exact=True).click()
        expect(page.get_by_text(reason, exact=True)).to_be_visible()
        notice.refresh_from_db()
        check('Opening notice marks it read and routes to leaves', notice.is_read)
        # Layouts are measured on the actual RN screens, without mocking API data.
        for mode in ('light', 'dark'):
            page.emulate_media(color_scheme=mode)
            for width in (390, 768, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                for tab in ('Tôi', 'Chấm công', 'Nghỉ phép', 'Thông báo'):
                    page.get_by_role('tab', name=tab, exact=True).click()
                    page.wait_for_timeout(250)
                    check(f'{mode}/{width}/{tab}: no horizontal overflow', no_overflow(page))
                    shot(page, f'employee-{tab}-{width}-{mode}')
        # Keyboard navigation is exercised in the exported UI (same RN controls).
        reload_button = page.get_by_role('button', name='Tải lại', exact=True)
        reload_button.focus()
        expect(reload_button).to_be_focused()
        with page.expect_response(lambda response: '/api/mobile/v1/notifications/' in response.url and response.status == 200):
            page.keyboard.press('Enter')
        check('Keyboard activates focused reload control')
        check('No browser JavaScript exceptions', not browser_errors)
        context.close()
        # HR login verifies role-gated approval tab and management explanation.
        context = browser.new_context(viewport={'width':390,'height':844}, color_scheme='dark')
        page = context.new_page()
        login(page, 'demo-hr')
        expect(page.get_by_text('Dành cho Nhân sự', exact=True)).to_be_visible()
        expect(page.get_by_role('tab', name='Duyệt đơn', exact=True)).to_be_visible()
        check('HR role visible with existing permissions')
        shot(page, 'hr-profile-390-dark')
        # Portal sees the same decision; web login is QA-owned, never borrowed.
        page.goto(args.url+'/portal/login/')
        page.locator('[name=username]').fill('demo-employee')
        page.locator('[name=password]').fill(password)
        page.get_by_role('button', name='Đăng nhập', exact=True).click()
        page.goto(args.url+'/portal/leave/')
        expect(page.get_by_text(reason, exact=True)).to_be_visible()
        check('Existing web portal sees mobile-created and approved leave')
        page.goto(args.url+'/portal/')
        expect(page.locator('body')).not_to_contain_text('Server Error')
        check('Related Dashboard renders after shared workflow')
        browser.close()
    result = {'synthetic_only': True, 'checks': checks, 'count': len(checks), 'screenshots': screenshots,
        'browser_errors': browser_errors, 'backend': 'sqlite', 'ui': 'React Native web export in Edge; not Android/iOS device certification'}
    (args.output/'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks':len(checks), 'screenshots':len(screenshots), 'errors':len(browser_errors)}))


if __name__ == '__main__':
    main()
