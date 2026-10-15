"""Measure screen alignment in Edge using marked, external synthetic data.

Inventory comes from Django URL patterns, including parameterized routes. GET
statuses and non-HTML downloads are recorded, never mistaken for layout passes.
Only form controls outside paper/editor templates are measured. Reports remain
outside Git; --only accepts route names or path/module fragments.
"""
import argparse
import asyncio
from collections import Counter
import inspect
import json
import os
from pathlib import Path
import re
import sys


MEASURE = r"""() => {
 const violations=[], measurements={};
 const rect=x=>{const r=x.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}};
 const visible=x=>x.checkVisibility()&&x.getBoundingClientRect().width>0;
 const selector=x=>x.id?'#'+x.id:x.tagName.toLowerCase()+(typeof x.className==='string'&&x.className.trim()?'.'+x.className.trim().replaceAll(' ','.'):'');
 const fail=(code,x,value)=>violations.push({code,selector:selector(x),value,rect:rect(x)});
 const main=document.querySelector('.ui-main'), wrap=document.querySelector('.ui-main-wrap');
 if(!main)return {violations:[],measurements:{no_portal_shell:true}};
 const content=main.querySelector('.ui-page')||main;
 if(content&&wrap){const p=rect(wrap),c=rect(content),s=getComputedStyle(wrap),left=p.x+parseFloat(s.paddingLeft),right=p.right-parseFloat(s.paddingRight);measurements.frame={main:rect(main),wrap:p,content:c,left:c.x-left,right:right-c.right};if(Math.abs(measurements.frame.left-measurements.frame.right)>2)fail('FRAME',content,measurements.frame);}
 if(document.documentElement.scrollWidth>innerWidth+1)fail('OVERFLOW',main,{width:innerWidth,scrollWidth:document.documentElement.scrollWidth});
 const screen=x=>!x.closest('.hcns-paper,.hcns-editor,[hidden],.ui-number-source');
 const controls=[...main.querySelectorAll('input,select,textarea')].filter(x=>visible(x)&&screen(x)&&!['hidden','checkbox','radio'].includes(x.type));
 for(const f of main.querySelectorAll('form')){const fields=controls.filter(x=>x.form===f);if(fields.length>12&&!f.querySelector('fieldset'))fail('FORM_GROUPS',f,fields.length);for(const c of fields){if(['full_name','address','reason','description','notes'].includes(c.name)&&rect(c.closest('.ui-field')||c).w<(rect(c.closest('.ui-form-grid')||f).w-parseFloat(getComputedStyle(c.closest('.ui-form-grid')||f).columnGap||0))/2-9)fail('LONG_FIELD',c,{width:rect(c).w,form:rect(f).w});const hint=(c.closest('.ui-field')||c.parentElement).querySelector('.ui-field-help,.ui-hr-text');if(hint&&visible(hint)&&!c.getAttribute('aria-describedby')?.split(' ').includes(hint.id))fail('HINT_ASSOCIATION',c,hint.textContent);}}
 for(const c of controls){const s=getComputedStyle(c);if(rect(c).h<43.5)fail('CONTROL_HEIGHT',c,rect(c).h);if(parseFloat(s.fontSize)<14)fail('FONT',c,s.fontSize);if(![...c.labels||[]].some(visible))fail('LABEL',c,c.name);if(['date','month'].includes(c.type)&&!c.parentElement.querySelector('.ui-date-echo'))fail('DATE_ECHO',c,c.type);if(['date','month'].includes(c.type)&&!c.hasAttribute('lang'))fail('DATE_LANGUAGE',c,c.type);}
 const grids=[...main.querySelectorAll('.ui-form-grid')].filter(x=>visible(x)&&screen(x));measurements.grids=[];
 measurements.grid_rules=[];
 const rules=(items,source,active=true)=>{for(const rule of items){if(rule.selectorText?.includes('.ui-form-grid')&&rule.style?.gridTemplateColumns)measurements.grid_rules.push({source,selector:rule.selectorText,columns:rule.style.gridTemplateColumns,active});if(rule.cssRules)rules(rule.cssRules,source,active&&(!rule.conditionText||matchMedia(rule.conditionText).matches));}};
 for(const sheet of document.styleSheets){try{rules(sheet.cssRules,sheet.href||'inline')}catch(error){}}
 for(const g of grids){const r=rect(g),s=getComputedStyle(g),gap=parseFloat(s.columnGap)||0,col=(r.w-11*gap)/12;
  const fields=controls.filter(x=>x.closest('.ui-form-grid')===g),rows=[];
  for(const c of fields){const field=c.closest('.ui-field')||c.parentElement,fr=rect(field),cr=rect(c);let row=rows.find(x=>Math.abs(x.y-fr.y)<=1);if(!row){row={y:fr.y,fields:[]};rows.push(row);}row.fields.push({name:c.name,field:fr,control:cr});
   const near=(edge,end=false)=>Array.from({length:13},(_,i)=>r.x+i*(col+gap)-(end&&i?gap:0)).some(x=>Math.abs(x-edge)<=1);
   if(innerWidth>=1024&&(!near(fr.x)||!near(fr.right,true)))fail('COLUMN_LINE',field,{grid:r,field:fr,columns:s.gridTemplateColumns});
   if(Math.abs(fr.right-cr.right)>1||Math.abs(fr.x-cr.x)>1)fail('FIELD_EDGE',c,{field:fr,control:cr});
  }
  for(const row of rows){const ys=row.fields.map(x=>x.control.y),hs=row.fields.map(x=>x.control.h);if(Math.max(...ys)-Math.min(...ys)>1)fail('ROW_TOP',g,row);if(Math.max(...hs)-Math.min(...hs)>1)fail('ROW_HEIGHT',g,row);}
  for(let i=0;i<rows.length-1;i++){const bottom=Math.max(...rows[i].fields.map(x=>x.field.bottom)),next=rows[i+1].y,between=[...g.children].some(x=>visible(x)&&rect(x).y>=bottom&&rect(x).bottom<=next&&!x.matches('.ui-field'));if(!between&&Math.abs(next-bottom-(parseFloat(s.rowGap)||0))>1)fail('ROW_GAP',g,{bottom,next,gap:next-bottom,expected:s.rowGap});}
  const nonlast=rows.slice(0,-1);for(const row of nonlast){const last=row.fields.at(-1);if(last&&r.right-last.field.right>col+gap+1)fail('ROW_HOLE',g,row);}
  measurements.grids.push({selector:selector(g),rect:r,columns:s.gridTemplateColumns,rows});
 }
 for(const group of main.querySelectorAll('.ui-form-actions')){if(!visible(group)||!screen(group))continue;const buttons=[...group.children].filter(x=>x.matches('button,a')&&visible(x));if(buttons.length>1){const sizes=buttons.map(rect);if(Math.max(...sizes.map(x=>x.h))-Math.min(...sizes.map(x=>x.h))>1)fail('FORM_BUTTON_HEIGHT',group,sizes);if(innerWidth<600&&Math.max(...sizes.map(x=>x.w))-Math.min(...sizes.map(x=>x.w))>1)fail('FORM_BUTTON_WIDTH',group,sizes);}}
 const h1=[...main.querySelectorAll('h1')].filter(x=>visible(x)&&screen(x));if(h1.length!==1)fail('H1',main,h1.length);
 for(const f of main.querySelectorAll('form[method=post],form[method=POST]')){if(!visible(f)||!screen(f))continue;const b=[...f.querySelectorAll('button[type=submit],input[type=submit]')].find(visible),first=controls.find(x=>x.form===f);if(b&&first&&!b.closest('table,.ui-query-bar')&&Math.abs(rect(b).x-rect(first.closest('.ui-field')||first.parentElement).x)>1)fail('FORM_ACTION',b,{button:rect(b),first:rect(first)});}
 for(const q of main.querySelectorAll('.ui-query-bar')){const fields=[...q.querySelectorAll('input,select')].filter(x=>visible(x)&&x.type!=='hidden'&&!x.classList.contains('ui-number-source')),b=q.querySelector('button[type=submit]');if(!fields.length||!b||!visible(b))continue;const f=rect(fields.at(-1)),br=rect(b);if(Math.abs(f.bottom-br.bottom)<=1&&br.x-f.right>17)fail('FILTER_ACTION',b,{gap:br.x-f.right});}
 for(const c of main.querySelectorAll('td.ui-number'))if(visible(c)&&screen(c)&&getComputedStyle(c).textAlign!=='right')fail('NUMBER_ALIGN',c,getComputedStyle(c).textAlign);
 return {violations,measurements};
}"""


