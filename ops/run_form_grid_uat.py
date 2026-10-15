"""Check date enhancement, keyboard geometry and before/after contact sheets.

Requires a marked external synthetic runtime; never reads operational accounts.
"""
import argparse
import json
from pathlib import Path
import sys

from run_layout_alignment_audit import configure, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--pdf-packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8790)
    parser.add_argument('--baseline-port', type=int, default=8791)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('External synthetic runtime required.')
    configure(root, folder)
    sys.path[:0] = [str(args.packages_dir.resolve()), str(args.pdf_packages_dir.resolve())]
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw

    password = next(line.split(': ', 1)[1] for line in
        (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines()
        if line.startswith('Mật khẩu'))
    routes = {route['name'].split(':')[-1]: route['url']
        for route in inventory(None) if 'url' in route}
    samples = ('hr_employee_edit', 'hr_contract_create', 'personnel_decision_detail',
        'leave_create', 'hr_candidate_create', 'finance_dependent_list',
        'dispatch_create', 'kpi_assign_create', 'report_hub')
    output = folder / 'form-grid-uat'
    output.mkdir(exist_ok=True)
    report = {'synthetic_only':True, 'checks':[], 'failures':[], 'screenshots':[]}

    def check(ok, label):
        report['checks' if ok else 'failures'].append(label)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True)
        for phase, port in (('before', args.baseline_port), ('after', args.port)):
            context = browser.new_context(service_workers='block', reduced_motion='reduce')
            page = context.new_page()
            base = f'http://127.0.0.1:{port}'

            def login(account):
                context.clear_cookies()
                page.goto(base + '/portal/login/')
                page.locator('[name=username]').fill(account)
                page.locator('[name=password]').fill(password)
                page.locator('main form button[type=submit]').click()
                page.wait_for_load_state('networkidle')

            active_account = None
            for name in samples:
                account = 'demo-finance' if name == 'finance_dependent_list' else 'demo-hr'
                if account != active_account:
                    login(account)
                    active_account = account
                response = page.goto(base + routes[name], wait_until='networkidle')
                check(response.status == 200, phase + ' readable ' + name)
                if name in ('leave_create', 'hr_employee_edit', 'hr_contract_create', 'finance_dependent_list'):
                    check(page.locator('main form[method=post] input:not([type=hidden]):not(.ui-number-source)').count() > 0,
                        phase + ' real form visible ' + name)
                for width in (1756, 390):
                    page.set_viewport_size({'width':width, 'height':920})
                    page.evaluate("document.documentElement.dataset.theme='light'")
                    path = output / f'{phase}-{name}-{width}.png'
                    page.screenshot(path=str(path), full_page=True)
                    report['screenshots'].append(str(path))
            if phase == 'after':
                page.goto(base + routes['hr_employee_edit'], wait_until='networkidle')
                date = page.locator('[name=date_of_birth]')
                # Native date input name is preserved by the baseline contract.
                if not date.count():
                    date = page.locator('input[type=date]').first
                date.fill('2026-10-09')
                echo = date.evaluate('x=>document.getElementById(x.getAttribute("aria-describedby").split(" ").at(-1)).textContent')
                check(echo == 'Thứ Sáu, 09/10/2026', 'Vietnamese weekday and dd/mm/yyyy')
                check(date.get_attribute('lang') == 'vi', 'native date language')
                check(date.input_value() == '2026-10-09', 'ISO value unchanged')
                check(date.evaluate('x=>new FormData(x.form).get(x.name)') == '2026-10-09', 'ISO submitted value unchanged')
                date.fill('')
                check(date.evaluate('x=>x.nextElementSibling.textContent') == '', 'empty date clears echo')
                check(page.locator('main [id]').evaluate_all('xs=>new Set(xs.map(x=>x.id)).size===xs.length'), 'unique field and echo IDs')
                for theme in ('light','dark'):
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t', theme)
                    for width in (1756, 390):
                        page.set_viewport_size({'width':width,'height':920})
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), f'{theme}/{width} page fits')
                        fields = page.locator('main form input:not([type=hidden]):not(.ui-number-source),main form select').filter(visible=True)
                        if fields.count() > 1:
                            fields.first.focus()
                            page.keyboard.press('Tab')
                            check(fields.nth(1).evaluate('x=>x===document.activeElement'), f'{theme}/{width} Tab follows DOM')
                        fields.last.focus()
                        check(fields.last.evaluate('x=>{const r=x.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight-44}'), f'{theme}/{width} focus above action bar')
                login('demo-layout-admin')
                page.goto(base + '/portal/project-activities/', wait_until='networkidle')
                month = page.locator('input[type=month]').first
                if month.count():
                    month.fill('2026-10')
                    check('2026' in month.evaluate('x=>x.nextElementSibling.textContent'), 'month echo preserves year')
                    check(month.input_value() == '2026-10', 'native month ISO unchanged')
                else:
                    check(False, 'month control available for regression')
            context.close()
        browser.close()

    for width in (1756, 390):
        tile_width, tile_height = (560, 330) if width == 1756 else (240, 570)
        sheet = Image.new('RGB', (tile_width * 2, (tile_height + 30) * len(samples)), 'white')
        draw = ImageDraw.Draw(sheet)
        for row, name in enumerate(samples):
            y = row * (tile_height + 30)
            draw.text((8, y + 5), f'{name} / {width} - BEFORE | AFTER', fill='black')
            for col, phase in enumerate(('before','after')):
                with Image.open(output / f'{phase}-{name}-{width}.png') as original:
                    # Top viewport contact sheet; full page images remain alongside.
                    image = original.crop((0,0,original.width,min(920,original.height)))
                    image.thumbnail((tile_width,tile_height))
                    sheet.paste(image,(col*tile_width,y+25))
        sheet.save(output / f'contact-sheet-{width}.png')
    (output/'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']), 'failures':report['failures'], 'screenshots':len(report['screenshots'])}))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
