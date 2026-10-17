"""Audit configured action kinds in source templates and real browser HTML.

No writes to application data. Runtime requires the marked external fixture DB.
Unclassified labels are reported separately; wrong kinds or geometry fail.
"""
import argparse
import asyncio
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

from run_layout_alignment_audit import configure, inventory


def normalize(label):
    return ' '.join(unescape(label).strip().lstrip('+←→− ').split()).rstrip(' →').strip()


def classify(label, config):
    raw=' '.join(unescape(label).split())
    label=normalize(raw)
    if label.isdigit():return ['secondary'],'current pagination indicator'
    for row in config['exceptions']:
        if row['label']==label:return row['allowed'],row['reason']
    for row in config['dynamic_templates']:
        if row['expression']==raw:return ([row['kind']] if row['kind'] else []),row['reason']
    if raw in config['exact']:return [config['exact'][raw]],'exact'
    if label in config['exact']:return [config['exact'][label]],'exact'
    # Longest prefix wins: Xóa lọc is navigation, while Xóa is destructive.
    matches=[(len(prefix),kind) for kind,prefixes in config['prefixes'].items() for prefix in prefixes if label==prefix or label.startswith(prefix+' ') or label.startswith(prefix+'/')]
    return ([max(matches)[1]],'prefix') if matches else ([],None)


