"""Project-wide browser evidence and form workflows on marked synthetic data."""
import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import sys
import uuid

from run_layout_alignment_audit import configure, inventory


def validate_coverage(audit, routes):
    """Reject partial matrices even when their measured subset is green."""
    accounts={'demo-layout-admin','demo-hr','demo-director','demo-manager','demo-employee','demo-finance','demo-hr-officer','demo-sys','demo-unlinked'}
    matrix={(w,t) for w in (1920,1756,1440,1280,1024,768,390) for t in ('light','dark')}
    if audit.get('phase')!='after' or audit.get('synthetic_only') is not True or audit.get('errors') or audit.get('violations'):
        return False
    names={route['name'] for route in routes}
    if {route['name'] for route in audit.get('routes',[])}!=names or any('unresolved' in route for route in audit['routes']):
        return False
    if {r['name']:r.get('url') for r in audit['routes']}!={r['name']:r.get('url') for r in routes}:return False
    cases=audit.get('cases',[])
    if {case['account'] for case in cases}!=accounts:return False
    for route in names:
        for account in accounts:
            group=[case for case in cases if case['route']==route and case['account']==account]
            measured=[case for case in group if 'width' in case]
            if measured:
                if len(group)!=14 or {(c['width'],c['theme']) for c in measured}!=matrix:return False
            elif len(group)!=1 or not group[0].get('skip') or group[0].get('error'):
                return False
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--packages-dir',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8800)
    parser.add_argument('--baseline-port',type=int,default=8801)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--flows-only',action='store_true')
    mode.add_argument('--evidence-only',action='store_true',help='Capture pages without repeating data-changing workflows; report explicitly records this mode.')
    parser.add_argument('--coverage-report',type=Path,help='Completed nine-role alignment result used to require representative page coverage.')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];folder=args.directory.resolve()
    if folder==root or root in folder.parents:parser.error('External runtime required')
    configure(root,folder)
    # Playwright's sync wrapper owns an event loop; this process only accesses
    # the explicitly marked disposable database, never application threads.
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE']='true'
    sys.path.insert(0,str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    from PIL import Image,ImageDraw
    from django.urls import reverse
    from django.utils import timezone
    from apps.asset.models import InventorySession
    from apps.office.models import RoomBooking
    from apps.planning.models import Event
    from apps.lifecycle.models import ChecklistTemplate
    for kind in ('Onboarding','Offboarding'):
        for index in range(5):
            ChecklistTemplate.objects.get_or_create(template_code=f'SYN-CHOICE-{kind}-{index}',defaults={'template_name':f'Đào mẫu giả lập {index}','template_type':kind})
    password=next(x.split(': ',1)[1] for x in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
    output=folder/'project-forms-uat';output.mkdir(exist_ok=True)
    report={'mode':'evidence-only' if args.evidence_only else 'flows-only' if args.flows_only else 'flows-and-evidence','synthetic_only':True,'checks':[],'failures':[],'pages':[],'excluded':[],'screenshots':[], 'representative_accounts':['demo-layout-admin','demo-hr','demo-finance'],'role_checks':[]}
    def check(ok,label):report['checks' if ok else 'failures'].append(label)
    def login(page,base,user):
        page.goto(base+'/portal/login/');page.locator('[name=username]').fill(user);page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
        check('/login/' not in page.url,'login '+user)
    def dates():
        start=timezone.localtime()+timedelta(days=10,hours=2)
        return start.strftime('%Y-%m-%dT%H:%M'),(start+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    def first_option(page,name):
        selector=page.locator(f'[name="{name}"]')
        value=selector.locator('option').evaluate_all('(xs)=>xs.find(x=>x.value)?.value')
        selector.select_option(value)
        return value
    def geometry(page,label,expected_rows):
        result=page.locator('main form:has(.ui-form-grid)').first.evaluate('''f=>{
          const fields=[...f.querySelectorAll('.ui-field')].filter(x=>x.checkVisibility());
          const rows=[];for(const x of fields){const y=x.getBoundingClientRect().y;if(!rows.some(v=>Math.abs(y-v)<1))rows.push(y);}
          const last=fields.at(-1)?.querySelector('input:not([type=hidden]):not(.ui-choice-search),select,textarea');
          const names=rows.map(y=>fields.filter(x=>Math.abs(x.getBoundingClientRect().y-y)<1).map(x=>x.querySelector('[name]')?.name));
          const button=f.querySelector('button[type=submit]');return {rows:rows.length,names,gap:last&&button?button.getBoundingClientRect().x-last.getBoundingClientRect().right:null,y:last&&button?Math.abs(button.getBoundingClientRect().y-last.getBoundingClientRect().y):null};
        }''')
        check(result['rows']==expected_rows,label+f' exactly {expected_rows} field rows: '+str(result))
        if label.startswith('event_list'):
            check(result['names']==[['title','event_type','department','attendance_mode'],['start_time','end_time','location','description']],label+' exact field grouping')
        check(result['y'] is not None and result['y']<=1 and 0<=result['gap']<=17,label+' button beside last control')

    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        if not args.evidence_only:
            context=browser.new_context(viewport={'width':1756,'height':1000},service_workers='block',locale='vi-VN',reduced_motion='reduce')
            page=context.new_page();base=f'http://127.0.0.1:{args.port}'
            login(page,base,'demo-hr')
            for theme in ('light','dark'):
                page.evaluate('(t)=>localStorage.setItem("ihrms-theme",t)',theme)
                for route,rows in (('inventory_session_list',1),('room_booking_list',1),('event_list',2)):
                    page.goto(base+reverse('portal:'+route),wait_until='networkidle')
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                    geometry(page,route+'/'+theme,rows)
                    check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),route+' no overflow')
                    page.screenshot(path=str(output/f'{route}-1756-{theme}.png'),full_page=True)
                    for width in (360,390,768,1024):
                        page.set_viewport_size({'width':width,'height':920})
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{route}/{width}/{theme} no overflow')
                    page.set_viewport_size({'width':1756,'height':1000})

            stamp='FORMS-'+uuid.uuid4().hex[:10]
            page.goto(base+reverse('portal:inventory_session_list'),wait_until='networkidle')
            page.locator('[name=session_name]').fill(stamp)
            office=page.locator('[name=office_name]')
            check(bool(office.get_attribute('list')),'office has reusable suggestions')
            office.fill('Synthetic new office '+stamp)
            page.locator('[name=inventory_datetime]').fill(dates()[0])
            page.locator('button[type=submit]:has-text("Tạo đợt")').click();page.wait_for_load_state('networkidle')
            session=InventorySession.objects.filter(session_name=stamp).first()
            check(session is not None and session.office_name=='Synthetic new office '+stamp,'new office text persists without catalogue restriction')
            check(session is not None and reverse('portal:inventory_session_detail',args=[session.pk]) in page.url,'inventory detail target')
            check('Đã tạo đợt kiểm kê' in page.locator('main').inner_text(),'inventory success message')

            page.goto(base+reverse('portal:room_booking_list'),wait_until='networkidle')
            room=first_option(page,'room');start,end=dates()
            page.locator('[name=purpose]').fill(stamp)
            page.locator('[name=start_time]').fill(start);page.locator('[name=end_time]').fill(end)
            page.locator('[name=end_time]').fill(start)
            page.locator('button[type=submit]:has-text("Đặt phòng")').click();page.wait_for_load_state('networkidle')
            check(page.locator('[name=purpose]').input_value()==stamp and page.locator('[name=room]').input_value()==room,'room text and catalogue retained after server error')
            page.locator('[name=end_time]').fill(end)
            page.locator('button[type=submit]:has-text("Đặt phòng")').click();page.wait_for_load_state('networkidle')
            booking=RoomBooking.objects.filter(purpose=stamp,room_id=room).first()
            check(booking is not None and booking.status=='Pending','room booking persisted Pending')
            check(reverse('portal:room_booking_list') in page.url and stamp in page.locator('main').inner_text(),'room target and saved row')

            for mode in ('Online','Offline'):
                page.goto(base+reverse('portal:event_list'),wait_until='networkidle');start,end=dates()
                page.locator('[name=title]').fill(stamp+'-'+mode)
                page.locator('[name=attendance_mode]').select_option(mode)
                page.locator('[name=start_time]').fill(start);page.locator('[name=end_time]').fill(start)
                page.locator('[name=location]').fill('Synthetic event location '+stamp)
                page.locator('[name=description]').fill('Long description retained after server validation')
                page.locator('button[type=submit]:has-text("Tạo sự kiện")').click();page.wait_for_load_state('networkidle')
                check(page.locator('[name=attendance_mode]').input_value()==mode,mode+' retained after invalid time')
                check(page.locator('[name=description]').input_value()=='Long description retained after server validation',mode+' description retained')
                page.locator('[name=end_time]').fill(end)
                page.locator('button[type=submit]:has-text("Tạo sự kiện")').click();page.wait_for_load_state('networkidle')
                check(Event.objects.filter(title=stamp+'-'+mode,attendance_mode=mode).exists(),mode+' event persisted')
                check('Đã tạo sự kiện' in page.locator('main').inner_text(),mode+' success message')
            page.goto(base+reverse('portal:task_create'),wait_until='networkidle')
            search=page.locator('.ui-choice-search').first
            check(search.count()>0,'long native selects have shared search')
            if search.count():
                page.locator('.ui-choice-toggle').first.click()
                native=page.locator('#'+search.get_attribute('aria-controls'));original=native.input_value()
                search.fill('NO_MATCH_SYNTHETIC_SENTINEL')
                check(native.input_value()==original,'search does not change submitted select value')
                check('Không có lựa chọn' in page.locator('.ui-choice-status').first.inner_text(),'no matches feedback')
                search.press('Escape');page.locator('.ui-choice-toggle').first.click();search.press('ArrowDown')
                check(native.evaluate('(x)=>x===document.activeElement'),'search keyboard moves to native selector')
            page.goto(base+reverse('portal:lifecycle_case_create'),wait_until='networkidle')
            page.locator('[name=case_type]').select_option('Onboarding')
            native=page.locator('[name=template_id]');toggle=native.locator('..').locator('.ui-choice-toggle')
            toggle.click();search=page.locator('#template_id-search');search.fill('dao')
            check(native.locator('option').evaluate_all('(xs)=>xs.some(x=>x.value&&!x.hidden&&x.dataset.type==="Onboarding")&&!xs.some(x=>x.value&&!x.hidden&&x.dataset.type!=="Onboarding")'),'accent-insensitive search preserves Onboarding scope')
            search.press('Escape')
            check(native.locator('option').evaluate_all('(xs)=>!xs.some(x=>x.value&&!x.hidden&&x.dataset.type!=="Onboarding")'),'Escape never exposes wrong checklist type')
            page.locator('[name=case_type]').select_option('Offboarding')
            check(native.locator('option').evaluate_all('(xs)=>!xs.some(x=>x.value&&!x.hidden&&x.dataset.type!=="Offboarding")'),'changing checklist type recomposes visibility')
            page.goto(base+reverse('portal:task_create'),wait_until='networkidle')
            page.evaluate('document.documentElement.style.zoom="2"')
            check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'form zoom 200% no overflow')
            context.close()
            # Native controls remain usable without JavaScript.
            nojs=browser.new_context(java_script_enabled=False)
            p=nojs.new_page();login(p,base,'demo-hr');p.goto(base+reverse('portal:event_list'))
            check(p.locator('[name=attendance_mode]').is_visible(),'no-JS native mode select visible')
            nojs.close()

        if not args.flows_only:
            routes=inventory(None)
            captured=set()
            for phase,port in (('before',args.baseline_port),('after',args.port)):
                for account in ('demo-layout-admin','demo-hr','demo-finance'):
                    ctx=browser.new_context(service_workers='block',locale='vi-VN',reduced_motion='reduce')
                    p=ctx.new_page();base=f'http://127.0.0.1:{port}';login(p,base,account)
                    for route in routes:
                        if 'url' not in route:
                            report['failures'].append('Unresolved '+route['name']);continue
                        key=(phase,route['name'])
                        response=p.request.get(base+route['url'],max_redirects=0)
                        report['role_checks'].append({'phase':phase,'account':account,'route':route['name'],'status':response.status})
                        if response.status>=500 or response.status==400:
                            report['failures'].append(f'{phase}/{account}/{route["name"]} unexpected HTTP {response.status}');continue
                        if response.status!=200 or 'text/html' not in response.headers.get('content-type',''):
                            report['excluded'].append({'phase':phase,'account':account,'route':route['name'],'status':response.status});continue
                        if key in captured:continue
                        p.goto(base+route['url'],wait_until='networkidle')
                        if not p.locator('.ui-main').count():report['failures'].append(phase+'/'+route['name']+' HTML page missing shell');continue
                        captured.add(key)
                        name=re.sub('[^a-zA-Z0-9_-]','-',route['name'])
                        for width in (1756,390):
                            p.set_viewport_size({'width':width,'height':1000 if width>600 else 844})
                            for theme in ('light','dark'):
                                p.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                                file=f'{phase}-{name}-{width}-{theme}.png'
                                p.screenshot(path=str(output/file),full_page=True)
                                report['screenshots'].append(file)
                        report['pages'].append({'phase':phase,'route':route['name'],'url':route['url'],'account':account})
                    ctx.close()
            if not args.coverage_report or not args.coverage_report.is_file():
                report['failures'].append('Completed nine-role coverage report required')
            else:
                audit=json.loads(args.coverage_report.read_text(encoding='utf-8'))
                check(validate_coverage(audit,routes),'coverage report is a complete clean after matrix')
                check(not audit.get('errors'),'nine-role audit has no runner errors')
                check(not any('unresolved' in route for route in audit['routes']),'nine-role inventory fully resolved')
                expected={case['route'] for case in audit['cases'] if 'width' in case}
                for phase in ('before','after'):
                    missing=expected-{name for capture_phase,name in captured if capture_phase==phase}
                    check(not missing,phase+' representative HTML coverage complete: missing '+str(sorted(missing)))
            # Every page is included in a paginated module contact sheet.
            groups={}
            for entry in report['pages']:
                if entry['phase']!='after':continue
                route=entry['route'];name=route.split(':')[-1]
                module=('hr' if name.startswith(('hr_','personnel_','profile_','lifecycle')) else
                        'recruitment' if name.startswith('recruitment') else
                        'reports' if name.startswith(('report','dashboard')) else
                        'office' if name.startswith(('room','vehicle','supply','procurement','event','office_','dispatch','holiday')) else
                        'assets' if name.startswith(('asset','inventory','disposal')) else
                        'work' if name.startswith(('activity','task','kpi')) else 'personal-finance')
                groups.setdefault(module,[]).append(route)
            for module,names in groups.items():
                for width in (1756,390):
                    for theme in ('light','dark'):
                        for offset in range(0,len(names),4):
                            sheet=Image.new('RGB',(1400,1760),'#e5e7eb');draw=ImageDraw.Draw(sheet)
                            for row,route in enumerate(names[offset:offset+4]):
                                draw.text((8,row*440+5),route+f' {width}/{theme} BEFORE / AFTER',fill='black')
                                name=re.sub('[^a-zA-Z0-9_-]','-',route)
                                for col,phase in enumerate(('before','after')):
                                    file=output/f'{phase}-{name}-{width}-{theme}.png'
                                    if not file.exists():continue
                                    with Image.open(file) as source:
                                        tile=source.crop((0,0,source.width,min(source.height,1000 if width>600 else 844)));tile.thumbnail((690,410));sheet.paste(tile,(col*700,row*440+25))
                            sheet.save(output/f'contact-{module}-{width}-{theme}-{offset//4+1}.png')
        browser.close()
    (output/('flows-result.json' if args.flows_only else 'result.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']),'failures':report['failures'],'pages':len(report['pages']),'screenshots':len(report['screenshots'])},ensure_ascii=False))
    return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
