"""Edge regression checks for persistent shell, section bars and report KPIs."""
import argparse
import json
from pathlib import Path
import sys


MEASURE = r"""() => {
 const violations=[], measurements={};
 const rect=x=>x.getBoundingClientRect(),visible=x=>x.checkVisibility();
 const fail=(code,x,detail)=>violations.push({code,selector:x.id||x.className,detail});
 const header=document.querySelector('#ui-topbar'),main=document.querySelector('.ui-main');
 if(!header||!main)return {violations,measurements};
 if(getComputedStyle(header).position!=='fixed')fail('SHELL_HEADER_POSITION',header,getComputedStyle(header).position);
 const h=rect(header);measurements.topbar={top:h.top,bottom:h.bottom,height:h.height,position:getComputedStyle(header).position,scrollY};
 if(h.top<-.5||h.bottom>innerHeight+.5)fail('SHELL_HEADER_VIEWPORT',header,measurements.topbar);
 const control=header.querySelector('.ui-brand');if(control){const r=rect(control),x=Math.max(0,Math.min(innerWidth-1,r.x+r.width/2)),y=r.y+r.height/2;
  if(y>=0&&y<innerHeight&&!header.contains(document.elementFromPoint(x,y)))fail('SHELL_HEADER_OCCLUDED',header,{x,y});}
 if(scrollY<1&&rect(main).top<h.bottom-.5)fail('SHELL_CONTENT_OFFSET',main,{mainTop:rect(main).top,headerBottom:h.bottom});
 const sidebar=document.querySelector('#portalSidebar');
 if(innerWidth>=1024&&sidebar&&visible(sidebar)&&rect(sidebar).top<h.bottom-.5)fail('SHELL_SIDEBAR_OFFSET',sidebar,{sidebarTop:rect(sidebar).top,headerBottom:h.bottom});
 for(const x of main.querySelectorAll('.home-dashboard .ui-section-header')){
  const s=getComputedStyle(x);if(['transparent','rgba(0, 0, 0, 0)'].includes(s.backgroundColor)||parseFloat(s.borderTopWidth)<1)fail('SECTION_HEADER_BAR',x,{background:s.backgroundColor,border:s.borderTopWidth});
 }
 const report=main.querySelector('.report-shell');
 if(report){
  const toolbar=report.querySelector('.report-toolbar');if(toolbar){
   const form=toolbar.querySelector('form'),exports=toolbar.querySelector('.report-export-actions'),submit=form?.querySelector('button[type=submit]');
   for(const echo of toolbar.querySelectorAll('.ui-date-echo')){if(!visible(echo)||!echo.textContent)continue;const a=rect(echo);
    for(const control of toolbar.querySelectorAll('label,input,button,a')){if(!visible(control))continue;const b=rect(control);
     if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)fail('REPORT_DATE_ECHO_OVERLAP',echo,{echo:echo.textContent,control:control.id||control.textContent.trim()});}
   }
   if(form&&exports&&submit&&rect(exports).left>=rect(form).right-1){const ys=[...exports.querySelectorAll('a')].map(x=>rect(x).bottom);if(ys.some(y=>Math.abs(y-rect(submit).bottom)>1))fail('REPORT_TOOLBAR_ALIGNMENT',toolbar,{submit:rect(submit).bottom,exports:ys});}
  }
  const cards=[...report.querySelectorAll('.ui-kpi-grid > .ui-kpi')],rows=[];
  measurements.kpis=cards.map(card=>{const label=card.querySelector('.ui-kpi-label'),icon=card.querySelector('.ui-kpi-symbol'),value=card.querySelector('.ui-kpi-value'),r=rect(card),v=rect(value);
   if(label&&icon){const a=rect(label),b=rect(icon);if(Math.abs(a.top-b.top)>1||a.right>b.left+1)fail('KPI_LABEL_ICON',card,{labelY:a.top,iconY:b.top,labelRight:a.right,iconLeft:b.left});}
   if(card.scrollWidth>card.clientWidth+1)fail('KPI_OVERFLOW',card,{scroll:card.scrollWidth,width:card.clientWidth});
   let row=rows.find(row=>Math.abs(row.y-r.y)<1);if(!row){row={y:r.y,values:[],heights:[]};rows.push(row);}row.values.push(v.y);row.heights.push(r.height);
   return {top:r.y,height:r.height,valueTop:v.y,label:label?.textContent.trim()};});
  for(const row of rows){if(Math.max(...row.values)-Math.min(...row.values)>1)fail('KPI_VALUE_ALIGNMENT',report,row);if(Math.max(...row.heights)-Math.min(...row.heights)>1)fail('KPI_CARD_ALIGNMENT',report,row);}
  const area=report.querySelector('.report-kpis');
  if(area){const w=area.clientWidth,rem=parseFloat(getComputedStyle(document.documentElement).fontSize),expected=w>=71*rem?6:w>=35*rem?3:w>=23*rem?2:1,grid=area.querySelector('.ui-kpi-grid'),columns=getComputedStyle(grid).gridTemplateColumns.split(' ').length;
   measurements.kpiColumns={width:w,expected,actual:columns};if(columns!==expected)fail('REPORT_KPI_COLUMNS',grid,measurements.kpiColumns);}
 }
 if(document.documentElement.scrollWidth>innerWidth+1)fail('SHELL_OVERFLOW',main,{width:innerWidth,scrollWidth:document.documentElement.scrollWidth});
 return {violations,measurements};
}"""