class Buttons(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.stack=[]
        self.feed(source)

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('a','button','summary','input','span') and 'ui-button' in attrs.get('class','').split():
            row={'line':self.getpos()[0],'tag':tag,'classes':attrs['class'],'label':attrs.get('value','') if tag=='input' else ''}
            self.rows.append(row)
            if tag!='input':self.stack.append((tag,row))

    def handle_data(self,data):
        if self.stack:self.stack[-1][1]['label']+=data

    def handle_endtag(self,tag):
        if self.stack and tag==self.stack[-1][0]:self.stack.pop()


def variants(classes):
    return set(re.findall(r'\bui-button--(primary|secondary|tertiary|danger-primary|danger-solid|danger)\b',classes))


def assess(row,config,static=False):
    row['label']=' '.join(re.sub(r'{%.*?%}',' ',row['label'],flags=re.S).split())
    allowed,reason=classify(row['label'],config)
    row['expected']=allowed;row['classification_reason']=reason
    issues=[]
    actual=variants(row['classes'])
    if allowed and (not actual or not actual.issubset(set(allowed))):issues.append('BUTTON_KIND')
    if not static:
        expected=config['geometry'];style=row['style']
        for key in ('height','fontSize','paddingTop','paddingRight','paddingBottom','paddingLeft','borderRadius','columnGap'):
            if abs(float(style[key])-expected[key])>1:issues.append('BUTTON_SIZE:'+key)
        if style['fontWeight']!=expected['fontWeight']:issues.append('BUTTON_SIZE:fontWeight')
        if any(abs(size-expected['iconSize'])>1 for size in row['icons']):issues.append('BUTTON_SIZE:icon')
    row['issues']=issues
    row['unclassified']=not allowed and reason is None
    return row


def template_audit(root,config):
    rows=[]
    for path in sorted((root/'src').rglob('*.html')):
        for row in Buttons(path.read_text(encoding='utf-8')).rows:
            row['template']=str(path.relative_to(root)).replace('\\','/')
            rows.append(assess(row,config,static=True))
    return rows


MEASURE="""()=>[...document.querySelectorAll('.ui-button')].filter(x=>x.checkVisibility()&&!x.closest('.hcns-paper')).map(x=>{
 const s=getComputedStyle(x),r=x.getBoundingClientRect();
 return {label:x.innerText||x.value||x.getAttribute('aria-label')||'',classes:x.className,tag:x.tagName.toLowerCase(),href:x.getAttribute('href'),
 style:{height:r.height,fontSize:parseFloat(s.fontSize),fontWeight:s.fontWeight,paddingTop:parseFloat(s.paddingTop),paddingRight:parseFloat(s.paddingRight),paddingBottom:parseFloat(s.paddingBottom),paddingLeft:parseFloat(s.paddingLeft),borderRadius:parseFloat(s.borderRadius),columnGap:parseFloat(s.columnGap)},
 icons:[...x.querySelectorAll('svg')].flatMap(i=>[i.getBoundingClientRect().width,i.getBoundingClientRect().height])};})"""


async def browser_audit(args,routes,config):
    from playwright.async_api import async_playwright
    password=next(line.split(': ',1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    accounts=args.accounts or ['demo-layout-admin','demo-hr','demo-director','demo-manager','demo-employee','demo-finance','demo-hr-officer','demo-sys','demo-unlinked']
    rows=[];cases=[];errors=[];lock=asyncio.Lock();limit=asyncio.Semaphore(args.workers)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(channel='msedge',headless=True)
        async def run(account):
            async with limit:
                context=await browser.new_context(viewport={'width':1756,'height':1000},locale='vi-VN',service_workers='block',reduced_motion='reduce')
                page=await context.new_page();base=f'http://127.0.0.1:{args.port}'
                async with lock:
                    await page.goto(base+'/portal/login/');await page.locator('[name=username]').fill(account);await page.locator('[name=password]').fill(password);await page.locator('main button[type=submit]').click();await page.wait_for_load_state('networkidle')
                if '/login/' in page.url:raise RuntimeError('Login failed '+account)
                for route in routes:
                    case={'account':account,'route':route['name']}
                    if 'url' not in route:errors.append(dict(case,error='Unresolved route'));continue
                    try:
                        response=await page.request.get(base+route['url'],max_redirects=0);case['status']=response.status
                        if response.status>=500 or response.status==400:errors.append(dict(case,error='Unexpected HTTP'));continue
                        if response.status!=200 or 'text/html' not in response.headers.get('content-type',''):
                            cases.append(dict(case,skip='HTTP/non-HTML'));continue
                        await page.goto(base+route['url'],wait_until='networkidle')
                        if not await page.locator('.ui-main').count():errors.append(dict(case,error='Missing portal shell'));continue
                        for theme in ('light','dark'):
                            await page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                            measured=await page.evaluate(MEASURE)
                            for row in measured:rows.append(assess(dict(case,theme=theme,**row),config))
                        cases.append(case)
                    except Exception as exc:errors.append(dict(case,error=str(exc)))
                await context.close()
                print('Finished '+account,flush=True)
        await asyncio.gather(*(run(account) for account in accounts))
        await browser.close()
    return rows,cases,errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config',type=Path,default=Path(__file__).resolve().parents[1]/'docs/UI_BUTTON_KINDS.json')
    parser.add_argument('--directory',type=Path)
    parser.add_argument('--packages-dir',type=Path)
    parser.add_argument('--port',type=int,default=8812)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--accounts',nargs='+');parser.add_argument('--only',nargs='+');parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args();root=args.source_root.resolve();config=json.loads(args.config.read_text(encoding='utf-8'))
    if args.output.resolve()==root or root in args.output.resolve().parents:parser.error('Evidence must be outside repository')
    static=template_audit(root,config);rows=[];cases=[];errors=[]
    if args.directory:
        if not args.packages_dir:parser.error('--packages-dir required for real browser geometry')
        configure(root,args.directory.resolve());sys.path.insert(0,str(args.packages_dir.resolve()))
        rows,cases,errors=asyncio.run(browser_audit(args,inventory(args.only),config))
    report={'source_root':str(root),'templates':static,'buttons':rows,'cases':cases,'errors':errors}
    report['violations']=[row for row in static+rows if row['issues']]
    report['unclassified']=[row for row in static+rows if row['unclassified']]
    args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'template_buttons':len(static),'rendered_buttons':len(rows),'cases':len(cases),'violations':len(report['violations']),'unclassified':len(report['unclassified']),'errors':len(errors)}))
    return bool(report['violations'] or errors)


if __name__=='__main__':raise SystemExit(main())
