"""Real Edge read-flow checks on the isolated dashboard demo, not operational data."""
import argparse
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory', type=Path, required=True)
parser.add_argument('--packages-dir', type=Path, required=True)
parser.add_argument('--port', type=int, default=8766)
args = parser.parse_args()
folder = args.directory.resolve()
if json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
    raise RuntimeError('Synthetic demo marker required')
sys.path.insert(0, str(args.packages_dir.resolve()))
from playwright.sync_api import sync_playwright
password = next(s.split(': ', 1)[1] for s in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if s.startswith('Mật khẩu'))
output = folder/'phase2-search-uat'
output.mkdir(exist_ok=True)
report = {'checks': [], 'errors': [], 'screenshots': [], 'synthetic_only': True}
base = f'http://127.0.0.1:{args.port}'

def check(condition, label):
    if not condition:
        raise AssertionError(label)
    report['checks'].append(label)

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(viewport={'width':1440, 'height':1000}, service_workers='block')
    page = context.new_page()
    page.on('pageerror', lambda error: report['errors'].append(str(error)))
    page.goto(base+'/portal/login/')
    page.locator('[name=username]').fill('demo-hr')
    page.locator('[name=password]').fill(password)
    page.locator('main form button[type=submit]').click()
    page.wait_for_load_state('networkidle')
    check(page.url.endswith('/portal/'), 'Real Edge login')
    for width in (360,768,1024,1440):
        page.set_viewport_size({'width':width,'height':1000})
        for theme in ('light','dark'):
            page.evaluate('(t)=>{document.documentElement.dataset.theme=t;localStorage.setItem("ihrms-theme",t)}',theme)
            for route, label in (('/portal/','home'),('/portal/dashboard/people/?metric=managed','kpi-detail'),('/portal/search/?q=nguyen','search')):
                response=page.goto(base+route,wait_until='networkidle')
                check(response.status==200, f'{label} HTTP200 {width} {theme}')
                check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{label} no overflow {width} {theme}')
                small=page.locator('body :is(p,span,strong,small,label,a,button,input,summary,th,td,h1,h2)').evaluate_all('''(xs)=>xs.filter(x=>{
                    const s=getComputedStyle(x),r=x.getBoundingClientRect();return r.width&&r.height&&s.visibility!=="hidden"&&x.checkVisibility()&&x.textContent.trim()&&!x.closest("svg")&&parseFloat(s.fontSize)<14;
                }).map(x=>({tag:x.tagName,cls:x.className,size:getComputedStyle(x).fontSize}))''')
                check(not small,f'{label} visible text at least 14px {width} {theme}: {small}')
                short=page.locator('body :is(button,input,select,a.ui-button,summary)').evaluate_all('''(xs)=>xs.filter(x=>{
                    const r=x.getBoundingClientRect();return x.checkVisibility()&&r.width&&r.height&&r.height<43.5&&x.type!=="hidden";
                }).map(x=>({tag:x.tagName,cls:x.className,height:x.getBoundingClientRect().height}))''')
                check(not short,f'{label} controls at least 44px {width} {theme}: {short}')
                if label=='search':
                    check('Nguyễn Đặng' in page.locator('main').inner_text(),'Unaccented name result')
                page.locator('#global-search-input').focus()
                page.locator('#global-search-input').fill('NGUYEN')
                with page.expect_navigation(wait_until='networkidle'):
                    page.keyboard.press('Enter')
                check('Nguyễn Đặng' in page.locator('main').inner_text(),f'Keyboard search {label} {width} {theme}')
                page.goto(base+route,wait_until='networkidle')
                name=f'{label}-{width}-{theme}.png'
                page.screenshot(path=str(output/name),full_page=True)
                report['screenshots'].append(name)
    check(not report['errors'],'No browser JavaScript errors')
    context.close()
    browser.close()
(output/'browser-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(report['checks']),'screenshots':len(report['screenshots']),'errors':report['errors']}))
