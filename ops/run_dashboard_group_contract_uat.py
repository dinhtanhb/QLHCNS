"""Compare Dashboard DTO, links and queries on a marked synthetic demo."""
import argparse,json,os,sys
from pathlib import Path
from datetime import date
from decimal import Decimal


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--phase',choices=('before','after'),required=True);p.add_argument('--baseline-templates',type=Path);p.add_argument('--source-root',type=Path);a=p.parse_args();root=a.source_root.resolve() if a.source_root else Path(__file__).resolve().parents[1];f=a.directory.resolve()
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

 from django.core.serializers.json import DjangoJSONEncoder
 from django.contrib.auth.hashers import make_password
 password=next(x.split(': ',1)[1] for x in (f/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
 for username,role_code in [('demo-sys','SYS_ADMIN'),('demo-unlinked','EMPLOYEE')]:
  role,_=Role.objects.get_or_create(role_code=role_code,defaults={'role_name':role_code})
  user,created=User.objects.get_or_create(username=username,defaults={'role':role})
  if created:user.password=make_password(password);user.save(update_fields=['password'])
 accounts=['demo-employee','demo-manager','demo-hr-officer','demo-hr','demo-director','demo-finance','demo-sys','demo-layout-admin','demo-unlinked']
 report={'synthetic_only':True,'cases':{},'failures':[]}
 baseline=json.loads((f/'dashboard-group-before.json').read_text(encoding='utf-8')) if a.phase=='after' else None
 for name in accounts:
  user=User.objects.get(username=name);client=Client();client.force_login(user);cache.clear();connection.queries_log.clear()
  with CaptureQueriesContext(connection) as queries:response=client.get(reverse('portal:dashboard'))
  sql=list(queries);count=sum(q['sql'].lstrip().upper().startswith('SELECT') for q in sql)
  import re
  writes=[re.match(r'(?:INSERT INTO|UPDATE|DELETE FROM)\s+([^\s(]+)',q['sql'],re.I).group(1) for q in sql if re.match(r'(?:INSERT INTO|UPDATE|DELETE FROM)\s+',q['sql'],re.I)]
  if any(table.strip('"[]') != 'django_session' for table in writes):
   report['failures'].append(name+' business write during Dashboard GET')
  snapshot=dict(response.context['dashboard_snapshot']);snapshot.pop('generated_at',None)
  normalized=json.loads(json.dumps(snapshot,cls=DjangoJSONEncoder))
  bad=[]
  for target in InternalLinks(response.content.decode()).links:
   result=client.get(target)
   if result.status_code not in (200,302):bad.append([target,result.status_code])
   if getattr(result,'streaming',False):result.close()
  report['cases'][name]={'write_tables':writes,'status':response.status_code,'selects':count,'snapshot':normalized,'bad_links':bad,'write_queries':sum(q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for q in sql)}
  if baseline:
   old=baseline['cases'][name]
   if normalized!=old['snapshot']:report['failures'].append(name+' changed snapshot')
   if count>old['selects']:report['failures'].append(name+' increased queries')
   if bad:report['failures'].append(name+' invalid links '+str(bad))
  if baseline and report['cases'][name]['write_queries']>old['write_queries']:report['failures'].append(name+' increased GET writes')
 (f/('dashboard-group-'+a.phase+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'phase':a.phase,'queries':{k:v['selects'] for k,v in report['cases'].items()},'failures':report['failures']}));return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
