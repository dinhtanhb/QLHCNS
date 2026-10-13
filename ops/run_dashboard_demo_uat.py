"""Live Edge checks of a synthetic instance created by dashboard_demo.py."""
import argparse
import json,sys,os
from pathlib import Path
from urllib.parse import quote
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory',type=Path,required=True)
parser.add_argument('--packages-dir',type=Path,required=True)
parser.add_argument('--port',type=int,default=8766)
args=parser.parse_args()
folder=args.directory.resolve()
packages=args.packages_dir.resolve()
if json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
 raise RuntimeError('Synthetic demo marker required')
sys.path.insert(0,str(packages))
from playwright.sync_api import sync_playwright
password=next(s.split(': ',1)[1] for s in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if s.startswith('Mật khẩu'))
report={'checks':[],'errors':[],'screenshots':[]}
def check(value,label):
 assert value,label
 report['checks'].append(label)
base=f'http://127.0.0.1:{args.port}'
(folder/'screenshots').mkdir(exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='msedge',headless=True)
 for user in ('hr','manager','employee','director','finance','hr-officer'):
  context=browser.new_context(viewport={'width':1440,'height':1000},service_workers='block')
  page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.goto(base+'/portal/login/')
  page.locator('[name=username]').fill('demo-'+user);page.locator('[name=password]').fill(password)
  page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
  check('/login/' not in page.url,'login '+user)
  if user=='hr':
   values=page.locator('#dashboard-status .ui-kpi-value').all_text_contents()
   check([x.strip() for x in values]==['22','17','2','3'],'KPI source totals 22/17/2/3')
   check(page.locator('.dashboard-slice').count()==4,'four contract types')
   check(page.locator('.dashboard-type-track > span').count()==4,'four contract share bars')
   check(page.locator('.dashboard-capacity li').count()==6,'six department rows')
   for i,count in enumerate((22,17,2,3)):
    page.goto(base+'/portal/');page.locator('#dashboard-status a.ui-kpi').nth(i).click();page.wait_for_load_state('networkidle')
    check(page.locator('tbody tr').count()==min(count,20),'KPI drilldown '+str(i))
  page.locator('#global-search-input').fill('@example.test');page.locator('.ui-global-search button').click();page.wait_for_load_state('networkidle')
  expected={'hr':20,'manager':5,'employee':1,'director':20,'finance':1,'hr-officer':20}[user]
  check(page.locator('main section').nth(1).locator('li').count()==expected,'scoped email search '+user)
  if user=='hr':
   page.locator('#global-search-input').fill('hop dong');page.locator('.ui-global-search button').click();page.wait_for_load_state('networkidle')
   page.locator('main a[href="/portal/hr/contracts/"]').click();page.wait_for_load_state('networkidle')
   check('Hợp đồng' in page.locator('main').inner_text(),'search destination contract page')
   for width in (360,390,768,1024,1440):
    for theme in ('light','dark'):
     page.set_viewport_size({'width':width,'height':1000})
     page.goto(base+'/portal/');page.evaluate('(theme)=>document.documentElement.setAttribute("data-theme",theme)',theme)
     check(page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),f'no overflow {width} {theme}')
     path=folder/'screenshots'/f'dashboard-{width}-{theme}.png';page.screenshot(path=str(path),full_page=True);report['screenshots'].append(path.name)
     page.locator('#global-search-input').focus();page.keyboard.type('demo001');page.keyboard.press('Enter');page.wait_for_load_state('networkidle')
     check('Nhân viên giả lập 01' in page.locator('main').inner_text(),f'keyboard search {width} {theme}')
  context.close()
 browser.close()
check(not report['errors'],'no JavaScript errors')
(folder/'browser-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(report['checks']),'checks passed')
