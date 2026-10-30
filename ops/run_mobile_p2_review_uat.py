"""Reproduce P2 review findings on an explicitly marked synthetic QA runtime."""
import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import uuid

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8805')
    parser.add_argument('--matrix', action='store_true')
    parser.add_argument('--matrix-only', action='store_true', help='Refresh the screenshot matrix without repeating workflow assertions')
    args = parser.parse_args()
    from mobile_qa import configure
    configure(args.directory.resolve())
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    from django.utils import timezone
    from apps.leave.models import LeaveRequest, LeaveType
    from apps.security.models import User
    from apps.notification.models import Notification
    from apps.portal.selectors import approvable_leave_requests

    password = next(line.split(': ', 1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    employee = User.objects.get(username='demo-employee').employee
    manager = User.objects.get(username='demo-manager')
    assert manager.check_password(password) and employee.user_account.check_password(password), 'QA fixture password mismatch'
    # Only the marked, disposable QA database is configured above.
    approvable_leave_requests(manager).update(status='Rejected')
    marker = 'QA-P2b-'+uuid.uuid4().hex[:8]
    day = timezone.localdate()+timedelta(days=180)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    kind = LeaveType.objects.get(leave_type_code='DEMO')
    pending = []
    for offset in (0, 7):
        start = day+timedelta(days=offset)
        while LeaveRequest.objects.filter(employee=employee, status__in=['Pending', 'Approved'], from_date__lte=start, to_date__gte=start).exists():
            start += timedelta(days=7)
        pending.append(LeaveRequest.objects.create(employee=employee, leave_type=kind, from_date=start, to_date=start, total_days=1, reason=marker+' '+str(offset)))
    notice = Notification.objects.create(employee=employee, title=marker+' quyết định nghỉ', message='Dữ liệu giả kiểm thử điều hướng', notification_type='leave', link='/portal/leave/')
    args.output.mkdir(parents=True, exist_ok=True)
    checks, failures, errors = [], [], []

    def check(name, assertion):
        try:
            assertion()
            checks.append(name)
        except Exception as error:
            failures.append({'check': name, 'error': str(error)[:1000]})
        (args.output/'progress.json').write_text(json.dumps({'checks': checks, 'failures': failures}, ensure_ascii=False, indent=2), encoding='utf-8')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        def login(username, init=None, palette=None, mode='light', width=390, height=844, fault=None):
            context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=mode)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            if init:
                page.add_init_script(init)
            if fault:
                page.route('**/api/mobile/v1/'+fault+'/**', lambda route: route.fulfill(status=503, json={'error': 'QA-P2b lỗi tải '+fault}))
            if palette:
                def palette_response(route):
                    response = route.fetch()
                    body = response.json()
                    body['palette'] = palette
                    route.fulfill(response=response, json=body)
                page.route('**/api/mobile/v1/me/', palette_response)
            page.goto(args.url)
            page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill(username)
            page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
            page.get_by_role('button', name='Đăng nhập', exact=True).click()
            expect(page.get_by_role('heading', name='Trang chủ', exact=True)).to_be_visible(timeout=20000)
            return context, page

        if args.matrix_only:
            capture_matrix(browser, login, args.output, checks)
            browser.close()
            assert not errors, errors
            (args.output/'validation-matrix.json').write_text(json.dumps({'checks': checks, 'page_errors': errors, 'synthetic_only': True}, indent=2)+'\n', encoding='utf-8')
            print(json.dumps({'matrix_only': True, 'checks': checks, 'page_errors': errors}))
            return

        def select_tab(page, name):
            tab = page.get_by_role('tab', name=name, exact=True)
            tab.click()
            expect(tab).to_have_attribute('aria-selected', 'true')
            page.wait_for_timeout(300)  # Let the navigator finish its screen transition.

        context, page = login('demo-employee')
        select_tab(page, 'Việc của tôi')
        page.get_by_role('radio', name='Nghỉ phép', exact=True).click()
        select_tab(page, 'Trang chủ')
        page.get_by_role('button', name='Chấm công', exact=True).click()
        check('M-02 home action selects attendance on an already mounted tab', lambda: expect(page.get_by_role('radio', name='Chấm công', exact=True)).to_be_checked(timeout=1500))
        page.get_by_role('radio', name='Chấm công', exact=True).click()
        select_tab(page, 'Trang chủ')
        page.get_by_role('button', name='Tạo đơn nghỉ', exact=True).click()
        page.get_by_role('button', name='Phép năm giả lập', exact=True).click()
        submit_day = day+timedelta(days=35)
        while LeaveRequest.objects.filter(employee=employee, status__in=['Pending', 'Approved'], from_date__lte=submit_day, to_date__gte=submit_day).exists():
            submit_day += timedelta(days=7)
        for label in ('Từ ngày (DD/MM/YYYY)', 'Đến ngày (DD/MM/YYYY)'):
            page.get_by_role('textbox', name=label, exact=True).fill(submit_day.strftime('%d/%m/%Y'))
        page.get_by_role('textbox', name='Lý do nghỉ', exact=True).fill(marker+' submitted')
        page.get_by_role('button', name='Gửi đơn nghỉ phép', exact=True).click()
        expect(page.get_by_text('Đã gửi đơn xin nghỉ phép, chờ phê duyệt.', exact=True)).to_be_visible()
        check('M-02 successful submission selects leave after attendance', lambda: expect(page.get_by_role('radio', name='Nghỉ phép', exact=True)).to_be_checked(timeout=1500))
        select_tab(page, 'Trang chủ')
        select_tab(page, 'Việc của tôi')
        check('M-02 submission banner is not replayed after returning', lambda: expect(page.get_by_text('Đã gửi đơn xin nghỉ phép, chờ phê duyệt.', exact=True)).to_have_count(0, timeout=1500))
        page.screenshot(path=str(args.output/'my-work-return.png'), full_page=True)
        (args.output/'my-work-return.txt').write_text(page.locator('body').inner_text(), encoding='utf-8')
        page.get_by_role('radio', name='Chấm công', exact=True).click()
        select_tab(page, 'Thông báo')
        page.get_by_role('button', name='Mở thông báo: '+notice.title, exact=True).click()
        check('M-02 notice destination explicitly selects leave', lambda: expect(page.get_by_role('radio', name='Nghỉ phép', exact=True)).to_be_checked(timeout=1500))
        context.close()

        # Put exactly two real requests in the manager inbox before exercising decisions.
        approvable_leave_requests(manager).exclude(pk__in=[row.pk for row in pending]).update(status='Rejected')
        context, page = login('demo-manager')
        tab = page.get_by_role('tab', name='Duyệt', exact=True)
        def home_count(value):
            card = page.get_by_text('Cần duyệt', exact=True).locator('..').locator('..').locator('..')
            expect(card.get_by_text(str(value), exact=True)).to_be_visible()
        check('M-03 initial badge is two', lambda: expect(tab.get_by_text('2', exact=True)).to_be_visible())
        select_tab(page, 'Duyệt')
        for index, row in enumerate(pending):
            page.get_by_role('button', name=f'Duyệt đơn của {employee.full_name} {row.from_date:%d/%m/%Y}', exact=True).click()
            page.get_by_role('button', name='Xác nhận', exact=True).click()
            expect(page.get_by_text(row.reason, exact=True)).to_have_count(0, timeout=15000)
            if index == 0:
                check('M-03 approving first request immediately updates badge to one', lambda: expect(tab.get_by_text('1', exact=True)).to_be_visible(timeout=2000))
                select_tab(page, 'Trang chủ')
                check('M-03 Home approval metric is also one after the first decision', lambda: home_count(1))
                select_tab(page, 'Duyệt')
            else:
                check('M-03 badge disappears after last request', lambda: expect(tab.get_by_text(re.compile(r'^\d+\+?$'))).to_have_count(0, timeout=2000))
        select_tab(page, 'Trang chủ')
        expect(page.get_by_role('heading', name='Đã xử lý hết', exact=True)).to_be_visible()
        home_count(0)
        check('M-03 home and tab both show zero after decisions', lambda: expect(tab.get_by_text(re.compile(r'^\d+\+?$'))).to_have_count(0))
        context.close()

        context, page = login('demo-employee', width=360, height=800)
        select_tab(page, 'Thêm')
        field = page.get_by_role('textbox', name='Tìm nghiệp vụ', exact=True)
        expect(field).to_be_visible()
        expect(page.get_by_role('button', name='Bảng công', exact=True)).to_be_visible(timeout=15000)
        def horizontal_inset():
            box = field.bounding_box()
            assert abs(box['x']-16) <= 1 and abs(box['width']-328) <= 1, box
            assert abs(page.get_by_role('heading', name='Nghiệp vụ', exact=True).bounding_box()['x']-box['x']) <= 1
        check('M-04 compact content has one 16px inset at 360px', horizontal_inset)
        page.screenshot(path=str(args.output/'compact-inset.png'), full_page=True)
        context.close()

        slow = """const original = fetch.bind(window); window.__started=[]; window.__initialEmpty=false;
          new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(node=>{
            if(node.textContent==='Không có đơn cần duyệt') window.__initialEmpty=true;
          }))).observe(document,{childList:true,subtree:true});
          window.fetch=async(...args)=>{const url=String(args[0]); window.__started.push(url);
          if(url.includes('/attendance/') || url.includes('/approvals/') || url.includes('/notifications/')) await new Promise(r=>setTimeout(r,1800));
          return original(...args);};"""
        context, page = login('demo-manager', init=slow)
        page.wait_for_timeout(150)
        check('M-05 home starts notifications independently of slow attendance', lambda: assert_true(page.evaluate("window.__started.some(x=>x.includes('/notifications/'))")))
        select_tab(page, 'Duyệt')
        check('M-05 loading does not claim approvals are empty', lambda: expect(page.get_by_role('heading', name='Không có đơn cần duyệt', exact=True)).to_have_count(0))
        check('M-05 initial render never inserts an empty approval heading', lambda: assert_true(not page.evaluate('window.__initialEmpty')))
        context.close()

        for resource, title, tabname in [('approvals', 'Không có đơn cần duyệt', 'Duyệt'), ('notifications', 'Chưa có thông báo', 'Thông báo')]:
            context, page = login('demo-manager', fault=resource)
            select_tab(page, tabname)
            expect(page.get_by_role('alert').filter(has_text='QA-P2b lỗi tải '+resource).last).to_be_visible()
            check('M-05 '+resource+' failure does not claim empty data', lambda: expect(page.get_by_role('heading', name=title, exact=True)).to_have_count(0))
            check('M-05 '+resource+' failure exposes retry', lambda: expect(page.get_by_role('button', name='Thử tải lại', exact=True)).to_be_visible())
            page.screenshot(path=str(args.output/(resource+'-error.png')), full_page=True)
            if resource == 'approvals':
                select_tab(page, 'Trang chủ')
                expect(page.get_by_role('alert').filter(has_text='QA-P2b lỗi tải approvals').last).to_be_visible()
                page.wait_for_timeout(150)
                check('M-05 home failure does not claim all approvals handled', lambda: expect(page.get_by_role('heading', name='Đã xử lý hết', exact=True)).to_have_count(0))
                select_tab(page, tabname)
            page.unroute('**/api/mobile/v1/'+resource+'/**')
            page.get_by_role('button', name='Thử tải lại', exact=True).click()
            check('M-05 '+resource+' retry recovers after backend returns', lambda: expect(page.get_by_role('alert').filter(has_text='QA-P2b lỗi tải '+resource)).to_have_count(0))
            context.close()

        # A loaded list must remain visible during a delayed focus refresh.
        refreshed = LeaveRequest.objects.create(employee=employee, leave_type=kind, from_date=day+timedelta(days=70), to_date=day+timedelta(days=70), total_days=1, reason=marker+' refresh')
        context, page = login('demo-manager')
        select_tab(page, 'Duyệt')
        expect(page.get_by_text(refreshed.reason, exact=True)).to_be_visible()
        page.evaluate("window.__originalFetch=fetch; window.fetch=async(...args)=>{if(String(args[0]).includes('/approvals/')) await new Promise(r=>setTimeout(r,1800)); return window.__originalFetch(...args);}")
        select_tab(page, 'Trang chủ')
        select_tab(page, 'Duyệt')
        check('M-05 existing list survives focus refresh', lambda: expect(page.get_by_text(refreshed.reason, exact=True)).to_be_visible(timeout=500))
        context.close()

        context, page = login('demo-employee')
        select_tab(page, 'Việc của tôi')
        page.get_by_role('radio', name='Nghỉ phép', exact=True).click()
        expect(page.get_by_text(refreshed.reason, exact=True)).to_be_visible()
        page.evaluate("window.__originalFetch=fetch; window.fetch=async(...args)=>{if(String(args[0]).includes('/attendance/')) await new Promise(r=>setTimeout(r,1800)); return window.__originalFetch(...args);}")
        page.get_by_role('radio', name='Chấm công', exact=True).click()
        check('M-05 changing list path hides old leave rows immediately', lambda: expect(page.get_by_text(refreshed.reason, exact=True)).to_have_count(0))
        expect(page.get_by_text('8.00 giờ làm việc', exact=True)).to_be_visible()
        context.close()

        if args.matrix:
            capture_matrix(browser, login, args.output, checks)
        browser.close()
    result = {'synthetic_only': True, 'ui': 'Expo web export in Edge; native not certified', 'checks': checks, 'failures': failures, 'page_errors': errors}
    (args.output/'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': len(checks), 'failed': [x['check'] for x in failures], 'page_errors': errors}, ensure_ascii=True))
    raise SystemExit(1 if failures or errors else 0)


