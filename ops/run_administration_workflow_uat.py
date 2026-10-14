"""Exercise administration writes in Edge on an explicitly marked disposable demo."""
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
 from apps.organization.models import Position
 from apps.security.models import User
 from apps.document.models import OfficialDispatch,DispatchTracking
 from apps.procurement.models import ProcurementRequest
 from apps.asset.models import AssetType,Asset,AssetDisposalRequest,AssetDisposalItem,AssetDisposalMinutes,InventorySession,InventoryLine
 from apps.office.models import MeetingRoom,Vehicle,RoomBooking,VehicleBooking
 from playwright.sync_api import sync_playwright
 director=User.objects.get(username='demo-director').employee
 position,_=Position.objects.get_or_create(position_code='ADMIN-UAT-DIRECTOR',defaults={'position_name':'Giám đốc giả lập'})
 director.position=position;director.save(update_fields=['position'])
 password=next(x.split(': ',1)[1] for x in (f/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
 out=f/'administration-workflow-uat';out.mkdir(exist_ok=True);report={'synthetic_only':True,'checks':[],'failures':[]};stamp=uuid.uuid4().hex[:10];base=f'http://127.0.0.1:{a.port}'
 def check(ok,label):report['checks' if ok else 'failures'].append(label)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True);context=browser.new_context(service_workers='block',reduced_motion='reduce');page=context.new_page()
  def login(name):
   context.clear_cookies();page.goto(base+'/portal/login/');page.locator('[name=username]').fill(name);page.locator('[name=password]').fill(password);page.locator('main button[type=submit]').click();page.wait_for_load_state('networkidle')
  def submit(button):
   button.click()
   if page.locator('#ui-confirm-dialog').is_visible():page.locator('[data-ui-confirm-accept]').click()
   page.wait_for_load_state('networkidle')
  login('demo-hr');hr=User.objects.get(username='demo-hr');person=hr.employee
  # Create and cancel room/vehicle requests via their real browser forms.
  room=MeetingRoom.objects.create(room_code='FLOW-'+stamp,room_name='Phòng giả '+stamp)
  vehicle=Vehicle.objects.create(vehicle_code='FLOW-'+stamp,vehicle_name='Xe giả '+stamp,plate_number='FAKE-'+stamp)
  for route,resource,model,extra in [('room_booking_list',room,RoomBooking,{}),('vehicle_booking_list',vehicle,VehicleBooking,{'destination':'Điểm đến giả'})]:
   page.goto(base+reverse('portal:'+route));form=page.locator('form[action="'+reverse('portal:'+route.replace('_list','_create'))+'"]');field='room' if route.startswith('room') else 'vehicle';form.locator('[name='+field+']').select_option(str(resource.pk));form.locator('[name=purpose]').fill('Họp thử '+stamp);start=timezone.localtime()+timedelta(days=60);form.locator('[name=start_time]').fill(start.strftime('%Y-%m-%dT%H:%M'));form.locator('[name=end_time]').fill((start+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'))
   for name,value in extra.items():form.locator('[name='+name+']').fill(value)
   submit(form.locator('button[type=submit]'));check(model.objects.filter(employee=person,**{field:resource}).exists(),route+' create persisted');check(page.locator('.ui-alert--success').count()>0,route+' create notice')
   # Owner cancellation is required; Escape must leave the pending reservation intact.
   record=model.objects.filter(employee=person,**{field:resource}).latest('pk');cancel=page.locator('form[action="'+reverse('portal:'+route.replace('_list','_cancel'),args=[record.pk])+'"]')
   check(cancel.count()==1,route+' owner cancel visible')
   if cancel.count():
    cancel.locator('button').click();page.keyboard.press('Escape');record.refresh_from_db();check(record.status=='Pending',route+' cancel Escape retains state');submit(cancel.locator('button'));record.refresh_from_db();check(record.status=='Cancelled',route+' cancel persisted');check(page.locator('.ui-alert--success').count()>0,route+' cancel notice')
   else:report.setdefault('existing_limits',[]).append(route+' owner cancellation hidden by existing template condition')
  # Two procurement rows, including the dynamically added labeled row.
  page.goto(base+reverse('portal:procurement_request_list'));form=page.locator('form[action="'+reverse('portal:procurement_request_create')+'"]');form.locator('[name=reason]').fill('Mua sắm giả '+stamp);page.locator('#add-procurement-item').click()
  for i in range(2):
   form.locator('[name=item_name]').nth(i).fill('Hàng giả '+stamp+'-'+str(i));form.locator('[name=quantity]').nth(i).fill(str(i+1));cost=form.locator('[name=estimated_cost]').nth(i);cost_id=cost.get_attribute('id');proxy=page.locator('[id="'+cost_id+'-display"]') if cost_id else None;proxy.fill('100000') if proxy is not None and proxy.count() else cost.fill('100000')
  submit(form.locator('button[type=submit]'));request=ProcurementRequest.objects.filter(reason='Mua sắm giả '+stamp).first();check(request is not None and request.items.count()==2,'procurement dynamic rows saved');check(page.locator('.ui-alert--success').count()>0,'procurement success notice')
  login('demo-director');page.goto(base+reverse('portal:procurement_request_list'));form=page.locator('form[action="'+reverse('portal:procurement_request_approve',args=[request.pk])+'"]:has([value=Approved])');submit(form.locator('button'));request.refresh_from_db();check(request.status=='Approved','procurement approval saved');form=page.locator('form[action="'+reverse('portal:procurement_request_mark_purchased',args=[request.pk])+'"]');submit(form.locator('button'));request.refresh_from_db();check(request.status=='Purchased','procurement purchase saved');login('demo-hr')
  # Existing dispatch with long text, progress/history and status visible after POST.
  dispatch=OfficialDispatch.objects.filter(dispatch_no='ADMIN-UAT-001').first();page.goto(base+reverse('portal:dispatch_detail',args=[dispatch.pk]));form=page.locator('form:has([name=comment])');form.locator('[name=comment]').fill('Tiến độ giả '+stamp);form.locator('[name=new_status]').select_option('Processing');submit(form.locator('button[type=submit]'));dispatch.refresh_from_db();check(dispatch.status=='Processing' and DispatchTracking.objects.filter(dispatch=dispatch,comment='Tiến độ giả '+stamp).exists(),'dispatch status and history saved');check(page.locator('.ui-alert--success').count()>0,'dispatch update notice')
  # Create disposal, add asset, director approval, then HR minutes through changed templates.
  kind=AssetType.objects.create(asset_type_code='FLOW-'+stamp,asset_type_name='Thiết bị giả');asset=Asset.objects.create(asset_type=kind,asset_code='FLOW-'+stamp,asset_name='Tài sản giả '+stamp,purchase_value=1000000)
  page.goto(base+reverse('portal:disposal_request_create'));form=page.locator('main form:has([name=request_no])');form.locator('[name=request_no]').fill('FLOW-'+stamp);form.locator('[name=request_date]').fill(timezone.localdate().isoformat());form.locator('[name=location_name]').fill('Văn phòng giả');submit(form.locator('button[type=submit]'));disposal=AssetDisposalRequest.objects.filter(request_no='FLOW-'+stamp).first();check(disposal is not None,'disposal created');form=page.locator('form:has([name=action][value=add_item])');form.locator('[name=asset]').select_option(str(asset.pk));form.locator('[name=damage_description]').fill('Hỏng giả');submit(form.locator('button'));check(AssetDisposalItem.objects.filter(request=disposal,asset=asset).exists(),'disposal asset persisted')
  login('demo-director');page.goto(base+reverse('portal:disposal_request_detail',args=[disposal.pk]));form=page.locator('form:has([name=action][value=approve])');form.locator('button').click();check(page.locator('#ui-confirm-dialog').is_visible(),'disposal approval confirmation');page.keyboard.press('Escape');disposal.refresh_from_db();check(disposal.status=='Pending','disposal Escape does not approve');submit(form.locator('button'));disposal.refresh_from_db();check(disposal.status=='Approved','director approval persisted')
  login('demo-hr');page.goto(base+reverse('portal:disposal_request_detail',args=[disposal.pk]));item=AssetDisposalItem.objects.get(request=disposal,asset=asset);details=page.locator('details').first;details.locator('summary').click();form=page.locator('form[action="'+reverse('portal:disposal_minutes_create',args=[item.pk])+'"]');form.locator('[name=decision_date]').fill(timezone.localdate().isoformat());form.locator('[name=conclusion]').fill('Kết luận giả '+stamp);submit(form.locator('button'));asset.refresh_from_db();check(AssetDisposalMinutes.objects.filter(item=item).exists() and asset.status=='Disposed','minutes saved and asset disposed');check(page.locator('.ui-alert--success').count()>0,'minutes success notice')
  # Count a fresh synthetic asset and complete a dedicated inventory session.
  inventory_asset=Asset.objects.create(asset_type=kind,asset_code='COUNT-'+stamp,asset_name='Tài sản kiểm kê giả')
  session=InventorySession.objects.create(session_name='COUNT-'+stamp,office_name='Văn phòng giả',inventory_datetime=timezone.now());line=InventoryLine.objects.create(session=session,asset=inventory_asset)
  page.goto(base+reverse('portal:inventory_session_detail',args=[session.pk]));form=page.locator('form[action="'+reverse('portal:inventory_line_update',args=[line.pk])+'"]');form.locator('[name=actual_condition]').select_option('Normal');form.locator('[name=note]').fill('Đã kiểm giả');submit(form.locator('button'));line.refresh_from_db();check(line.is_counted and line.note=='Đã kiểm giả','inventory line persisted');form=page.locator('form[action="'+reverse('portal:inventory_session_complete',args=[session.pk])+'"]');form.locator('[name=recommendation]').fill('Kiến nghị giả');submit(form.locator('button'));session.refresh_from_db();check(session.status=='Completed' and session.recommendation=='Kiến nghị giả','inventory completion saved');check(page.url.endswith(reverse('portal:inventory_session_print',args=[session.pk])),'inventory completion print destination')
  # The create screen must still submit the original dispatch fields.
  page.goto(base+reverse('portal:dispatch_create'));form=page.locator('main form:has([name=dispatch_no])');form.locator('[name=dispatch_type]').select_option('Incoming');form.locator('[name=dispatch_no]').fill('FLOW-'+stamp);form.locator('[name=title]').fill('Công văn mới giả '+stamp);form.locator('[name=issuing_organization]').fill('Tổ chức giả');form.locator('[name=issue_date]').fill(timezone.localdate().isoformat());form.locator('[name=received_or_sent_date]').fill(timezone.localdate().isoformat());submit(form.locator('button[type=submit]'));check(OfficialDispatch.objects.filter(dispatch_no='FLOW-'+stamp).exists(),'dispatch create persisted');check(page.locator('.ui-alert--success').count()>0,'dispatch create success notice')
  page.screenshot(path=str(out/'dispatch-created.png'),full_page=True);page.goto(base+'/portal/');check(page.locator('main').is_visible(),'dashboard accessible after administration flows');browser.close()
 (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'checks':len(report['checks']),'failures':report['failures'],'limits':report.get('existing_limits',[])},ensure_ascii=False));return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
