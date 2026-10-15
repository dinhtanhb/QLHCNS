"""Check report presentation and keyboard filtering on a marked external demo."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--packages-dir', required=True, type=Path)
    parser.add_argument('--port', required=True, type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if root == folder or root in folder.parents:
        parser.error('Synthetic runtime must be outside source.')
    if json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    password = next(x.split(': ', 1)[1] for x in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
    output = folder/'headcount-design-uat'
    output.mkdir(exist_ok=True)
    report = {'synthetic_only': True, 'checks': [], 'errors': [], 'screenshots': []}

    def check(condition, label):
        report['checks'].append(label)
        if not condition:
            report['errors'].append(label)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        for role in ('hr', 'director'):
            context = browser.new_context(viewport={'width': 1440, 'height': 900}, service_workers='block', reduced_motion='reduce')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            base = f'http://127.0.0.1:{args.port}'
            page.goto(base+'/portal/login/')
            page.locator('[name=username]').fill('demo-'+role)
            page.locator('[name=password]').fill(password)
            page.locator('main form button[type=submit]').click()
            page.wait_for_load_state('networkidle')
            for width in (1756, 1440, 1280, 1024, 768, 390):
                page.set_viewport_size({'width': width, 'height': 900})
                for theme in ('light', 'dark'):
                    page.evaluate('(t)=>{document.documentElement.dataset.theme=t;localStorage.setItem("ihrms-theme",t)}', theme)
                    response = page.goto(base+'/portal/reports/headcount/?year=2026', wait_until='networkidle')
                    label = f'{role} {width} {theme}'
                    check(response.status == 200, label+' report opens')
                    result = page.locator('.headcount-report').evaluate(r'''root=>{
                        const style=x=>getComputedStyle(x), rect=x=>x.getBoundingClientRect();
                        const h1=root.querySelector('h1'),card=root.querySelector('.ui-card'),field=root.querySelector('label'),select=root.querySelector('select');
                        const cells=[...root.querySelectorAll('.headcount-number')];
                        return {
                          noOverflow:document.documentElement.scrollWidth<=innerWidth+1,
                          heading:style(h1).fontSize==='24px'&&style(h1).lineHeight==='32px',
                          padding:['paddingTop','paddingRight','paddingBottom','paddingLeft'].every(k=>parseFloat(style(card)[k])>=19.5),
                          labelGap:Math.abs(rect(select).top-rect(field).bottom-8)<=1,
                          numeric:cells.every(x=>style(x).textAlign==='right'&&style(x).fontVariantNumeric.includes('tabular-nums')),
                          rows:[...root.querySelectorAll('tbody tr')].every(x=>rect(x).height>=43.5),
                          labels:[...root.querySelectorAll('td[data-value]')].every(x=>{const n=Number(x.dataset.value),text=x.querySelector('.headcount-gap').textContent;return text.includes(n<0?'Vượt':n>0?'Thiếu':'Đủ')&&Number(x.querySelector('.headcount-gap-raw').textContent.replaceAll('.',''))===n}),
                          shadow:style(card).boxShadow==='none'
                        };
                    }''')
                    for criterion, passed in result.items():
                        check(passed, label+' '+criterion)
                    scroll = page.locator('.headcount-scroll')
                    scroll.focus()
                    check(scroll.evaluate('x=>x===document.activeElement&&getComputedStyle(x).outlineWidth==="3px"'), label+' keyboard focus3px')
                    if width == 390:
                        scroll.evaluate('x=>{x.scrollLeft=0}')
                        page.keyboard.press('ArrowRight')
                        page.wait_for_function('document.querySelector(".headcount-scroll").scrollLeft>0')
                        check(scroll.evaluate('x=>x.scrollLeft>0'), label+' keyboard scrolls table')
                    if width in (1756, 1440, 390):
                        page.locator('h1').evaluate('x=>{x.tabIndex=-1;x.focus();scrollTo(0,0)}')
                        path = output/f'{role}-{width}-{theme}.png'
                        page.screenshot(path=str(path), full_page=True)
                        report['screenshots'].append(path.name)
            page.set_viewport_size({'width':1440,'height':900})
            page.goto(base+'/portal/reports/headcount/?year=2026', wait_until='networkidle')
            select = page.locator('[name=year]')
            select.select_option('2025')
            select.focus()
            page.keyboard.press('Tab')
            check(page.locator('.headcount-report button[type=submit]').evaluate('x=>x===document.activeElement'), role+' filter Tab order')
            with page.expect_navigation(wait_until='networkidle'):
                page.keyboard.press('Enter')
            page.wait_for_load_state('networkidle')
            check('year=2025' in page.url and page.locator('[name=year]').input_value() == '2025', role+' keyboard applies year')
            page.get_by_role('link', name='Xóa lọc', exact=True).click()
            page.wait_for_load_state('networkidle')
            check('year=' not in page.url, role+' reset preserves route')
            context.close()
        browser.close()
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']),'screenshots':len(report['screenshots']),'errors':report['errors']}))
    return bool(report['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