def assert_true(value):
    assert value


def capture_matrix(browser, login, output, checks):
    """Exercise actual theme tokens; only me.palette is overridden as a QA fixture."""
    records = []
    palettes = json.loads((Path(__file__).resolve().parents[1]/'mobile/src/palettes.json').read_text(encoding='utf-8'))
    for palette in ('viethealth', 'chamdong', 'thanam'):
        for mode in ('light', 'dark'):
            for role in ('employee', 'manager'):
                for width, height in ((360, 800), (390, 844), (412, 915)):
                    context, page = login('demo-'+role, palette=palette, mode=mode, width=width, height=height)
                    screens = [('Trang chủ', 'home'), ('Việc của tôi', 'my-leave'), ('Việc của tôi', 'my-attendance'), ('Thông báo', 'notifications'), ('Thêm', 'more')]
                    if role == 'manager':
                        screens.insert(3, ('Duyệt', 'approvals'))
                    for tab, name in screens:
                        target = page.get_by_role('tab', name=tab, exact=True)
                        target.click()
                        expect(target).to_have_attribute('aria-selected', 'true')
                        expect(page.get_by_role('heading', name='Nghiệp vụ' if tab == 'Thêm' else tab, exact=True)).to_be_visible()
                        if name.startswith('my-'):
                            page.get_by_role('radio', name='Chấm công' if name.endswith('attendance') else 'Nghỉ phép', exact=True).click()
                        page.wait_for_timeout(180)
                        expect(page.get_by_role('progressbar', name='Đang tải nội dung')).to_have_count(0, timeout=15000)
                        if name == 'more':
                            expect(page.get_by_role('button', name='Bảng công', exact=True)).to_be_visible(timeout=15000)
                            expect(page.get_by_text('Danh mục thay đổi theo quyền của tài khoản.', exact=True)).to_have_count(1)
                            color = palettes[palette][mode]['surface'].lstrip('#')
                            expected = 'rgb('+', '.join(str(int(color[i:i+2], 16)) for i in (0, 2, 4))+')'
                            expect(page.get_by_role('textbox', name='Tìm nghiệp vụ', exact=True)).to_have_css('background-color', expected)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (palette, mode, role, width, name)
                        file = f'{palette}_{mode}_{role}_{width}_{name}.png'
                        page.screenshot(path=str(output/file), full_page=True)
                        # Scroll each actual RN scroll container to the last item, then verify it clears the tab bar.
                        page.evaluate("document.querySelectorAll('div').forEach(x=>{if(/auto|scroll/.test(getComputedStyle(x).overflowY)&&x.scrollHeight>x.clientHeight)x.scrollTop=x.scrollHeight;})")
                        page.wait_for_timeout(80)
                        tab_top = page.get_by_role('tab', name='Trang chủ', exact=True).bounding_box()['y']
                        bad = page.evaluate("""tabTop=>[...document.querySelectorAll('div')].filter(x=>/auto|scroll/.test(getComputedStyle(x).overflowY)&&x.scrollHeight>x.clientHeight).some(x=>x.getBoundingClientRect().bottom>tabTop+3)""", tab_top)
                        assert not bad, ('scroll area overlaps tab bar', file)
                        records.append({'palette': palette, 'mode': mode, 'role': role, 'width': width, 'height': height, 'screen': name, 'file': file, 'no_horizontal_overflow': True, 'scroll_area_clears_tabs': True, 'palette_fixture': True})
                    context.close()
    (output/'matrix.json').write_text(json.dumps({'screens': len(records), 'records': records}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    checks.append(f'M-04 matrix: {len(records)} screenshots, no overflow or scroll area overlapping tabs')


if __name__ == '__main__':
    main()
