"""Verify Home KPI wording for both roles on a marked, external synthetic QA."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect

from check_mobile_kpi_limit import ROOT, check_limits


def scope_for(role, limit):
    total = 'Bản ghi chấm công và Cần duyệt' if role == 'manager' else 'Bản ghi chấm công'
    return f'{total} tính trên toàn bộ dữ liệu. Các số ghi “gần nhất” chỉ tính trên {limit} bản ghi mới nhất.'


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
    cases, errors = [], []
    report = {'synthetic_only': True, 'qa': str(qa), 'backend': args.url, 'backend_page_size': backend_limit,
              'ui_copy_limit': limit, 'read_responses': 'Controlled first pages; real QA login and role checks',
              'cases': cases, 'page_errors': errors, 'native_tested': False}
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
                                    expected = [
                                        ('Bản ghi chấm công', str(limit+12)),
                                        (f'Giờ làm ({limit} bản ghi gần nhất)', str(8*(limit-1)+2)),
                                        (f'Đơn chờ ({limit} đơn gần nhất)', str(min(3, limit))),
                                        ('Cần duyệt', str(limit+1)) if role == 'manager'
                                        else (f'Chưa đọc ({limit} thông báo gần nhất)', str(min(4, limit))),
                                    ]
                                    heights = []
                                    for label, value in expected:
                                        label_node = page.get_by_text(label, exact=True)
                                        expect(label_node).to_be_visible()
                                        card = label_node.locator('..').locator('..').locator('..')
                                        expect(card.get_by_text(value, exact=True)).to_be_visible()
                                        box, label_box = card.bounding_box(), label_node.bounding_box()
                                        assert label_box['y']+label_box['height'] <= box['y']+box['height'], label
                                        assert box['x'] >= 15 and box['x']+box['width'] <= width-15, box
                                        assert label_node.evaluate("el=>el.scrollWidth<=el.clientWidth+1 && el.scrollHeight<=el.clientHeight+1 && ['', 'none', '0'].includes(getComputedStyle(el).webkitLineClamp)"), label
                                        heights.append(box['height'])
                                    assert max(heights)-min(heights) <= 1, heights
                                    scope = scope_for(role, limit)
                                    expect(page.get_by_text(scope, exact=True)).to_have_count(1)
                                    other_role = 'employee' if role == 'manager' else 'manager'
                                    expect(page.get_by_text(scope_for(other_role, limit), exact=True)).to_have_count(0)
                                    for old_label in ('Ngày công', 'Giờ gần đây'):
                                        expect(page.get_by_text(old_label, exact=True)).to_have_count(0)
                                    expect(page.get_by_text(re.compile('trang đầu danh sách đã tải'))).to_have_count(0)
                                    color = palettes[palette][mode]['surface'].lstrip('#')
                                    rgb = 'rgb('+', '.join(str(int(color[i:i+2], 16)) for i in (0, 2, 4))+')'
                                    first_card = page.get_by_text(expected[0][0], exact=True).locator('..').locator('..').locator('..')
                                    expect(first_card).to_have_css('background-color', rgb)
                                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                                    filename = f'{palette}_{mode}_{role}_{width}_home.png'
                                    page.screenshot(path=str(out/filename), full_page=True)
                                    page.get_by_text(scope, exact=True).scroll_into_view_if_needed()
                                    expect(page.get_by_text(scope, exact=True)).to_be_visible()
                                    scope_file = f'{palette}_{mode}_{role}_{width}_scope.png'
                                    page.screenshot(path=str(out/scope_file), full_page=True)
                                    cases.append({'palette': palette, 'mode': mode, 'role': role, 'width': width, 'height': height,
                                                  'file': filename, 'scope_file': scope_file, 'card_heights': heights,
                                                  'unchanged_values': dict(expected), 'scope': scope,
                                                  'no_horizontal_overflow': True, 'no_kpi_label_clamping': True})
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
                      'ui_copy_limit': limit, 'unchanged_values_verified': True}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
