"""Real Edge phase-two read flows on an explicitly marked synthetic demo."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    folder = args.directory.resolve()
    root = Path(__file__).resolve().parents[1]
    if folder == root or root in folder.parents:
        parser.error('Synthetic runtime must be outside the repository.')
    if json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
        raise RuntimeError('Synthetic demo marker required')
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    password = next(line.split(': ', 1)[1] for line in (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    output = folder / 'dashboard-phase2-uat'
    output.mkdir(exist_ok=True)
    report = {'checks': [], 'errors': [], 'screenshots': [], 'synthetic_only': True}
    base = f'http://127.0.0.1:{args.port}'

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        report['checks'].append(label)

    expected = {
        'hr': {'own_leave', 'global_leave', 'history', 'postings', 'candidates', 'joined', 'requests'},
        'hr-officer': {'own_leave', 'history', 'candidates', 'joined'},
        'manager': {'own_leave', 'joined', 'requests'},
        'director': {'own_leave', 'global_leave', 'history', 'postings', 'joined'},
        'employee': {'own_leave'},
    }
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            for role, allowed in expected.items():
                context = browser.new_context(viewport={'width':1440, 'height':1000}, service_workers='block', reduced_motion='reduce')
                page = context.new_page()
                page.on('pageerror', lambda error: report['errors'].append(str(error)))
                page.goto(base + '/portal/login/')
                page.locator('[name=username]').fill('demo-' + role)
                page.locator('[name=password]').fill(password)
                page.locator('main form button[type=submit]').click()
                page.wait_for_load_state('networkidle')
                check(page.url.endswith('/portal/'), role + ' actual login')
                for width in (1920,1440,1024,768,360):
                    page.set_viewport_size({'width':width,'height':1000})
                    for theme in ('light','dark'):
                        page.evaluate('(t)=>{document.documentElement.dataset.theme=t;localStorage.setItem("ihrms-theme",t)}', theme)
                        response = page.goto(base + '/portal/', wait_until='networkidle')
                        label = f'{role} {width} {theme}'
                        check(response.status == 200, label + ' HTTP200')
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), label + ' no page overflow')
                        for key in expected['hr']:
                            check(bool(page.locator('#phase2-' + key).count()) == (key in allowed), label + ' scope ' + key)
                        text = page.locator('main').inner_text()
                        check('Thai sản' in text if role in ('hr','hr-officer') else 'Thai sản' not in text, label + ' leave type privacy')
                        check('SYNTHETIC_PRIVATE' not in page.content(), label + ' private sentinels absent')
                        check(page.locator('#dashboard-status .ui-kpi').count() == (4 if role in ('hr','director') else 3 if role in ('hr-officer','manager') else 0), label + ' original KPI count')
                        small = page.locator('main :is(p,span,strong,small,label,a,button,input,summary,th,td,h1,h2,time,dt,dd)').evaluate_all('''xs=>xs.filter(x=>{
                            const r=x.getBoundingClientRect();return x.checkVisibility()&&r.width&&r.height&&x.textContent.trim()&&!x.closest('svg')&&parseFloat(getComputedStyle(x).fontSize)<14;
                        }).map(x=>({tag:x.tagName,cls:x.className,size:getComputedStyle(x).fontSize}))''')
                        check(not small, label + ' text >=14px ' + str(small))
                        short = page.locator('main :is(button,input,select,a.ui-button,a.dashboard-text-link,summary)').evaluate_all('''xs=>xs.filter(x=>{
                            const r=x.getBoundingClientRect();return x.checkVisibility()&&r.width&&r.height&&r.height<43.5&&x.type!=='hidden';
                        }).map(x=>({tag:x.tagName,cls:x.className,height:x.getBoundingClientRect().height}))''')
                        check(not short, label + ' targets >=44px ' + str(short))
                        check(page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches'), label + ' reduced motion')
                        if 'joined' in allowed:
                            count = page.locator('#phase2-joined .ui-kpi-value').inner_text()
                            with page.expect_navigation(wait_until='networkidle'):
                                page.locator('#phase2-joined a.ui-kpi').click()
                            check('metric=joined' in page.url and page.locator('main').inner_text().find('Nhân sự vào làm trong tháng') >= 0, label + ' joined drill-down')
                            check(response.status == 200 and int(count) == page.locator('tbody tr').count(), label + ' joined rows match')
                            page.goto(base + '/portal/', wait_until='networkidle')
                        if 'history' in allowed:
                            history_link = page.locator('#phase2-history a').first
                            if history_link.count():
                                with page.expect_navigation(wait_until='networkidle'):
                                    history_link.click()
                                check('decisions' in page.url, label + ' decision detail link')
                                page.goto(base + '/portal/', wait_until='networkidle')
                        # Native summary: keyboard opens/closes without custom JS.
                        summary = page.locator('.dashboard-explanation summary').first
                        if summary.count():
                            summary.focus(); page.keyboard.press('Enter')
                            check(summary.evaluate('x=>x.parentElement.open'), label + ' Enter disclosure')
                            page.keyboard.press('Enter')
                            check(not summary.evaluate('x=>x.parentElement.open'), label + ' Enter close')
                        page.locator('#global-search-input').focus()
                        page.keyboard.press('Tab'); page.keyboard.press('Escape')
                        check(page.evaluate('document.activeElement !== document.body'), label + ' Tab/Escape focus retained')
                        name = f'{role}-{width}-{theme}.png'
                        page.screenshot(path=str(output / name), full_page=True)
                        report['screenshots'].append(name)
                context.close()
            browser.close()
        check(not report['errors'], 'No browser JavaScript errors')
    finally:
        (output / 'browser-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']), 'screenshots':len(report['screenshots']), 'errors':report['errors']}))


if __name__ == '__main__':
    main()