def configure(root, folder):
    marker = json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:
        raise RuntimeError('Synthetic marker required')
    sys.path.insert(0, str(root/'src'))
    os.environ.update(APP_ENV='test', DB_ENGINE='django.db.backends.sqlite3',
        DJANGO_SETTINGS_MODULE='config.settings', SECRET_KEY=marker['secret_key'], M365_STORAGE_ENABLED='False')
    import config.settings as cfg
    cfg.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(folder/'synthetic.sqlite3'), 'OPTIONS': {'timeout': 30}}}
    cfg.MEDIA_ROOT = folder/'media'
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = str(folder/('alignment-'+Path(handler['filename']).name))
    import django
    django.setup()


def inventory(only):
    from django.apps import apps
    from django.urls import get_resolver, reverse, URLResolver
    models = {model.__name__: model for model in apps.get_models()}
    entries=[]
    def walk(patterns, namespace=''):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                if pattern.namespace=='admin':
                    continue  # Django Admin has its own layout and no portal components.
                walk(pattern.url_patterns, namespace+(pattern.namespace+':' if pattern.namespace else ''))
                continue
            if not pattern.name:
                continue
            name=namespace+pattern.name
            if only and not any(key in name or key in str(pattern.pattern) for key in only):
                continue
            converters=getattr(pattern.pattern,'converters',{})
            callback=inspect.unwrap(pattern.callback)
            try:source=inspect.getsource(callback)
            except (OSError,TypeError):source=''
            model_names=re.findall(r'get_object_or_404\(\s*([A-Z]\w+)',source)
            model_names+=re.findall(r'\b([A-Z]\w+)\.objects',source)
            selected=next((models[key] for key in model_names if key in models),None)
            explicit={'profile_change_request_decide':'EmployeeProfileChangeRequest',
                'profile_change_request_attachment':'EmployeeProfileChangeRequest',
                'lifecycle_case_detail':'EmployeeLifecycleCase','lifecycle_item_assign':'LifecycleChecklistItem',
                'lifecycle_item_update':'LifecycleChecklistItem','leave_approve':'LeaveRequest',
                'task_detail':'Task','activity_update':'Activity','activity_proposal':'Activity',
                'activity_proposal_decide':'ActivityProposal','activity_proposal_file':'ActivityProposal',
                'kpi_score_update':'EmployeeKPI','hr_interview_result':'Interview',
                'hr_offer_update_status':'Offer','document_approve':'Document','payslip_pdf':'Payslip',
                'notification_outbox_mark_sent':'NotificationEmailOutbox','supply_request_issue':'SupplyRequest'}
            if pattern.name in explicit:selected=models.get(explicit[pattern.name],selected)
            kwargs={};unresolved=[]
            for key,converter in converters.items():
                kind=converter.__class__.__name__
                if key=='slug':kwargs[key]='labor-contract'
                elif key=='history_type':kwargs[key]='transfer'
                elif key=='export_format':kwargs[key]='xlsx'
                elif key=='action':kwargs[key]='submit'
                elif key=='field_name':kwargs[key]='proposal_pdf'
                elif key=='name':kwargs[key]='layout-audit-no-private-file.pdf'
                elif kind=='IntConverter':
                    obj=selected.objects.order_by('pk').first() if selected else None
                    if obj:kwargs[key]=obj.pk
                    else:unresolved.append(key)
                else:unresolved.append(key)
            if unresolved:entries.append({'name':name,'unresolved':unresolved,'pattern':str(pattern.pattern),'model':selected.__name__ if selected else None});continue
            try:entries.append({'name':name,'url':reverse(name,kwargs=kwargs),'kwargs':kwargs})
            except Exception as error:entries.append({'name':name,'unresolved':[type(error).__name__]})
    walk(get_resolver().url_patterns)
    return entries


