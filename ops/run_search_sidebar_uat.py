"""Live Edge search visibility checks on an explicitly marked isolated demo."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import quote

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory', type=Path, required=True)
parser.add_argument('--packages-dir', type=Path, required=True)
parser.add_argument('--port', type=int, default=8766)
args = parser.parse_args()
folder = args.directory.resolve()
assert json.loads((folder/'synthetic-demo.json').read_text()).get('synthetic_only') is True
password = next(line.split(': ',1)[1] for line in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
sys.path.insert(0, str(args.packages_dir.resolve()))
from playwright.sync_api import sync_playwright
output = folder/'sidebar-search-uat'
output.mkdir(exist_ok=True)
report = {'checks': [], 'errors': [], 'screenshots': [], 'synthetic_only': True}
base = f'http://127.0.0.1:{args.port}'

def check(value, label):
    if not value: raise AssertionError(label)
    report['checks'].append(label)

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='msedge', headless=True)
    for role in ('hr','employee','manager','director'):
        context = browser.new_context(viewport={'width':1440,'height':1000},service_workers='block')
        page = context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        page.goto(base+'/portal/login/')
        page.locator('[name=username]').fill('demo-'+role)
        page.locator('[name=password]').fill(password)
        with page.expect_navigation(wait_until='networkidle'):
            page.locator('main form button[type=submit]').click()
        check(page.url.endswith('/portal/'),'Login '+role)
        for width in (360,768,1024,1440):
            for theme in ('light','dark'):
                page.set_viewport_size({'width':width,'height':1000})
                page.evaluate('(t)=>{document.documentElement.dataset.theme=t;localStorage.setItem("ihrms-theme",t)}',theme)
                for query, href, visible in (
                    ('Nhân viên & hồ sơ nhân sự','/portal/hr/employees/', role=='hr'),
                    ('Biểu mẫu HCNS','/portal/hcns-forms/',role=='hr'),
                    ('Đề xuất tuyển dụng','/portal/recruitment/',role in ('hr','manager'))):
                    response = page.goto(base+'/portal/search/?q='+quote(query),wait_until='networkidle')
                    check(response.status==200, f'Search200 {role} {query} {width} {theme}')
                    found = page.locator('main a').evaluate_all('(xs)=>xs.map(a=>a.getAttribute("href"))')
                    check((href in found)==visible,f'Search visibility {role} {query} {width} {theme}')
                    check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'No overflow {role} {width} {theme}')
                    if visible:
                        check(page.locator('#portalSidebar a[href="'+href+'"]').count()>0,'Matches sidebar '+role+href)
                small = page.locator('body :is(p,span,strong,small,label,a,button,input,h1,h2)').evaluate_all('(xs)=>xs.filter(x=>x.checkVisibility()&&x.getBoundingClientRect().height&&x.textContent.trim()&&!x.closest("svg")&&parseFloat(getComputedStyle(x).fontSize)<14).map(x=>x.tagName)')
                check(not small,f'Text14px {role} {width} {theme}')
                controls = page.locator('body :is(button,input,select,a.ui-button)').evaluate_all('(xs)=>xs.filter(x=>x.checkVisibility()&&x.type!=="hidden"&&x.getBoundingClientRect().height<43.5).map(x=>x.tagName)')
                check(not controls,f'Controls44px {role} {width} {theme}')
                page.locator('#global-search-input').fill('nhan vien')
                with page.expect_navigation(wait_until='networkidle'): page.locator('#global-search-input').press('Enter')
                check(page.url.endswith('q=nhan+vien'),'Keyboard search '+role)
                name=f'{role}-{width}-{theme}.png'
                page.screenshot(path=str(output/name),full_page=True)
                report['screenshots'].append(name)
        context.close()
    check(not report['errors'],'No JavaScript errors')
    browser.close()
(output/'browser-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(report['checks']),'screenshots':len(report['screenshots']),'errors':report['errors']}))