def interactions(page, base, output, report, negative_controls=False):
    checks = report.setdefault('interaction_checks', [])

    def check(ok, label):
        checks.append({'label': label, 'passed': bool(ok)})
        if not ok:
            report['errors'].append({'code':'INTERACTION','detail':label})

    for width in (1756,390):
        page.set_viewport_size({'width':width,'height':1000})
        page.goto(base+'/portal/reports/',wait_until='networkidle')
        for details in page.locator('.ui-action-overflow:visible').all():
            summary = details.locator('summary')
            summary.focus()
            page.keyboard.press('Enter')
            check(details.evaluate('x=>x.open'), 'overflow Enter opens')
            for link in details.locator('.ui-action-menu a').all():
                link.scroll_into_view_if_needed()
                check(link.evaluate('x=>{const r=x.getBoundingClientRect(),top=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return top===x||x.contains(top)}'), 'menu link receives pointer')
            page.keyboard.press('Tab')
            check(details.evaluate('x=>x.contains(document.activeElement)'), 'Tab enters action menu')
            page.keyboard.press('Escape')
            check(not details.evaluate('x=>x.open'), 'Escape closes action menu')
        for zoom in (1,2):
            page.evaluate('(zoom)=>document.documentElement.style.zoom=zoom',str(zoom))
            page.wait_for_timeout(200)
            page.locator('#userMenuButton').focus()
            page.keyboard.press('Enter')
            bounds=page.locator('#userDropdown').bounding_box()
            check(bounds and bounds['x']>=-1 and bounds['x']+bounds['width']<=width+1 and bounds['y']+bounds['height']<=1001, 'account menu stays in viewport at zoom '+str(zoom))
            page.keyboard.press('Escape')
            page.evaluate('document.documentElement.style.zoom=""')
        page.locator('#userMenuButton').focus()
        page.keyboard.press('Enter')
        check(page.locator('#userDropdown').is_visible(), 'account menu opens')
        page.keyboard.press('Escape')
        check(not page.locator('#userDropdown').is_visible(), 'account Escape closes')
        if width==390:
            page.locator('#mobileNavToggle').focus()
            page.keyboard.press('Enter')
            check(page.locator('#portalSidebar').get_attribute('aria-modal')=='true', 'mobile navigation is modal')
            page.keyboard.press('Escape')
            check(not page.locator('#portalSidebar').is_visible(), 'mobile navigation Escape closes')
        page.evaluate('''() => {document.querySelector('.report-kpis .ui-kpi-label').textContent='Nhãn kiểm thử rất dài để xác minh xuống dòng';document.querySelector('.report-kpis .ui-kpi-value').textContent='1.234.567';}''')
        page.wait_for_timeout(150)
        result = page.evaluate(MEASURE)
        check(not result['violations'], 'long label/large value '+str(width))
        path = output/f'long-kpis-{width}.png'
        page.locator('.report-kpis').screenshot(path=str(path))
        report['screenshots'].append(str(path))
    if not negative_controls:
        return
    page.set_viewport_size({'width':1756,'height':1000})
    report['negative_controls'] = []
    for code,route,selector,property_name,value,scroll in (
        ('SHELL_HEADER_POSITION','/portal/','#ui-topbar','position','absolute',800),
        ('SHELL_CONTENT_OFFSET','/portal/','body','padding-top','0px',0),
        ('SHELL_SIDEBAR_OFFSET','/portal/','#portalSidebar','top','0px',0),
        ('SECTION_HEADER_BAR','/portal/','.ui-section-header','border-top-width','0px',0),
        ('KPI_LABEL_ICON','/portal/reports/','.ui-kpi-heading','display','block',0),
        ('KPI_VALUE_ALIGNMENT','/portal/reports/','.ui-kpi-value','transform','translateY(5px)',0),
        ('REPORT_KPI_COLUMNS','/portal/reports/','.report-kpis>.ui-kpi-grid','grid-template-columns','repeat(2,minmax(0,1fr))',0),
        ('REPORT_TOOLBAR_ALIGNMENT','/portal/reports/','.report-export-actions','margin-top','8px',0),
        ('REPORT_DATE_ECHO_OVERLAP','/portal/reports/','.ui-date-echo','transform','translateY(-30px)',0),
    ):
        page.goto(base+route,wait_until='networkidle')
        page.evaluate('([selector,key,value,y])=>{document.querySelector(selector).style.setProperty(key,value);scrollTo(0,y)}',[selector,property_name,value,scroll])
        page.wait_for_timeout(100)
        found={v['code'] for v in page.evaluate(MEASURE)['violations']}
        check(code in found, 'negative control '+code)
        report['negative_controls'].append({'code':code,'detected':code in found})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--palette', default='viethealth')
    parser.add_argument('--phase', choices=('before', 'after'), required=True)
    parser.add_argument('--negative-controls', action='store_true')
    parser.add_argument('--widths', type=int, nargs='+', default=[1920,1756,1440,1280,1024,768,390,360])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('QA runtime must be outside the repository.')
    if json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    password = next(line.split(': ',1)[1] for line in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    output = folder/f'header-report-{args.phase}-{args.palette}'
    output.mkdir(exist_ok=True)
    report = {'synthetic_only':True,'cases':[],'errors':[],'screenshots':[]}
    base = f'http://127.0.0.1:{args.port}'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge',headless=True)
        context = browser.new_context(viewport={'width':1756,'height':1000},locale='vi-VN',service_workers='block',reduced_motion='reduce')
        page = context.new_page()
        page.goto(base+'/portal/login/')
        page.locator('[name=username]').fill('demo-layout-admin')
        page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click()
        page.wait_for_load_state('networkidle')
        for width in args.widths:
            page.set_viewport_size({'width':width,'height':1000})
            for theme in ('light','dark'):
                for route,name in (('/portal/','dashboard'),('/portal/reports/','reports')):
                    page.evaluate('(theme)=>localStorage.setItem("ihrms-theme",theme)',theme)
                    page.goto(base+route,wait_until='networkidle')
                    for state in ('expanded','collapsed') if width>=1024 else ('mobile',):
                        if width>=1024:
                            wanted=state=='collapsed'
                            if page.evaluate('document.body.dataset.sidebarCollapsed==="true"')!=wanted:
                                page.locator('#mobileNavToggle').click()
                        for zoom in (1,2):
                            page.evaluate('(zoom)=>document.documentElement.style.zoom=zoom',str(zoom))
                            for position in ('top','middle','bottom'):
                                page.evaluate('(position)=>{const y=document.documentElement.scrollHeight-innerHeight;scrollTo(0,position==="top"?0:position==="middle"?y/2:y)}',position)
                                # ResizeObserver -> action layout -> shell height
                                # can span several frames after CSS zoom/reflow.
                                page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                                page.evaluate('''() => new Promise(resolve=>{
                                  let previous='',stable=0,count=0;
                                  const tick=()=>{const signature=JSON.stringify([document.documentElement.scrollWidth,...[...document.querySelectorAll('#ui-topbar,.ui-section-header,.ui-card-header')].map(x=>{const r=x.getBoundingClientRect();return [r.x,r.y,r.width,r.height,x.scrollWidth]})]);
                                    stable=signature===previous?stable+1:0;previous=signature;
                                    if(stable>=3||++count>=40)resolve();else setTimeout(tick,50);};tick();
                                })''')
                                result=page.evaluate(MEASURE)
                                case={'route':route,'width':width,'theme':theme,'sidebar':state,'zoom':zoom,'scroll':position,**result}
                                report['cases'].append(case)
                                report['errors'].extend({'case':{k:case[k] for k in ('route','width','theme','sidebar','zoom','scroll')},**v} for v in result['violations'])
                                if width in (1756,390) and zoom==1 and state in ('expanded','mobile'):
                                    path=output/f'{name}-{width}-{theme}-{position}.png'
                                    page.screenshot(path=str(path),full_page=False)
                                    report['screenshots'].append(str(path))
                            page.evaluate('document.documentElement.style.zoom=""')
                    page.evaluate('scrollTo(0,0)')
        if args.phase=='after':
            interactions(page,base,output,report,args.negative_controls)
        context.close()
        browser.close()
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'cases':len(report['cases']),'violations':len(report['errors']),'by_code':{code:sum(e['code']==code for e in report['errors']) for code in sorted({e['code'] for e in report['errors']})},'output':str(output)}))
    return bool(report['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