def seed_missing_fixtures():
    """Only called by explicit --seed in a marked disposable database."""
    from django.apps import apps
    from django.db import models
    from django.utils import timezone
    allowed={'EmployeeProfileChangeRequest','EmployeeLifecycleCase','LifecycleChecklistItem',
             'ChecklistTemplate','ChecklistTemplateItem','Interview','Offer','Task','Activity','ActivityProposal',
             'Payslip','Document','DocumentCategory','NotificationEmailOutbox'}
    def make(model,depth=0):
        existing=model.objects.order_by('pk').first()
        if existing:return existing
        if model.__name__ not in allowed or depth>5:raise RuntimeError('Missing prerequisite '+model.__name__)
        values={}
        for field in model._meta.fields:
            if field.primary_key or field.auto_created or getattr(field,'auto_now',False) or getattr(field,'auto_now_add',False) or field.has_default() or field.null:continue
            if field.is_relation:values[field.name]=make(field.remote_field.model,depth+1)
            elif field.choices:values[field.name]=list(field.flatchoices)[0][0]
            elif isinstance(field,models.DateTimeField):values[field.name]=timezone.now()
            elif isinstance(field,models.DateField):values[field.name]=timezone.localdate()
            elif isinstance(field,(models.IntegerField,models.DecimalField,models.FloatField)):values[field.name]=1
            elif isinstance(field,models.BooleanField):values[field.name]=False
            elif isinstance(field,models.EmailField):values[field.name]='layout-audit@example.test'
            elif isinstance(field,models.FileField):values[field.name]=''
            else:values[field.name]=('LAYOUT-'+model.__name__+'-'+field.name)[:field.max_length or 100]
        return model.objects.create(**values)
    for model in apps.get_models():
        if model.__name__ in allowed:make(model)


