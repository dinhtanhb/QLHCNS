"""Measure all filter bars in real Edge on marked synthetic data, before and after."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--packages-dir',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8767)
    parser.add_argument('--baseline-port',type=int,default=8768)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    folder=args.directory.resolve()
    if folder==root or root in folder.parents:
        parser.error('Synthetic runtime must be outside source.')
    if json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    password=next(line.split(': ',1)[1] for line in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    sys.path.insert(0,str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    output=folder/'inline-filter-uat';output.mkdir(exist_ok=True)
    routes={
        'decisions':'/portal/hr-decisions/?q=DEMO',
        'employees':'/portal/hr/employees/?q=DEMO',
        'timesheet':'/portal/timesheet/?month=10&year=2026',
        'reports':'/portal/reports/?from_date=2026-01-01&to_date=2026-10-13',
        'catalog':'/portal/hcns-forms/?employee_id=1',
        'activity':'/portal/project-activities/?month=2026-10',
        'calendar':'/portal/project-activities/calendar/?month=2026-10',
        'people':'/portal/dashboard/people/?metric=active&q=DEMO',
        'dispatch':'/portal/dispatches/?q=DEMO',
        'kpi':'/portal/kpi/score/?period=1',
        'budget':'/portal/reports/budget/?year=2026',
        'headcount':'/portal/reports/headcount/?year=2026',
        'changes':'/portal/reports/personnel-changes/?from_date=2026-01-01&to_date=2026-10-13',
        'report-timesheet':'/portal/reports/timesheet/?month=10&year=2026',
        'admin':'/admin/contract/contract/?q=DEMO',
    }
    report={'checks':[],'failures':[],'measurements':{},'synthetic_only':True}
    def check(ok,label):report['checks' if ok else 'failures'].append(label)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        for version,port in (('before',args.baseline_port),('after',args.port)):
            context=browser.new_context(service_workers='block',reduced_motion='reduce')
            page=context.new_page();base=f'http://127.0.0.1:{port}'
            page.goto(base+'/portal/login/')
            page.locator('[name=username]').fill('demo-layout-admin')
            page.locator('[name=password]').fill(password)
            page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
            for name,route in routes.items():
                page.set_viewport_size({'width':1920,'height':1000})
                response=page.goto(base+route,wait_until='networkidle')
                if response.status!=200:raise AssertionError(name+' response '+str(response.status))
                for width in (1920,1440,1024,768,390):
                    page.set_viewport_size({'width':width,'height':1000})
                    for theme in ('light','dark'):
                        page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                        page.wait_for_timeout(30)
                        key=f'{version} {name} {width} {theme}'
                        selector='#changelist-search' if name=='admin' else '.ui-query-bar'
                        form=page.locator(selector)
                        geometry=form.evaluate('''f=>{
                            const xs=[...f.querySelectorAll('input:not([type=hidden]):not([type=submit]),select')].filter(x=>x.checkVisibility());
                            if(!xs.length)return {missingFields:true,html:f.outerHTML.slice(0,2000)};
                            const b=xs.at(-1).getBoundingClientRect();
                            const button=f.querySelector('button[type=submit],button:not([type]),input[type=submit]');const a=button.getBoundingClientRect();
                            const reset=f.querySelector('.ui-query-actions a');
                            return {gap:a.left-b.right,baseline:Math.abs(a.bottom-b.bottom),height:a.height,
                              wrapped:a.top>=b.bottom,resetSameRow:!reset||Math.abs(reset.getBoundingClientRect().top-a.top)<=1,
                              font:parseFloat(getComputedStyle(button).fontSize),
                              labelFont:[...f.querySelectorAll('label')].every(x=>parseFloat(getComputedStyle(x).fontSize)>=14),
                              mobileWidth:innerWidth>=600||xs.every(x=>Math.abs(x.getBoundingClientRect().width-f.getBoundingClientRect().width)<=2),
                              overflow:document.documentElement.scrollWidth>innerWidth+1,
                              labels:xs.every(x=>!!f.querySelector('label[for="'+x.id+'"]'))};
                        }''')
                        report['measurements'][key]=geometry
                        if geometry.get('missingFields'):
                            if version=='after':check(False,key+' fields visible')
                            continue
                        if version=='after':
                            check(not geometry['overflow'],key+' no overflow')
                            check(geometry['height']>=44 and geometry['font']>=14,key+' control size/font')
                            check(geometry['wrapped'] or geometry['baseline']<=1 and 0<=geometry['gap']<=17,key+' action follows final field')
                            if name!='admin':
                                check(geometry['labels'],key+' labels')
                                check(geometry['labelFont'],key+' readable label font')
                                check(geometry['wrapped'] or geometry['baseline']<=1 and 0<=geometry['gap']<=17,key+' inline gap/baseline')
                                check(width>=600 or geometry['resetSameRow'],key+' mobile same row')
                                check(geometry['mobileWidth'],key+' mobile full-width fields')
                                check(form.get_by_role('button',name='Áp dụng',exact=True).count()==1,key+' single apply')
                                check(form.get_by_role('link',name='Xóa lọc',exact=True).count()==1,key+' reset present')
                                button=form.get_by_role('button',name='Áp dụng',exact=True);button.focus()
                                check(button.evaluate('x=>getComputedStyle(x).outlineStyle!="none" && parseFloat(getComputedStyle(x).outlineWidth)>=3'),key+' keyboard focus')
                        if width in (1920,390) and theme=='light' and name in ('decisions','employees','timesheet','reports','catalog','admin'):
                            page.screenshot(path=str(output/f'{version}-{name}-{width}.png'),full_page=True)
                if version=='after' and name!='admin':
                    page.set_viewport_size({'width':1440,'height':1000})
                    # Enter submits the native GET. Check reset URL and retained field values.
                    fields=form.locator('[name]').evaluate_all('xs=>xs.map(x=>[x.name,x.value])')
                    button=form.get_by_role('button',name='Áp dụng',exact=True)
                    text_field=form.locator('input[type=text]')
                    if text_field.count():text_field.first.focus()
                    else:button.focus()
                    with page.expect_navigation(wait_until='networkidle'):page.keyboard.press('Enter')
                    from urllib.parse import parse_qs,urlsplit
                    query=parse_qs(urlsplit(page.url).query,keep_blank_values=True)
                    check(all(query.get(k,[None])[0]==v for k,v in fields),name+' Enter GET retains fields')
                    reset=page.locator('.ui-query-actions a')
                    href=page.url
                    if reset.count():
                        href=reset.get_attribute('href')
                        with page.expect_navigation(wait_until='networkidle'):reset.click()
                    check(not page.locator('.ui-query-actions a').count(),name+' reset clears applied filters')
                    cleared=parse_qs(urlsplit(href).query)
                    check(all(k not in cleared for k,v in fields if k not in ('metric','on_date')),name+' reset URL excludes filters')
            context.close()
        browser.close()
    report['passed']=not report['failures']
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']),'measurements':len(report['measurements']),'failures':report['failures']},ensure_ascii=False))
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
