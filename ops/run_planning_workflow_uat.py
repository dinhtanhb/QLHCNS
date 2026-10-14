"""Exercise planning writes in Edge on an explicitly marked disposable demo."""
import argparse,json,os,sys,uuid
from datetime import timedelta
from pathlib import Path


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--packages-dir',type=Path,required=True);p.add_argument('--port',type=int,default=8782);a=p.parse_args();root=Path(__file__).resolve().parents[1];f=a.directory.resolve()
 if f==root or root in f.parents:p.error('External synthetic runtime required.')
 m=json.loads((f/'synthetic-demo.json').read_text(encoding='utf-8'))
 if m.get('synthetic_only') is not True:p.error('Synthetic marker required.')
 sys.path[:0]=[str(root/'src'),str(a.packages_dir.resolve())];os.environ.update(APP_ENV='test',DB_ENGINE='django.db.backends.sqlite3',DJANGO_SETTINGS_MODULE='config.settings',SECRET_KEY=m['secret_key'],M365_STORAGE_ENABLED='False',DJANGO_ALLOW_ASYNC_UNSAFE='true')
 import config.settings as cfg
 cfg.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(f/'synthetic.sqlite3')}};cfg.MEDIA_ROOT=f/'media'
 for h in cfg.LOGGING['handlers'].values():
  if 'filename' in h:h['filename']=str(f/Path(h['filename']).name)
 import django;django.setup()
 from django.utils import timezone
 from django.urls import reverse
 from apps.security.models import User
 from playwright.sync_api import sync_playwright
 from apps.kpi.models import KPIPeriod,KPITemplate,EmployeeKPI
 from apps.attendance.models import Holiday
 from decimal import Decimal
 password=next(x.split(': ',1)[1] for x in (f/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
 out=f/'planning-workflow-uat';out.mkdir(exist_ok=True);report={'synthetic_only':True,'checks':[],'failures':[],'limits':['No training-registration route exists in portal; training enrollment is read-only.']};stamp=uuid.uuid4().hex[:10];base=f'http://127.0.0.1:{a.port}'
 def check(ok,label):report['checks' if ok else 'failures'].append(label)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True);context=browser.new_context(service_workers='block',reduced_motion='reduce');page=context.new_page()
  def login(name):
   context.clear_cookies();page.goto(base+'/portal/login/');page.locator('[name=username]').fill(name);page.locator('[name=password]').fill(password);page.locator('main button[type=submit]').click();page.wait_for_load_state('networkidle')
  def submit(button):button.click();page.wait_for_load_state('networkidle')
  login('demo-hr');hr=User.objects.get(username='demo-hr');person=hr.employee
  period=KPIPeriod.objects.get(year=2026,month=10);template=KPITemplate.objects.create(kpi_name='FLOW-KPI-'+stamp,weight=Decimal('30'))
  page.goto(base+reverse('portal:kpi_assign_create'));form=page.locator('main form');form.locator('[name=employee]').select_option(str(person.pk));form.locator('[name=kpi_template]').select_option(str(template.pk));form.locator('[name=kpi_period]').select_option(str(period.pk));form.locator('[name=target]').fill('100');submit(form.locator('button[type=submit]'))
  result=EmployeeKPI.objects.filter(employee=person,kpi_template=template).first();check(result is not None,'KPI assignment persisted');check(page.locator('.ui-alert--success').count()>0,'KPI assignment notice');check(page.url.endswith(reverse('portal:kpi_score_list')),'KPI assignment destination')
  form=page.locator('form[action="'+reverse('portal:kpi_score_update',args=[result.pk])+'"]');field=form.locator('input[name=actual]:visible');field.fill('80');field.press('Enter');page.wait_for_load_state('networkidle');result.refresh_from_db();check(result.actual==80 and result.achievement==80 and result.score==24,'KPI actual, achievement and weighted score persisted');check(page.locator('.ui-alert--success').count()>0,'KPI scoring notice');check(page.url.endswith(reverse('portal:kpi_score_list')),'KPI scoring destination')
  page.locator('[name=period]').select_option(str(period.pk));page.locator('.ui-query-actions button').click();page.wait_for_load_state('networkidle');check('period='+str(period.pk) in page.url,'KPI period filter applied');check(page.get_by_text('Xóa lọc',exact=True).count()==1,'KPI reset visible');page.get_by_text('Xóa lọc',exact=True).click();page.wait_for_load_state('networkidle');check('period=' not in page.url,'KPI reset clears filter')
  holiday_date=timezone.localdate()+timedelta(days=4000)
  while Holiday.objects.filter(holiday_date=holiday_date).exists():holiday_date+=timedelta(days=1)
  page.goto(base+reverse('portal:holiday_list'));form=page.locator('main form:has([name=holiday_code])');form.locator('[name=holiday_code]').fill('FLOW-'+stamp);form.locator('[name=holiday_name]').fill('Ngày lễ giả '+stamp);form.locator('[name=holiday_date]').fill(holiday_date.isoformat());submit(form.locator('button'));holiday=Holiday.objects.get(holiday_code='FLOW-'+stamp);check(holiday.is_active,'holiday created');check(page.locator('.ui-alert--success').count()>0,'holiday create notice');form=page.locator('form[action="'+reverse('portal:holiday_delete',args=[holiday.pk])+'"]');form.locator('button').click();check(page.locator('#ui-confirm-dialog').is_visible(),'holiday delete confirmation');page.keyboard.press('Escape');holiday.refresh_from_db();check(holiday.is_active,'holiday Escape does not delete');form.locator('button').click();page.locator('[data-ui-confirm-accept]').click();page.wait_for_load_state('networkidle');holiday.refresh_from_db();check(not holiday.is_active,'holiday soft delete persisted');check(page.locator('.ui-alert--success').count()>0,'holiday delete notice')
  page.goto(base+reverse('portal:training_my_list'));check(page.get_by_text('Khóa đào tạo giả có tên dài kiểm tra bảng và trạng thái',exact=True).count()>0,'training own enrollment displayed');check(page.get_by_text('Đã đăng ký',exact=True).count()>0,'training enrollment status displayed');check(page.locator('main form[method=post]').count()==0,'training remains read-only')
  for name in ['event_list','report_hub','dashboard']:
   response=page.goto(base+reverse('portal:'+name));check(response.status==200,name+' available after writes')
  page.screenshot(path=str(out/'workflow-final.png'),full_page=True);browser.close()
 report['passed']=not report['failures'];(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'checks':len(report['checks']),'failures':report['failures'],'limits':report['limits']},ensure_ascii=False));return not report['passed']


if __name__=='__main__':raise SystemExit(main())
