"""Group C regression probes and screenshot matrix on synthetic mobile QA only."""
import argparse
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
LONG_NAME = 'Nhân viên kiểm thử tên dài ' * 18
LONG_REASON = 'Lý do giả lập cần xem đầy đủ trước khi quyết định. ' * 60 + 'KẾT THÚC QA'
ROW = dict(id=987654, employee_name=LONG_NAME, leave_type='Phép năm QA',
           from_date='2027-01-04', to_date='2027-01-04', total_days='1',
           reason=LONG_REASON, status='Pending', status_label='Chờ duyệt')
LINKS = [('Chấm công', '/portal/attendance/'), ('Đăng ký QA', '/portal/qa-register/'),
         ('Bảng công', '/portal/attendance/summary/')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8810')
    parser.add_argument('--phase', choices=['before', 'after'], default='after')
    parser.add_argument('--single', action='store_true', help='Diagnostic 360px light probe; not the full matrix')
    args = parser.parse_args()
    qa, out = args.directory.resolve(), args.output.resolve()
    assert not qa.is_relative_to(ROOT) and not out.is_relative_to(ROOT)
    assert urlsplit(args.url).hostname in ('localhost', '127.0.0.1', '::1')
    for marker in ('synthetic-demo.json', 'mobile-qa.json'):
        assert json.loads((qa/marker).read_text(encoding='utf-8'))['synthetic_only'] is True
    password = next(line.split(': ', 1)[1] for line in (qa/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    out.mkdir(parents=True, exist_ok=True)
    cases, errors = [], []
    report = dict(phase=args.phase, cases=cases, page_errors=errors, synthetic_only=True,
                  native_tested=False, responses='Long QA approval and controlled navigation labels; real QA manager login')
    palettes = json.loads((ROOT/'mobile/src/palettes.json').read_text(encoding='utf-8'))
    combinations = [(p, m, w, h) for p in palettes for m in ('light', 'dark')
                    for w, h in ((360, 800), (390, 844), (412, 915))]
    if args.phase == 'before' or args.single:
        combinations = combinations[:1]
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            try:
                for palette, mode, width, height in combinations:
                    context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=mode)
                    try:
                        page = context.new_page()
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        def me_response(route):
                            response = route.fetch()
                            body = response.json()
                            assert body['can_approve'] is True
                            body['palette'] = palette
                            route.fulfill(response=response, json=body)
                        page.route('**/api/mobile/v1/me/', me_response)
                        page.route('**/api/mobile/v1/approvals/**', lambda route: route.fulfill(json=dict(items=[ROW], count=1, page=1, has_next=False)))
                        page.route('**/api/mobile/v1/workspace/**', lambda route: route.fulfill(json=dict(
                            kind='page', title='QA', path='/portal/', blocks=[], messages=[], navigation=[
                                dict(kind='link', label=label, path=path, external=False, group='Nghiệp vụ QA') for label, path in LINKS])))
                        page.goto(args.url)
                        page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill('demo-manager')
                        page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
                        page.get_by_role('button', name='Đăng nhập', exact=True).click()
                        expect(page.get_by_role('heading', name='Trang chủ', exact=True)).to_be_visible(timeout=20000)
                        tabs = page.get_by_role('tab')
                        expect(tabs).to_have_count(5)
                        case = dict(palette=palette, mode=mode, width=width)
                        cases.append(case)
                        labels = []
                        for name in ('Trang chủ', 'Việc của tôi', 'Duyệt', 'Thông báo', 'Thêm'):
                            tab = page.get_by_role('tab', name=name, exact=True)
                            label = tab.get_by_text(name, exact=True)
                            labels.append(label.evaluate('el=>{const r=document.createRange();r.selectNodeContents(el);return {font:parseFloat(getComputedStyle(el).fontSize),width:el.getBoundingClientRect().width,scroll:el.scrollWidth,textWidth:r.getBoundingClientRect().width};}'))
                            box = tab.bounding_box()
                            assert box['width'] >= 44 and box['height'] >= 44, box
                            assert box['x'] >= -1 and box['x']+box['width'] <= width+1, box
                        case['tab_labels'] = labels
                        if args.phase == 'after':
                            assert all(x['font'] == 12 and x['scroll'] <= math.ceil(x['width']) and x['textWidth'] <= x['width']+0.1 for x in labels), labels
                        tab = page.get_by_role('tab', name='Duyệt', exact=True)
                        expect(tab.get_by_text('1', exact=True)).to_be_visible()
                        badge = tab.get_by_text('1', exact=True).bounding_box()
                        tb = tab.bounding_box()
                        assert badge['x'] >= tb['x'] and badge['x']+badge['width'] <= tb['x']+tb['width']+1
                        tab.click()
                        approve = page.get_by_role('button', name='Duyệt đơn của '+LONG_NAME+' 04/01/2027', exact=True)
                        expect(approve).to_be_attached()
                        page.wait_for_timeout(200)
                        case['action_bottom'] = approve.bounding_box()['y']+approve.bounding_box()['height']
                        case['tab_top'] = tab.bounding_box()['y']
                        case['details_available'] = page.get_by_role('button', name='Xem đầy đủ đơn nghỉ phép', exact=True).count() > 0
                        prefix = f'{palette}_{mode}_{width}'
                        page.screenshot(path=str(out/(prefix+'_approvals.png')))
                        if args.phase == 'after':
                            assert case['action_bottom'] < case['tab_top'], case
                            assert case['details_available']
                            for button in (approve, page.get_by_role('button', name='Từ chối đơn của '+LONG_NAME+' 04/01/2027', exact=True)):
                                box = button.bounding_box()
                                assert box['width'] >= 44 and box['height'] >= 44 and box['y'] >= 0
                                assert box['y']+box['height'] < case['tab_top'], box
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                            reason = page.get_by_text(LONG_REASON, exact=True)
                            assert reason.evaluate("el=>getComputedStyle(el).webkitLineClamp") == '3'
                            # The mounted, hidden Home also contains the employee name.
                            name = page.get_by_text(LONG_NAME, exact=True).last
                            assert name.evaluate("el=>getComputedStyle(el).webkitLineClamp") == '2'
                            page.get_by_role('button', name='Xem đầy đủ đơn nghỉ phép', exact=True).click()
                            expect(page.get_by_role('heading', name='Chi tiết đơn nghỉ phép', exact=True)).to_be_visible()
                            page.wait_for_timeout(400)  # Complete the sheet's slide before measuring viewport bounds.
                            # The sheet must retain the full text, without line clamps, and scroll to the end.
                            full = page.get_by_text(LONG_REASON, exact=True).last
                            assert full.evaluate("el=>!['2','3'].includes(getComputedStyle(el).webkitLineClamp)")
                            full.evaluate("el=>{for(let p=el.parentElement;p;p=p.parentElement){if(p.scrollHeight>p.clientHeight&&['auto','scroll'].includes(getComputedStyle(p).overflowY)){p.scrollTop=p.scrollHeight;break;}}}")
                            end = full.evaluate("el=>{const range=document.createRange(); range.selectNodeContents(el); range.setStart(el.firstChild,el.firstChild.length-11); const r=range.getBoundingClientRect(); return {top:r.top,bottom:r.bottom};}")
                            page.screenshot(path=str(out/(prefix+'_details-end.png')))
                            assert end['top'] >= 0 and end['bottom'] <= height, end
                            page.get_by_role('button', name='Đóng chi tiết', exact=True).click()
                            approve.click()
                            expect(page.get_by_role('heading', name='Duyệt đơn nghỉ phép?', exact=True)).to_be_visible()
                            # A confirm sheet is exercised without sending any decision.
                            case['overlay'] = page.get_by_role('button', name='Xác nhận', exact=True).evaluate("""el=>{
                                for(let p=el;p;p=p.parentElement){const c=getComputedStyle(p).backgroundColor;
                                    if(c.startsWith('rgba(')&&c!=='rgba(0, 0, 0, 0)') return c;}
                                return null;}""")
                            assert case['overlay'] == 'rgba(0, 0, 0, 0.35)', case
                            page.screenshot(path=str(out/(prefix+'_confirm.png')))
                            page.get_by_role('button', name='Quay lại', exact=True).click()
                        page.get_by_role('tab', name='Thêm', exact=True).click()
                        search = page.get_by_role('textbox', name='Tìm nghiệp vụ', exact=True)
                        for query, label in [('cham cong', 'Chấm công'), ('dang ky', 'Đăng ký QA'), ('bang cong', 'Bảng công'), ('ChẤm CÔng', 'Chấm công')]:
                            search.fill(query)
                            page.wait_for_timeout(100)
                            found = page.get_by_role('button', name=label, exact=True).count() > 0
                            case.setdefault('searches', []).append(dict(query=query, found=found))
                            if args.phase == 'after':
                                assert found, (query, label)
                        search.fill('cham cong')
                        page.wait_for_timeout(100)
                        page.screenshot(path=str(out/(prefix+'_more-search.png')))
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.get_by_role('tablist').screenshot(path=str(out/(prefix+'_tabs.png')))
                    finally:
                        context.close()
            finally:
                browser.close()
        assert not errors, errors
    except Exception as error:
        report['failure'] = dict(type=type(error).__name__, message=str(error)[:2000])
        raise
    finally:
        (out/'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if args.phase == 'before':
        assert cases[0]['action_bottom'] > cases[0]['tab_top']
        assert not cases[0]['details_available']
        assert all(x['font'] == 11 for x in cases[0]['tab_labels'])
        assert not any(x['found'] for x in cases[0]['searches'][:3])
    print(json.dumps(dict(phase=args.phase, cases=len(cases), page_errors=errors)))


if __name__ == '__main__':
    main()
