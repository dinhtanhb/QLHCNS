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
                            // Phương án B: nội dung nằm trong .home-dashboard-stream (8/4), nên
                            // khối và nhóm được chọn theo section[id] thay vì con trực tiếp.
                            const stream=root.querySelector('.home-dashboard-stream')||root;
                            return {page:rect(root),document_height:document.documentElement.scrollHeight,
                             blocks:Object.fromEntries([...root.querySelectorAll('section[id]')].map(x=>[x.id,rect(x)])),
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
                            groups=page.locator('.home-dashboard section[id^=group-]').evaluate_all('xs=>xs.map(x=>x.id)')
                            check(groups==[x for x in ['group-projects','group-hr','group-admin','group-recruitment'] if x in groups],label+' business group order')
                            check(not page.locator('.home-dashboard').get_by_text('Thao tác nhanh',exact=True).count(),label+' quick actions removed')
                            check('theo tổng quan cũ' not in page.locator('main').inner_text(),label+' clear labels')
                            if page.locator('#dashboard-my-work').count():
                                check(page.locator('#dashboard-my-work a[href="/portal/leave/create/"]').count()==1,label+' own leave creation')
                                check(page.locator('#dashboard-my-work a[href="/portal/leave/"]').count()==1,label+' own leave list')
                            grids=page.locator('.home-row,.home-my-work-grid').evaluate_all('xs=>xs.map(g=>({cards:[...g.children].map(x=>{let r=x.getBoundingClientRect();let header=x.querySelector(":scope > .ui-card-header"), h=header?.getBoundingClientRect();return {y:r.y,h:r.height,w:r.width,headerBottom:h?.bottom,titleY:header?.querySelector("h3")?.getBoundingClientRect().y}})}))')
                            if page.locator('#dashboard-my-work').count():
                                check(page.locator('.home-my-work-grid > .home-work-card').count()==2,label+' two work cards remain in their shared grid')
                            if width>=1024:
                                for grid in grids:
                                    rows=grid['cards']
                                    if len(rows)>1:
                                        check(max(x['y'] for x in rows)-min(x['y'] for x in rows)<1.1,label+' row top alignment')
                                        check(max(x['h'] for x in rows)-min(x['h'] for x in rows)<1.1,label+' equal card heights including HR and leave')
                                        if all(x.get('headerBottom') is not None for x in rows):
                                            check(max(x['headerBottom'] for x in rows)-min(x['headerBottom'] for x in rows)<1.1,label+' shared card header boundary')
                                            check(max(x['titleY'] for x in rows)-min(x['titleY'] for x in rows)<1.1,label+' paired title top alignment')
                                ratios=page.locator('.home-row:not(.home-row--single),.home-my-work-grid').evaluate_all('xs=>xs.filter(x=>x.children.length===2).map(x=>x.children[0].getBoundingClientRect().width/x.children[1].getBoundingClientRect().width)')
                                check(all(abs(ratio-1.5)<0.01 for ratio in ratios),label+' paired content is 60/40')
                            quality=page.locator('.home-dashboard').evaluate(r"""root=>{
 const rect=x=>x.getBoundingClientRect(), near=(a,b)=>Math.abs(a-b)<=2;
 const visible=x=>x.checkVisibility()&&!x.closest('.sr-only,.home-info-body');
 const cards=[...root.querySelectorAll('.ui-card')].filter(visible);
 const body=[...root.querySelectorAll('p,span,a,th,td,dt,dd')].filter(visible);
 const stream=root.querySelector('.home-dashboard-stream')||root;
 const spacing=[...stream.children].filter(x=>visible(x)&&x.matches('section'));
 // Thang chữ lấy thẳng từ token thay vì số cứng: cổng kiểm "mọi cỡ chữ trên
 // bảng điều khiển đến từ token", nên đổi token không làm cổng sai lệch.
 const rem=parseFloat(getComputedStyle(document.documentElement).fontSize)||16;
 const token=name=>{const raw=getComputedStyle(root).getPropertyValue(name).trim();
   return raw.endsWith('rem')?parseFloat(raw)*rem:parseFloat(raw)};
 const scales=[['h1',token('--ui-text-h1'),token('--ui-leading-h1')],
   ['h2',20,28], ['h3',16,24],
   ['.ui-kpi-value',token('--ui-text-kpi'),token('--ui-leading-kpi')],
   ['.home-work-card .home-work-value',token('--ui-text-work'),token('--ui-leading-stat')],
   ['.home-project-metrics dd,.home-recruitment-metrics .home-work-value',token('--ui-text-stat'),token('--ui-leading-stat')]];
 const targetFloor=matchMedia('(min-width:770px) and (pointer:fine)').matches?36:44;
 const rows=[...root.querySelectorAll('.home-list>li,.home-capacity>li,.home-type-list>li')].filter(visible);
 const targets=[...root.querySelectorAll('a,summary')].filter(visible);
 const overlaps=targets.some((x,i)=>targets.slice(i+1).some(y=>{if(x.contains(y)||y.contains(x))return false;const a=rect(x),b=rect(y);return Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1}));
 const capacity=[...root.querySelectorAll('.home-capacity>li')];
 const align=selector=>{const xs=capacity.map(x=>x.querySelector(selector)).filter(Boolean).map(x=>rect(x).x);return !xs.length||Math.max(...xs)-Math.min(...xs)<=1};
 const metrics=[...root.querySelectorAll('.home-project-metrics,.home-recruitment-metrics')];
 return {
  // Sectioned cards put the readable inset on the body, with the same header
  // inset. Check those actual surfaces instead of requiring double padding.
  padding:cards.every(x=>{const header=x.querySelector(':scope > .ui-card-header'),body=x.querySelector(':scope > .ui-card-body');
    if(header&&body){const h=getComputedStyle(header),b=getComputedStyle(body);return ['paddingTop','paddingBottom','paddingLeft','paddingRight'].every(k=>parseFloat(b[k])>=16)&&near(parseFloat(h.paddingLeft),parseFloat(b.paddingLeft))&&near(parseFloat(h.paddingRight),parseFloat(b.paddingRight));}
    return ['paddingTop','paddingBottom','paddingLeft','paddingRight'].every(k=>parseFloat(getComputedStyle(x)[k])>=16)}),
 // Phương án B: KPI gộp một dải nên gap = 0 và ngăn bằng đường kẻ dọc; các lưới
 // còn lại vẫn giữ nhịp 16px. Đổi ở đây là đổi hợp đồng, không phải nới cổng.
 // Shared header/body tracks have zero row gap inside each pair; stacked
 // cards keep the existing 16px separation below the two-column breakpoint.
 cardGap:[...root.querySelectorAll('.home-row,.home-my-work-grid')].every(x=>{const s=getComputedStyle(x);return near(parseFloat(s.columnGap),16)&&near(parseFloat(s.rowGap),innerWidth>=1024?0:16)})&&[...root.querySelectorAll('.home-main-kpis')].every(x=>parseFloat(getComputedStyle(x).gap)===0),
  groupGap:near(parseFloat(getComputedStyle(root).rowGap),32),
  sectionGap:spacing.filter(x=>x.children.length>1).every(x=>near(parseFloat(getComputedStyle(x).rowGap),12)),
  type:scales.every(([selector,size,line])=>[...root.querySelectorAll(selector)].filter(visible).every(x=>near(parseFloat(getComputedStyle(x).fontSize),size)&&near(parseFloat(getComputedStyle(x).lineHeight),line))),
  // Static HR reading rows use 32px; interactive targets remain 44px below.
  rows:rows.every(x=>rect(x).height>=(x.querySelector('a')?targetFloor-.5:x.matches('.home-capacity>li,.home-type-list>li')?31.5:39.5)),
  targets:targets.every(x=>rect(x).height>=targetFloor-.5&&rect(x).width>=targetFloor-.5),
  overlaps,
  capacityAligned:innerWidth<1280||['.home-department-name','.home-capacity-track','.home-capacity-value','.home-capacity-alert'].every(align),
  metricsAligned:innerWidth<768||metrics.every(x=>{const ys=[...x.querySelectorAll('.home-work-value,dd')].filter(y=>y.parentElement.parentElement===x).map(y=>rect(y).y);return !ys.length||Math.max(...ys)-Math.min(...ys)<=1}),
  noShadow:cards.every(x=>getComputedStyle(x).boxShadow==='none'),
  kpiHeights:[...root.querySelectorAll('.home-main-metric')].map(x=>rect(x).height),
  focusTokens:getComputedStyle(root).getPropertyValue('--ui-focus-width').trim()==='3px'
 };
}""")
                            for criterion in ('padding','cardGap','groupGap','sectionGap','type','rows','targets','capacityAligned','metricsAligned','noShadow','focusTokens'):
                                check(quality[criterion],label+' visual system '+criterion)
                            check(not quality['overlaps'],label+' hit targets do not overlap')
                            if width>=1280 and quality['kpiHeights']:check(max(quality['kpiHeights'])-min(quality['kpiHeights'])<=1,label+' equal KPI heights')
                            if width==1440:
                                for key in ('dashboard-status','dashboard-my-work'):
                                    if key in measures['blocks']:check(measures['blocks'][key]['bottom']<=900,label+' first fold '+key)
                                # Đợt 4: thẻ KPI có thêm hàng 2 (5 chỉ số tổng hợp), nên một nhóm
                                # nghiệp vụ không còn vừa trọn màn hình đầu. Hợp đồng đổi thành
                                # "tiêu đề nhóm đầu tiên phải nằm trong màn hình đầu", không đòi
                                # cả nhóm; đây là đổi hợp đồng theo yêu cầu chủ dự án, không nới cổng.
                                if groups:check(page.locator('#'+groups[0]+' > header').bounding_box()['y']<900,label+' first group title in first fold')
                            if width==1440 and page.locator('#dashboard-my-work').count():
                                bottom=page.locator('#dashboard-my-work').bounding_box()['y']+page.locator('#dashboard-my-work').bounding_box()['height']
                                check(bottom<=900,label+' first fold includes my work')
                            check(page.locator('main summary').evaluate_all('xs=>xs.filter(x=>x.checkVisibility()).every(x=>x.getBoundingClientRect().height>=(matchMedia("(min-width:770px) and (pointer:fine)").matches?35.5:43.5))'),label+' calculation touch targets')
                            small=page.locator('main :is(p,span,strong,a,summary,th,td)').evaluate_all('xs=>xs.filter(x=>x.checkVisibility() && x.textContent.trim() && parseFloat(getComputedStyle(x).fontSize)<14).map(x=>[x.className,getComputedStyle(x).fontSize,x.textContent.slice(0,40)])');check(not small,label+' text >=14px '+str(small))
                            values=page.locator('.home-main-kpis .ui-kpi-value').evaluate_all('xs=>xs.map(x=>x.getBoundingClientRect().y)')
                            if width>=1280 and len(values)>1:check(max(values)-min(values)<=1,label+' main value baseline')
                            # Spec 17 puts an admitted personal block inside native details.
                            # Open its parent before exercising every nested calculation popover.
                            own_summaries=page.locator('.dashboard-own-leave > summary').all()
                            for summary in own_summaries:
                                summary.focus();page.keyboard.press('Enter')
                                check(summary.evaluate('x=>x.parentElement.open'),label+' personal leave keyboard opens')
                            for summary in page.locator('main details.home-info > summary').all():
                                owner=summary.evaluate('x=>x.closest("section")?.id');summary.focus();bounds=page.locator('.home-dashboard').bounding_box();page.keyboard.press('Enter');check(summary.evaluate('x=>x.parentElement.open'),label+' '+str(owner)+' calculation keyboard opens');check(page.locator('.home-dashboard').bounding_box()==bounds,label+' info does not move content');page.keyboard.press('Escape');check(not summary.evaluate('x=>x.parentElement.open'),label+' '+str(owner)+' calculation Escape closes');page.keyboard.press('Enter');page.locator('h1').evaluate('x=>{x.tabIndex=-1;x.focus()}');check(not summary.evaluate('x=>x.parentElement.open'),label+' info blur closes')
                            for summary in own_summaries:
                                summary.focus();page.keyboard.press('Enter')
                                check(not summary.evaluate('x=>x.parentElement.open'),label+' personal leave keyboard closes')
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