async def audit(args, routes, output):
    from playwright.async_api import async_playwright
    password=next(line.split(': ',1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    accounts=args.accounts or ['demo-layout-admin','demo-hr','demo-director','demo-manager','demo-employee','demo-finance','demo-hr-officer','demo-sys','demo-unlinked']
    cases=[];semaphore=asyncio.Semaphore(args.workers);login_lock=asyncio.Lock();captured=set()
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(channel='msedge',headless=True)
        async def account_run(account):
            async with semaphore:
                context=await browser.new_context(viewport={'width':1756,'height':920},locale='vi-VN',service_workers='block',reduced_motion='reduce')
                page=await context.new_page();base=f'http://127.0.0.1:{args.port}'
                async with login_lock:
                    await page.goto(base+'/portal/login/');await page.locator('[name=username]').fill(account);await page.locator('[name=password]').fill(password);await page.locator('main form button[type=submit]').click();await page.wait_for_load_state('domcontentloaded')
                for route in routes:
                    if 'url' not in route:continue
                    case={'route':route['name'],'account':account,'url':route['url']}
                    try:
                        response=await page.request.get(base+route['url'],max_redirects=0);case['status']=response.status
                        content_type=response.headers.get('content-type','')
                        if response.status!=200 or 'text/html' not in content_type:
                            case['skip']='HTTP '+str(response.status)+' or non-HTML '+content_type;cases.append(case);continue
                        await page.goto(base+route['url'],wait_until='load')
                        if not await page.locator('.ui-main').count():case['skip']='No portal shell';cases.append(case);continue
                        for width in args.widths:
                            await page.set_viewport_size({'width':width,'height':920})
                            for theme in ('light','dark'):
                                await page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                                result=await page.evaluate(MEASURE)
                                item=dict(case,width=width,theme=theme,**result)
                                image_key=(route['name'],width)
                                if result['violations'] and width in (1756,390) and theme=='light' and image_key not in captured:
                                    captured.add(image_key)
                                    filename=re.sub(r'[^a-zA-Z0-9_-]','-',route['name'])+'-'+account+'-'+str(width)+'.png'
                                    await page.screenshot(path=str(output/filename),full_page=True);item['screenshot']=filename
                                cases.append(item)
                    except Exception as error:cases.append(dict(case,error=str(error)))
                await context.close()
                (output/('progress-'+account+'.json')).write_text(json.dumps([case for case in cases if case.get('account')==account],ensure_ascii=False),encoding='utf-8')
                print('Finished '+account,flush=True)
        await asyncio.gather(*(account_run(account) for account in accounts))
        await browser.close()
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--packages-dir',type=Path,required=True)
    parser.add_argument('--source-root',type=Path)
    parser.add_argument('--port',type=int,default=8782)
    parser.add_argument('--phase',choices=('before','after'),required=True)
    parser.add_argument('--only',nargs='+')
    parser.add_argument('--accounts',nargs='+')
    parser.add_argument('--widths',nargs='+',type=int,default=[1920,1756,1440,1280,1024,768,390])
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--seed',action='store_true',help='Create missing synthetic route fixtures in this marked external DB.')
    parser.add_argument('--output-dir',type=Path,help='Optional external report folder for a focused run.')
    args=parser.parse_args();root=(args.source_root or Path(__file__).resolve().parents[1]).resolve();args.directory=args.directory.resolve()
    if root==args.directory or root in args.directory.parents:parser.error('Runtime must be external.')
    sys.path.insert(0,str(args.packages_dir.resolve()));configure(root,args.directory)
    if args.seed:seed_missing_fixtures()
    output=(args.output_dir or args.directory/('alignment-'+args.phase)).resolve()
    if output==root or root in output.parents:parser.error('Reports must remain outside source.')
    output.mkdir(exist_ok=True,parents=True)
    routes=inventory(args.only)
    (output/'route-inventory.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2),encoding='utf-8')
    cases=asyncio.run(audit(args,routes,output))
    waivers=json.loads((Path(__file__).parent/'layout_waivers.json').read_text(encoding='utf-8'))
    violations=[]
    for case in cases:
        for violation in case.get('violations',[]):
            if args.phase=='before' and violation['code']=='DATE_ECHO':continue
            if not any(w.get('route')==case['route'] and w.get('criterion')==violation['code'] for w in waivers):violations.append(dict(route=case['route'],account=case['account'],width=case['width'],theme=case['theme'],**violation))
    counts=Counter(v['route'].split(':')[-1].split('_')[0] for v in violations)
    report={'phase':args.phase,'synthetic_only':True,'routes':routes,'cases':cases,'violations':violations,'by_module':dict(counts),'errors':[case for case in cases if 'error' in case],'waivers':waivers}
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Layout alignment '+args.phase,'','| Route | Account | Width/theme | Criterion | Selector |','|---|---|---|---|---|']
    for v in violations:lines.append(f"| {v['route']} | {v['account']} | {v['width']}/{v['theme']} | {v['code']} | {v['selector']} |")
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    causes=[]
    for css in (root/'src/static/css').glob('*.css'):
        if css.name=='tailwind.css':continue
        for line_number,line in enumerate(css.read_text(encoding='utf-8').splitlines(),1):
            if '.ui-form-grid' in line and 'grid-template-columns' in line:
                causes.append({'file':str(css.relative_to(root)),'line':line_number,'rule':line.strip()})
    (output/'grid-sources.json').write_text(json.dumps(causes,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'routes':len(routes),'cases':len(cases),'violations':len(violations),'by_module':dict(counts),'errors':len(report['errors']),'output':str(output)}))
    return bool(violations or report['errors'])


if __name__=='__main__':raise SystemExit(main())
