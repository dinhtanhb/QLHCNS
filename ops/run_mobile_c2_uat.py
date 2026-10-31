"""C2 short/long approval cards and decision-error recovery on synthetic QA."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright
from run_mobile_c_uat import ROW

ROOT = Path(__file__).resolve().parents[1]
SHORT = {**ROW, 'employee_name': 'QA An', 'reason': 'Việc gia đình.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8810')
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    qa, out = args.directory.resolve(), args.output.resolve()
    assert not qa.is_relative_to(ROOT) and not out.is_relative_to(ROOT)
    assert urlsplit(args.url).hostname in ('127.0.0.1', 'localhost', '::1')
    for marker in ('synthetic-demo.json', 'mobile-qa.json'):
        assert json.loads((qa/marker).read_text(encoding='utf-8'))['synthetic_only']
    password = next(line.split(': ', 1)[1] for line in (qa/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    out.mkdir(parents=True, exist_ok=True)
    cases, errors = [], []
    report = dict(baseline=args.baseline, cases=cases, page_errors=errors, native_tested=False,
                  synthetic_only=True, read_and_decision_responses='controlled QA fixtures, real demo-manager login')
    combinations = [(mode, w, h) for mode in ('light', 'dark') for w, h in ((360, 800), (390, 844), (412, 915))]
    if args.baseline:
        combinations = combinations[:1]
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            try:
                for mode, width, height in combinations:
                    context = browser.new_context(viewport=dict(width=width, height=height), color_scheme=mode)
                    try:
                        page = context.new_page()
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        state = dict(row=SHORT, handled=False, list_error=False, counter_requests_after_error=0)
                        def approvals(route):
                            if state['handled'] and not urlsplit(route.request.url).query:
                                state['counter_requests_after_error'] += 1
                            if state['list_error'] and urlsplit(route.request.url).query:
                                return route.fulfill(status=503, json={'error': 'QA danh sách tạm lỗi'})
                            route.fulfill(json=dict(items=[] if state['handled'] else [state['row']],
                                                   count=0 if state['handled'] else 1, page=1, has_next=False))
                        def decision(route):
                            state.update(handled=True, list_error=True)
                            route.fulfill(status=400, json={'error': 'QA đơn đã được xử lý bởi người khác'})
                        page.route('**/api/mobile/v1/approvals/**', approvals)
                        page.route('**/api/mobile/v1/leaves/*/decision/', decision)
                        page.goto(args.url)
                        page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill('demo-manager')
                        page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
                        page.get_by_role('button', name='Đăng nhập', exact=True).click()
                        expect(page.get_by_role('heading', name='Trang chủ', exact=True)).to_be_visible(timeout=20000)
                        tab = page.get_by_role('tab', name='Duyệt', exact=True)
                        tab.click()
                        approve = page.get_by_role('button', name='Duyệt đơn của QA An 04/01/2027', exact=True)
                        expect(approve).to_be_visible()
                        more = page.get_by_role('button', name='Xem đầy đủ đơn nghỉ phép', exact=True)
                        case = dict(mode=mode, width=width, short_more_count=more.count())
                        cases.append(case)
                        expect(more).to_have_count(1 if args.baseline else 0)
                        page.screenshot(path=str(out/f'{mode}_{width}_short.png'))
                        approve.click()
                        page.get_by_role('button', name='Xác nhận', exact=True).click()
                        expect(page.get_by_role('alert').filter(has_text='QA đơn đã được xử lý bởi người khác').last).to_be_visible()
                        expect(page.get_by_role('button', name='Thử tải lại', exact=True)).to_be_visible()
                        page.wait_for_timeout(400)
                        case['counter_requests_after_error'] = state['counter_requests_after_error']
                        case['stale_badge_after_error'] = tab.get_by_text('1', exact=True).count() > 0
                        if args.baseline:
                            assert case['stale_badge_after_error'] and state['counter_requests_after_error'] == 0
                        else:
                            assert not case['stale_badge_after_error'] and state['counter_requests_after_error'] > 0, case
                        # A failed list reload keeps existing rows; retry must recover from the server.
                        expect(page.get_by_text(SHORT['reason'], exact=True)).to_be_visible()
                        state['list_error'] = False
                        page.get_by_role('button', name='Thử tải lại', exact=True).click()
                        expect(page.get_by_role('heading', name='Không có đơn cần duyệt', exact=True)).to_be_visible()
                        expect(approve).to_have_count(0)
                        expect(tab.get_by_text('1', exact=True)).to_have_count(0)
                        if not args.baseline:
                            state.update(row=ROW, handled=False)
                            page.get_by_role('tab', name='Trang chủ', exact=True).click()
                            tab.click()
                            expect(more).to_be_visible()
                            long_approve = page.get_by_role('button', name='Duyệt đơn của '+ROW['employee_name']+' 04/01/2027', exact=True)
                            expect(long_approve).to_be_visible()
                            box = long_approve.bounding_box()
                            assert box['height'] >= 44 and box['y']+box['height'] < tab.bounding_box()['y']
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                            page.screenshot(path=str(out/f'{mode}_{width}_long.png'))
                    finally:
                        context.close()
            finally:
                browser.close()
        assert not errors, errors
    except Exception as error:
        report['failure'] = str(error)[:2000]
        raise
    finally:
        (out/'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(cases=len(cases), page_errors=errors, baseline=args.baseline)))


if __name__ == '__main__':
    main()
