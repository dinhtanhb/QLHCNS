"""Compare administration GET/form/link/query contracts on a marked synthetic demo."""
import argparse,json,os,sys
from pathlib import Path
from datetime import date


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--phase',choices=('before','after'),required=True);p.add_argument('--baseline-templates',type=Path);p.add_argument('--allow-cancel-ui',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1];f=a.directory.resolve()
 if f==root or root in f.parents:p.error('External synthetic data required.')
 marker=json.loads((f/'synthetic-demo.json').read_text(encoding='utf-8'))
 if marker.get('synthetic_only') is not True:p.error('Synthetic marker required.')
 sys.path.insert(0,str(root/'src'));os.environ.update(APP_ENV='test',DB_ENGINE='django.db.backends.sqlite3',DJANGO_SETTINGS_MODULE='config.settings',SECRET_KEY=marker['secret_key'],M365_STORAGE_ENABLED='False')
 import config.settings as cfg
 cfg.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(f/'synthetic.sqlite3')}};cfg.MEDIA_ROOT=f/'media'
 for h in cfg.LOGGING['handlers'].values():
  if 'filename' in h:h['filename']=str(f/Path(h['filename']).name)
 if a.baseline_templates:
  cfg.TEMPLATES[0]['DIRS']=[str(a.baseline_templates.resolve())]+list(cfg.TEMPLATES[0]['DIRS'])
 import django;django.setup()
 from django.core.cache import cache
 from django.test import Client
 from django.test.utils import CaptureQueriesContext,setup_test_environment
 from django.db import connection
 from django.urls import reverse
 from apps.security.models import Role,User
 from apps.hrm.models import Employee
 from apps.asset.models import InventorySession,AssetDisposalRequest
 from apps.document.models import DispatchBook,OfficialDispatch
 from apps.portal.test_personal_ui import Forms
 from apps.portal.ui_test_helpers import InternalLinks
 setup_test_environment()
 people=list(Employee.objects.order_by('pk'));book,_=DispatchBook.objects.get_or_create(book_code='ADMIN-UAT',defaults={'book_name':'Sổ giả','book_type':'Incoming','year':2026})
 dispatch,_=OfficialDispatch.objects.get_or_create(dispatch_no='ADMIN-UAT-001',defaults={'dispatch_type':'Incoming','dispatch_book':book,'title':'Công văn giả có tiêu đề dài để kiểm tra bố cục chi tiết và lịch sử','issuing_organization':'Tổ chức giả','issue_date':date(2026,10,1),'received_or_sent_date':date(2026,10,1),'assigned_to':people[0],'department':people[0].department})
 session=InventorySession.objects.order_by('pk').first();disposal=AssetDisposalRequest.objects.order_by('pk').first()
 names=['asset_admin_list','asset_list','dispatch_create','dispatch_list','document_approval_list','document_list','event_list','inventory_session_list','procurement_request_list','room_booking_approval_list','room_booking_list','supply_request_approval_list','supply_request_list','vehicle_booking_approval_list','vehicle_booking_list','disposal_request_list','disposal_request_create']
 routes={n:reverse('portal:'+n) for n in names};routes.update(dispatch_detail=reverse('portal:dispatch_detail',args=[dispatch.pk]),inventory_session_detail=reverse('portal:inventory_session_detail',args=[session.pk]),disposal_request_detail=reverse('portal:disposal_request_detail',args=[disposal.pk]))
 report={'synthetic_only':True,'routes':routes,'cases':{},'failures':[],'links':{},'source':{}}
 template_root=root/'src/apps/portal/templates/portal';stems=['asset_admin_list','asset_list','dispatch_create','dispatch_detail','dispatch_list','disposal_request_detail','disposal_request_form','disposal_request_list','document_approval_list','document_list','event_list','inventory_session_detail','inventory_session_list','office_incoming_list','office_outgoing_list','procurement_request_list','room_booking_approval_list','room_booking_list','supply_request_approval_list','supply_request_list','vehicle_booking_approval_list','vehicle_booking_list','_office_booking_approvals']
 import re
 for stem in stems:
  text=((a.baseline_templates/'portal' if a.baseline_templates else template_root)/(stem+'.html')).read_text(encoding='utf-8');classes=re.findall(r'class="([^"]*)"',text);report['source'][stem]={'old_tokens':sum(len(re.findall(r'(?<![\w-])(?:p[xy]?|m[trblxy]?|text|bg|border|rounded|shadow|gap|grid-cols|col-span|space-y|font|w|max-w|min-w|h|flex|items|justify|overflow|divide|tracking|leading)-[\w./:-]+',v)) for v in classes),'forms':len(re.findall(r'<form\b',text)),'csrf':text.count('{% csrf_token %}')}
 baseline_path=f/'administration-before.json';baseline=json.loads(baseline_path.read_text(encoding='utf-8')) if a.phase=='after' else None
 for idx,code in enumerate(('EMPLOYEE','DEPT_MANAGER','HR_OFFICER','HR_MANAGER','DIRECTOR','FINANCE_OFFICER','SYS_ADMIN','SUPERUSER','UNLINKED')):
  role,_=Role.objects.get_or_create(role_code=code if code not in ('SUPERUSER','UNLINKED') else 'EMPLOYEE',defaults={'role_name':code})
  u=User.objects.filter(role=role,employee__isnull=False).first() if code not in ('SUPERUSER','UNLINKED') else None
  if u is None:u,_=User.objects.get_or_create(username='admin-uat-'+code.lower(),defaults={'role':role,'is_superuser':code=='SUPERUSER'})
  c=Client();c.force_login(u);report['links'][code]={}
  for name,url in routes.items():
   cache.clear()
   connection.queries_log.clear()
   with CaptureQueriesContext(connection) as q:response=c.get(url)
   query_count=len(q)
   forms=[]
   if response.status_code==200:
    for form in Forms(response.content.decode()).forms:
     attrs=form['attrs'];fields=[{k:v for k,v in x.items() if k in ('name','type','value','min','max','step','required','multiple','form') and x.get('name')!='csrfmiddlewaretoken'} for x in form['fields'] if x.get('name')!='csrfmiddlewaretoken']
     forms.append({'method':attrs.get('method','get').lower(),'action':attrs.get('action',''),'enctype':attrs.get('enctype',''),'fields':fields,'csrf':any(x.get('name')=='csrfmiddlewaretoken' for x in form['fields'])})
    for target in InternalLinks(response.content.decode()).links:
     if target in report['links'][code]:continue
     result=c.get(target);report['links'][code][target]=result.status_code
     if getattr(result,'streaming',False):result.close()
   key=code+'/'+name;report['cases'][key]={'status':response.status_code,'queries':query_count,'forms':forms}
   if baseline:
    old=baseline['cases'][key]
    def normalize(value):
     if isinstance(value,list):return [normalize(x) for x in value]
     if isinstance(value,dict):return {k:normalize(v) for k,v in value.items() if not (k=='value' and v=='' or k=='type' and v=='text')}
     return value
    for prop in ('status','forms'):
     current_value, old_value = report['cases'][key][prop], old[prop]
     if a.allow_cancel_ui and prop=='forms':
      # Authorized UI restoration adds owner-only POST forms; all other forms stay exact.
      def without_cancel(forms):return [f for f in forms if not (f['action'].endswith('/cancel/') and ('/rooms/' in f['action'] or '/vehicles/' in f['action']))]
      current_value,old_value=without_cancel(current_value),without_cancel(old_value)
     if normalize(current_value)!=normalize(old_value):report['failures'].append(key+' changed '+prop)
    if query_count>old['queries']:report['failures'].append(key+' increased queries '+str(old['queries'])+' -> '+str(query_count))
    for target,status in report['links'][code].items():
     if status not in (200,302) and status!=baseline['links'][code].get(target):report['failures'].append(code+' new broken link '+target+' '+str(status))
 out=f/('administration-'+a.phase+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'phase':a.phase,'cases':len(report['cases']),'failures':report['failures'],'existing_broken_links':sum(v not in (200,302) for links in report['links'].values() for v in links.values())}));return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
