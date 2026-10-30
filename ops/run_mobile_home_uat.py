"""Verify Home KPI wording for both roles on a marked, external synthetic QA."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect

from check_mobile_kpi_limit import ROOT, check_limits


def metric_specs(role, limit):
    return [('Bản ghi chấm công', 'Toàn bộ dữ liệu'), ('Giờ làm', f'{limit} bản ghi gần nhất'),
            ('Đơn chờ', f'{limit} đơn gần nhất'), ('Cần duyệt', 'Toàn bộ dữ liệu') if role == 'manager'
            else ('Chưa đọc', f'{limit} thông báo gần nhất')]


def assert_home_summary(page, role, limit, expected_values=None, muted_color=None, normal_font=True):
    """Shared by the matrix and live settings UAT, with independent UI expectations."""
    heights, metrics = [], []
    for label, scope in metric_specs(role, limit):
        label_node = page.get_by_text(label, exact=True)
        expect(label_node).to_be_visible()
        summary = label_node.locator('..').locator('..')
        card = summary.locator('..')
        expect(summary).to_have_attribute('aria-label', re.compile('^'+re.escape(f'{label}, {scope}, ')+'.+$'))
        expect(summary).not_to_have_attribute('aria-label', re.compile(', —$'))
        name = summary.get_attribute('aria-label')
        value = expected_values[label] if expected_values is not None else name.rsplit(', ', 1)[1]
        expect(summary).to_have_attribute('aria-label', f'{label}, {scope}, {value}')
        expect(card.get_by_text(value, exact=True)).to_be_visible()
        scope_node = card.get_by_text(scope, exact=True)
        expect(scope_node).to_be_visible()
        box = card.bounding_box()
        for node in (label_node, scope_node):
            text_box = node.bounding_box()
            assert text_box['y']+text_box['height'] <= box['y']+box['height'], label
            assert node.evaluate("el=>el.scrollWidth<=el.clientWidth+1 && el.scrollHeight<=el.clientHeight+1 && ['', 'none', '0'].includes(getComputedStyle(el).webkitLineClamp)"), label
        if normal_font:
            assert label_node.evaluate('el=>el.getBoundingClientRect().height<=parseFloat(getComputedStyle(el).lineHeight)+1'), label
        assert scope_node.evaluate('el=>parseFloat(getComputedStyle(el).fontSize)>=12'), label
        if muted_color:
            expect(scope_node).to_have_css('color', muted_color)
        assert box['x'] >= 15 and box['x']+box['width'] <= page.viewport_size['width']-15, box
        heights.append(box['height'])
        metrics.append({'label': label, 'scope': scope, 'value': value, 'accessibility_name': name})
    assert max(heights)-min(heights) <= 1, heights
    expect(page.get_by_text('Chưa đọc' if role == 'manager' else 'Cần duyệt', exact=True)).to_have_count(0)
    expect(page.get_by_text(re.compile('Các số ghi|trang đầu danh sách đã tải'))).to_have_count(0)
    actions = []
    for label in ('Tạo đơn nghỉ', 'Chấm công'):
        button = page.get_by_role('button', name=label, exact=True)
        expect(button).to_be_visible()
        assert button.get_by_text(label, exact=True).evaluate('el=>el.getBoundingClientRect().height<=parseFloat(getComputedStyle(el).lineHeight)+1'), label
        actions.append(button.bounding_box())
    assert abs(actions[0]['y']-actions[1]['y']) <= 1 and abs(actions[0]['height']-actions[1]['height']) <= 1, actions
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
    return {'card_heights': heights, 'metrics': metrics, 'actions': actions,
            'no_horizontal_overflow': True, 'no_kpi_label_clamping': True, 'actions_one_line': True}


def fixtures_for(limit):
    attendance = [{'id': 1000+i, 'date': '2026-01-12', 'check_in': None, 'check_out': None,
                   'hours': '8.00' if i < limit-1 else '2.00', 'status_label': 'Đủ công'} for i in range(limit)]
    leaves = [{'id': 2000+i, 'employee_name': 'Nhân viên QA', 'leave_type': 'Phép năm QA',
               'from_date': '2026-01-12', 'to_date': '2026-01-12', 'total_days': '1.0',
               'reason': 'Dữ liệu giả kiểm tra nhãn KPI', 'status': 'Pending' if i < 3 else 'Approved',
               'status_label': 'Chờ duyệt' if i < 3 else 'Đã duyệt'} for i in range(limit)]
    notices = [{'id': 3000+i, 'title': 'Thông báo QA', 'message': 'Dữ liệu giả kiểm tra phạm vi số liệu',
                'is_read': i >= 4, 'created_at': '2026-01-01T12:00:00Z', 'destination': None} for i in range(limit)]
    def page(items, count):
        return {'items': items, 'count': count, 'page': 1, 'has_next': True}
    return {
        'attendance': page(attendance, limit+12), 'leaves': page(leaves, limit+43),
        'notifications': page(notices, limit+34),
        'approvals': page([{**row, 'status': 'Pending', 'status_label': 'Chờ duyệt'} for row in leaves], limit+1),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True, help='Existing synthetic mobile QA directory')
    parser.add_argument('--url', required=True, help='Loopback origin serving the QA backend and mobile web export')
    parser.add_argument('--output', type=Path, required=True, help='Evidence directory outside the repository')
    parser.add_argument('--channel', default='msedge', help='Installed Playwright browser channel')
    args = parser.parse_args()
    qa, out = args.directory.resolve(), args.output.resolve()
    if any(path == ROOT or ROOT in path.parents for path in (qa, out)) or qa == out:
        parser.error('QA data and evidence must be separate directories outside the repository')
    origin = urlsplit(args.url)
    if (origin.scheme not in ('http', 'https') or origin.hostname not in ('127.0.0.1', 'localhost', '::1')
            or origin.username or origin.password or origin.query or origin.fragment or origin.path not in ('', '/')):
        parser.error('--url must be a loopback QA origin without credentials, query or path')
    for marker in ('synthetic-demo.json', 'mobile-qa.json'):
        if json.loads((qa/marker).read_text(encoding='utf-8')).get('synthetic_only') is not True:
            parser.error('Unverified synthetic QA directory')
    password = next(line.split(': ', 1)[1] for line in (qa/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines()
                    if 'Mật khẩu chung' in line)
    limit, backend_limit = check_limits()
    fixtures = fixtures_for(limit)
    palettes = json.loads((ROOT/'mobile/src/palettes.json').read_text(encoding='utf-8'))
    out.mkdir(parents=True, exist_ok=True)
    cases, errors, large_kpi_text = [], [], []
    report = {'synthetic_only': True, 'qa': str(qa), 'backend': args.url, 'backend_page_size': backend_limit,
              'ui_copy_limit': limit, 'read_responses': 'Controlled first pages; real QA login and role checks',
              'cases': cases, 'large_kpi_text_web_simulation': large_kpi_text,
              'page_errors': errors, 'native_tested': False}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=args.channel, headless=True)
            try:
                for palette in ('viethealth', 'chamdong', 'thanam'):
                    for mode in ('light', 'dark'):
                        for role in ('employee', 'manager'):
                            for width, height in ((360, 800), (390, 844), (412, 915)):
                                context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=mode)
                                try:
                                    page = context.new_page()
                                    page.on('pageerror', lambda error: errors.append(str(error)))
                                    def me_response(route):
                                        response = route.fetch()
                                        data = response.json()
                                        assert data['can_approve'] == (role == 'manager'), 'QA role mismatch'
                                        data['palette'] = palette
                                        route.fulfill(response=response, json=data)
                                    page.route('**/api/mobile/v1/me/', me_response)
                                    for resource, fixture in fixtures.items():
                                        page.route('**/api/mobile/v1/'+resource+'/**',
                                                   lambda route, request, body=fixture: route.fulfill(json=body))
                                    page.goto(args.url)
                                    page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill('demo-'+role)
                                    page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
                                    page.get_by_role('button', name='Đăng nhập', exact=True).click()
                                    expect(page.get_by_role('heading', name='Trang chủ', exact=True)).to_be_visible(timeout=20000)
                                    expected = {'Bản ghi chấm công': str(limit+12), 'Giờ làm': str(8*(limit-1)+2),
                                                'Đơn chờ': str(min(3, limit)),
                                                **({'Cần duyệt': str(limit+1)} if role == 'manager' else {'Chưa đọc': str(min(4, limit))})}
                                    def rgb(hex_color):
                                        color = hex_color.lstrip('#')
                                        return 'rgb('+', '.join(str(int(color[i:i+2], 16)) for i in (0, 2, 4))+')'
                                    measured = assert_home_summary(page, role, limit, expected, rgb(palettes[palette][mode]['muted']))
                                    for old_label in ('Ngày công', 'Giờ gần đây'):
                                        expect(page.get_by_text(old_label, exact=True)).to_have_count(0)
                                    expect(page.get_by_text(re.compile('trang đầu danh sách đã tải'))).to_have_count(0)
                                    first_card = page.get_by_text('Bản ghi chấm công', exact=True).locator('..').locator('..').locator('..')
                                    expect(first_card).to_have_css('background-color', rgb(palettes[palette][mode]['surface']))
                                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                                    filename = f'{palette}_{mode}_{role}_{width}_home.png'
                                    page.screenshot(path=str(out/filename), full_page=True)
                                    keyboard_actions = False
                                    if width == 360 and palette == 'viethealth' and mode == 'light':
                                        page.get_by_role('button', name='Tạo đơn nghỉ', exact=True).focus()
                                        page.keyboard.press('Tab')
                                        attendance_button = page.get_by_role('button', name='Chấm công', exact=True)
                                        expect(attendance_button).to_be_focused()
                                        attendance_button.evaluate('el=>el.blur()')
                                        keyboard_actions = True
                                    cases.append({'palette': palette, 'mode': mode, 'role': role, 'width': width, 'height': height,
                                                  'file': filename, 'unchanged_values': expected,
                                                  'keyboard_actions_checked': keyboard_actions, **measured})
                                    if width == 360:
                                        # Approximate larger KPI text on web; this is not native font-scale certification.
                                        for label, scope in metric_specs(role, limit):
                                            summary = page.get_by_label(f'{label}, {scope}, {expected[label]}', exact=True)
                                            for text in (label, scope, expected[label]):
                                                summary.get_by_text(text, exact=True).evaluate("el=>{const s=getComputedStyle(el);const size=parseFloat(s.fontSize),line=parseFloat(s.lineHeight);el.style.fontSize=(size*2)+'px';el.style.lineHeight=(line*2)+'px';}")
                                        for attempt in range(10):
                                            page.wait_for_timeout(100)
                                            try:
                                                enlarged = assert_home_summary(page, role, limit, expected,
                                                                               rgb(palettes[palette][mode]['muted']), normal_font=False)
                                                break
                                            except AssertionError:
                                                if attempt == 9:
                                                    raise
                                        large_file = f'{palette}_{mode}_{role}_{width}_kpi-text-200.png'
                                        page.screenshot(path=str(out/large_file), full_page=True)
                                        large_kpi_text.append({'palette': palette, 'mode': mode, 'role': role,
                                                               'file': large_file, 'kpi_text_css_scale': 2, **enlarged})
                                finally:
                                    context.close()
            finally:
                browser.close()
        assert not errors, errors
    except Exception as error:
        report['failure'] = {'type': type(error).__name__, 'message': str(error)[:1500]}
        raise
    finally:
        report['count'] = len(cases)
        (out/'home-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'cases': len(cases), 'page_errors': errors, 'backend_page_size': backend_limit,
                      'ui_copy_limit': limit, 'unchanged_values_verified': True,
                      'large_kpi_text_web_cases': len(large_kpi_text)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
