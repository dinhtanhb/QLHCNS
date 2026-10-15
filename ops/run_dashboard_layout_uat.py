"""Real Edge layout geometry and navigation on a marked synthetic demo."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--phase', choices=('before','after'), default='after')
    parser.add_argument('--accounts', nargs='+', help='Optional focused rerun; default covers all nine accounts.')
    parser.add_argument('--widths', nargs='+', type=int, help='Optional focused widths; default covers the required matrix.')
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
    output = folder / ('dashboard-group-layout-'+args.phase)
    output.mkdir(exist_ok=True)
    report = {'checks': [], 'errors': [], 'screenshots': [], 'measurements': {}, 'synthetic_only': True}
    base = f'http://127.0.0.1:{args.port}'

    def check(condition, label):
        report['checks'].append(label)
        if not condition: report['errors'].append(label)


    accounts=['employee','manager','hr-officer','hr','director','finance','sys','layout-admin','unlinked']
    if args.phase=='before':accounts=['employee','manager','hr','director']
    if args.accounts:accounts=args.accounts
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True)
            for role in accounts:
                context=browser.new_context(viewport={'width':1440,'height':900},service_workers='block',reduced_motion='reduce')
                page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
                page.goto(base+'/portal/login/');page.locator('[name=username]').fill('demo-'+role);page.locator('[name=password]').fill(password);page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
                widths=(1756,1440,390) if args.phase=='before' else (1756,1440,1280,1024,768,390)
                if args.widths:widths=args.widths
                for width in widths:
                    page.set_viewport_size({'width':width,'height':900})
                    for theme in ('light','dark'):
                        page.evaluate('(t)=>{document.documentElement.dataset.theme=t;localStorage.setItem("ihrms-theme",t)}',theme)
                        response=page.goto(base+'/portal/',wait_until='networkidle');label=f'{role} {width} {theme}'
                        page.evaluate('()=>scrollTo(0,0)')
                        measures=page.locator('.home-dashboard').evaluate(r"""root=>{
                            const rect=x=>{const r=x.getBoundingClientRect();return {y:r.y,h:r.height,w:r.width,bottom:r.bottom}};
                            return {page:rect(root),document_height:document.documentElement.scrollHeight,
                             blocks:Object.fromEntries([...root.children].filter(x=>x.id).map(x=>[x.id,rect(x)])),
                             kpis:[...root.querySelectorAll('.home-main-metric')].map(rect),
                             work:[...root.querySelectorAll('.home-work-card')].map(rect),
                             badges:[...root.querySelectorAll('.ui-badge')].filter(x=>x.checkVisibility()).map(x=>({...rect(x),nowrap:getComputedStyle(x).whiteSpace})),
                             lists:[...root.querySelectorAll('.home-list>li,.home-leave-table tbody>tr')].filter(x=>x.checkVisibility()).map(x=>({...rect(x),decision:x.closest('.home-decisions')!==null}))};
                        }""")
                        report['measurements'][label]=measures
                        if args.phase=='after':
                            check(response.status==200,label+' opens')
                            check(page.evaluate('document.documentElement.dataset.theme')==theme,label+' requested theme retained after navigation')
                            overflow=page.locator('body *').evaluate_all('xs=>xs.filter(x=>x.checkVisibility() && x.getBoundingClientRect().right>innerWidth+1).map(x=>[x.tagName,x.className,x.getBoundingClientRect().right]).slice(0,12)')
                            check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),label+' no page overflow '+str(overflow)+' '+str(page.evaluate('()=>({w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth,offenders:[...document.querySelectorAll("*")].filter(x=>x.scrollWidth>x.clientWidth+2).map(x=>[x.tagName,x.className,x.scrollWidth,x.clientWidth]).slice(0,20)})')))
                            nested=page.locator('.home-dashboard .ui-card *').evaluate_all('xs=>xs.filter(x=>x.checkVisibility() && ["auto","scroll"].includes(getComputedStyle(x).overflowY) && x.scrollHeight>x.clientHeight+1).map(x=>x.className)')
                            check(not nested,label+' no inner vertical scrolling '+str(nested))
                            check(page.locator('.home-dashboard .ui-card').evaluate_all('xs=>xs.every(x=>x.scrollHeight<=x.clientHeight+1)'),label+' cards fit content')
                            groups=page.locator('.home-dashboard > section[id^=group-]').evaluate_all('xs=>xs.map(x=>x.id)')
                            check(groups==[x for x in ['group-projects','group-hr','group-admin','group-recruitment'] if x in groups],label+' business group order')
                            check(not page.locator('.home-dashboard').get_by_text('Thao tác nhanh',exact=True).count(),label+' quick actions removed')
                            check('theo tổng quan cũ' not in page.locator('main').inner_text(),label+' clear labels')
                            if page.locator('#dashboard-my-work').count():
                                check(page.locator('#dashboard-my-work a[href="/portal/leave/create/"]').count()==1,label+' own leave creation')
                                check(page.locator('#dashboard-my-work a[href="/portal/leave/"]').count()==1,label+' own leave list')
                            grids=page.locator('.home-row,.home-my-work-grid').evaluate_all('xs=>xs.map(g=>[...g.children].map(x=>{let r=x.getBoundingClientRect();return {y:r.y,h:r.height,w:r.width}}))')
                            if width>=1024:
                                for rows in grids:
                                    if len(rows)>1:
                                        check(max(x['y'] for x in rows)-min(x['y'] for x in rows)<1.1,label+' row top alignment')
                                        check(max(x['h'] for x in rows)-min(x['h'] for x in rows)<1.1,label+' equal card heights')
                                ratios=page.locator('.home-row:not(.home-row--single),.home-my-work-grid').evaluate_all('xs=>xs.filter(x=>x.children.length===2).map(x=>x.children[0].getBoundingClientRect().width/x.children[1].getBoundingClientRect().width)')
                                check(all(abs(ratio-1.5)<0.01 for ratio in ratios),label+' paired content is 60/40')
                                blanks=page.locator('.home-row .ui-card').evaluate_all('xs=>xs.map(x=>{const last=[...x.children].filter(y=>y.checkVisibility()&&!y.matches(".sr-only,.home-info-body")).at(-1);return last?x.getBoundingClientRect().bottom-last.getBoundingClientRect().bottom-parseFloat(getComputedStyle(x).paddingBottom):0})')
                                check(all(gap<=32 for gap in blanks),label+' paired cards trailing space <=32px '+str(blanks))
                            if width>=1280:
                                if page.locator('#group-recruitment').count():check(page.locator('#group-recruitment').bounding_box()['height']<=96.1,label+' recruitment strip <=96')
                                check(page.locator('.home-page-header').bounding_box()['height']<=56.1,label+' page header <=56')
                                if measures['kpis']:
                                    heights=[x['h'] for x in measures['kpis']]
                                    check(max(heights)<=104.1 and max(heights)-min(heights)<=1,label+' KPI <=104 and equal')
                                if measures['work']:check(max(x['h'] for x in measures['work'])<=72.1,label+' own work <=72')
                                check(all(x['h']<=28.1 and x['nowrap']=='nowrap' for x in measures['badges']),label+' badge <=28 and nowrap')
                                check(all(x['h']<=(36.1 if x['decision'] else 40.1) for x in measures['lists']),label+' compact list heights')
                            if width==1440:
                                for key in ('dashboard-status','dashboard-my-work','group-projects'):
                                    if key in measures['blocks']:check(measures['blocks'][key]['bottom']<=900,label+' first fold '+key)
                                if 'group-hr' in measures['blocks']:check(measures['blocks']['group-hr']['y']<900,label+' first fold HR')
                                if role=='hr':
                                    check(measures['document_height']<=1260,label+' HR document <=1260')
                                    if 'group-hr' in measures['blocks']:check(measures['blocks']['group-hr']['h']<=520,label+' HR section <=520')
                                if role=='director':check(measures['document_height']<=990,label+' Director document <=990')
                                if role=='employee':check(measures['document_height']<=900,label+' Employee document <=900')
                            if width==1440 and page.locator('#dashboard-my-work').count():
                                bottom=page.locator('#dashboard-my-work').bounding_box()['y']+page.locator('#dashboard-my-work').bounding_box()['height']
                                check(bottom<=900,label+' first fold includes my work')
                                if groups:check(page.locator('#'+groups[0]+' > header').bounding_box()['y']<900,label+' first group title in first fold')
                            check(page.locator('main summary').evaluate_all('xs=>xs.filter(x=>x.checkVisibility()).every(x=>x.getBoundingClientRect().height>=43.5)'),label+' calculation touch targets')
                            small=page.locator('main :is(p,span,strong,a,summary,th,td)').evaluate_all('xs=>xs.filter(x=>x.checkVisibility() && x.textContent.trim() && parseFloat(getComputedStyle(x).fontSize)<14).map(x=>[x.className,getComputedStyle(x).fontSize,x.textContent.slice(0,40)])');check(not small,label+' text >=14px '+str(small))
                            values=page.locator('.home-main-kpis .ui-kpi-value').evaluate_all('xs=>xs.map(x=>x.getBoundingClientRect().y)')
                            if width>=1280 and len(values)>1:check(max(values)-min(values)<=1,label+' main value baseline')
                            for summary in page.locator('main details.home-info > summary').all():
                                owner=summary.evaluate('x=>x.closest("section")?.id');summary.focus();bounds=page.locator('.home-dashboard').bounding_box();page.keyboard.press('Enter');check(summary.evaluate('x=>x.parentElement.open'),label+' '+str(owner)+' calculation keyboard opens');check(page.locator('.home-dashboard').bounding_box()==bounds,label+' info does not move content');page.keyboard.press('Escape');check(not summary.evaluate('x=>x.parentElement.open'),label+' '+str(owner)+' calculation Escape closes');page.keyboard.press('Enter');page.locator('h1').evaluate('x=>{x.tabIndex=-1;x.focus()}');check(not summary.evaluate('x=>x.parentElement.open'),label+' info blur closes')
                        if width in (1756,1440,390) and role in ('employee','manager','hr','director'):
                            page.evaluate('()=>{document.activeElement.blur();scrollTo(0,0)}')
                            for full,suffix in ((False,'first'),(True,'full')):
                                path=output/f'{args.phase}-{role}-{width}-{theme}-{suffix}.png';page.screenshot(path=str(path),full_page=full);report['screenshots'].append(str(path))
                context.close()
            browser.close()
    except Exception as error:
        report['errors'].append(str(error))
    report['passed']=not report['errors'];(output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'checks':len(report['checks']),'screenshots':len(report['screenshots']),'errors':report['errors']}));return not report['passed']


if __name__=='__main__':raise SystemExit(main())
