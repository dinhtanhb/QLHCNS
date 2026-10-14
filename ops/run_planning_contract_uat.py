"""Compare planning GET/form/link/query contracts on a marked synthetic demo."""
import argparse,json,os,sys
from pathlib import Path
from datetime import date
from decimal import Decimal


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--phase',choices=('before','after'),required=True);p.add_argument('--baseline-templates',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1];f=a.directory.resolve()
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
 from apps.portal.test_personal_ui import Forms
 from apps.portal.ui_test_helpers import InternalLinks
 setup_test_environment()
 from apps.kpi.models import KPIPeriod,KPITemplate,EmployeeKPI
 from apps.planning.models import TrainingCourse,TrainingEnrollment
 from apps.attendance.models import Holiday
 people=list(Employee.objects.order_by('pk'))
 period,_=KPIPeriod.objects.get_or_create(year=2026,month=10)
 template,_=KPITemplate.objects.get_or_create(kpi_name='PLAN-UAT Tiêu chí dài để kiểm tra bố cục',defaults={'weight':30})
 for employee in people:
  EmployeeKPI.objects.get_or_create(employee=employee,kpi_template=template,kpi_period=period,defaults={'target':Decimal('100'),'actual':Decimal('0')})
 course,_=TrainingCourse.objects.get_or_create(course_code='PLAN-UAT',defaults={'course_name':'Khóa đào tạo giả có tên dài kiểm tra bảng và trạng thái','provider':'Đơn vị đào tạo giả','start_date':date(2026,10,1)})
 for employee in people:TrainingEnrollment.objects.get_or_create(course=course,employee=employee)
 Holiday.objects.get_or_create(holiday_code='PLAN-UAT',defaults={'holiday_name':'Ngày lễ giả kiểm tra nhãn chữ','holiday_date':date(2026,10,20)})
 names=['holiday_list','training_my_list','kpi_score_list','kpi_assign_create','event_list','report_hub']
 routes={n:reverse('portal:'+n) for n in names}
 report={'synthetic_only':True,'routes':routes,'cases':{},'failures':[],'links':{},'source':{}}
 template_root=root/'src/apps/portal/templates/portal';stems=['holiday_list','training_my_list','kpi_score_list','kpi_assign_create']
 import re
 for stem in stems:
  text=((a.baseline_templates/'portal' if a.baseline_templates else template_root)/(stem+'.html')).read_text(encoding='utf-8');classes=re.findall(r'class="([^"]*)"',text);report['source'][stem]={'old_tokens':sum(len(re.findall(r'(?<![\w-])(?:p[xy]?|m[trblxy]?|text|bg|border|rounded|shadow|gap|grid-cols|col-span|space-y|font|w|max-w|min-w|h|flex|items|justify|overflow|divide|tracking|leading)-[\w./:-]+',v)) for v in classes),'forms':len(re.findall(r'<form\b',text)),'csrf':text.count('{% csrf_token %}')}
 baseline_path=f/'planning-before.json';baseline=json.loads(baseline_path.read_text(encoding='utf-8')) if a.phase=='after' else None
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
     if isinstance(value,dict):
      # HTML number inputs require a dot; compare the same saved decimal semantically.
      if value.get('name')=='actual' and value.get('type')=='number':
       value=dict(value);value['value']=value.get('value','').replace(',','.')
      return {k:normalize(v) for k,v in value.items() if not (k=='value' and v=='' or k=='type' and v=='text')}
     return value
    for prop in ('status','forms'):
     current_value, old_value = report['cases'][key][prop], old[prop]
     if normalize(current_value)!=normalize(old_value):report['failures'].append(key+' changed '+prop)
    if query_count>old['queries']:report['failures'].append(key+' increased queries '+str(old['queries'])+' -> '+str(query_count))
    for target,status in report['links'][code].items():
     if status not in (200,302) and status!=baseline['links'][code].get(target):report['failures'].append(code+' new broken link '+target+' '+str(status))
 out=f/('planning-'+a.phase+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'phase':a.phase,'cases':len(report['cases']),'failures':report['failures'],'existing_broken_links':sum(v not in (200,302) for links in report['links'].values() for v in links.values())}));return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
