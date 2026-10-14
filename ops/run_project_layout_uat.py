"""Audit screen layouts in Edge against an explicitly marked disposable demo."""
import argparse
import json
import os
from pathlib import Path
import sys
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--only', nargs='*', help='Optional focused URL paths before the full audit.')
    parser.add_argument('--account', choices=('demo-layout-admin', 'demo-hr'), default='demo-layout-admin')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('Synthetic runtime must be outside source.')
    marker = json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    os.environ.update(APP_ENV='test', DB_ENGINE='django.db.backends.sqlite3',
        DJANGO_SETTINGS_MODULE='config.settings', SECRET_KEY=marker['secret_key'],
        M365_STORAGE_ENABLED='False', DJANGO_ALLOW_ASYNC_UNSAFE='true')
    sys.path.insert(0, str(root / 'src'))
    sys.path.insert(0, str(args.packages_dir.resolve()))
    import config.settings as cfg
    cfg.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(folder / 'synthetic.sqlite3')}}
    cfg.MEDIA_ROOT = folder / 'media'
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = str(folder / ('project-uat-' + Path(handler['filename']).name))
    import django
    django.setup()
    from apps.security.models import User
    from apps.asset.models import InventorySession
    from apps.office.models import MeetingRoom, Vehicle, RoomBooking, VehicleBooking, SupplyItem, SupplyRequest, SupplyRequestItem
    from django.utils import timezone
    from datetime import timedelta
    from apps.portal.urls import urlpatterns
    from django.urls import reverse
    from playwright.sync_api import sync_playwright
    password = next(line.split(': ', 1)[1] for line in (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    admin, _ = User.objects.get_or_create(username='demo-layout-admin')
    admin.is_staff = admin.is_superuser = admin.is_active = True
    if not admin.check_password(password):
        admin.set_password(password)
    admin.save()
    # Parameterized pages and POST endpoints have separate business-flow suites.
    excluded = {'login', 'logout', 'service_worker', 'notification_mark_all_read',
        'timesheet_entry_create', 'timesheet_summary_update', 'inventory_session_create'}
    routes = [reverse('portal:' + p.name) for p in urlpatterns
        if p.name not in excluded and '<' not in str(p.pattern)]
    routes += ['/admin/', '/admin/hrm/employee/']
    if args.only:
        routes = args.only
    output = folder / 'project-layout-uat'
    output.mkdir(exist_ok=True)
    report = {'synthetic_only': True, 'checks': [], 'problems': [], 'excluded': sorted(excluded), 'pages': {}}
    base = f'http://127.0.0.1:{args.port}'

    def check(ok, label):
        report['checks' if ok else 'problems'].append(label)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(service_workers='block', reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda err: report['problems'].append('JavaScript: ' + str(err)))
        page.goto(base + '/portal/login/')
        page.locator('[name=username]').fill(args.account)
        page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click()
        page.wait_for_load_state('networkidle')
        for route in routes:
            try:
                response = page.goto(base + route, wait_until='networkidle')
            except Exception as error:
                if not any(message in str(error) for message in ('ERR_HTTP_RESPONSE_CODE_FAILURE', 'chrome-error://chromewebdata/')):
                    raise
                response = page.request.get(base + route)
                if response.status == 200:
                    response = page.goto(base + route, wait_until='networkidle')
            report['pages'][route] = response.status
            check(response.status in (200, 403, 405), route + ' response ' + str(response.status))
            if response.status != 200:
                continue
            for width in (1920, 1440, 1024, 768, 390):
                page.set_viewport_size({'width': width, 'height': 1000})
                for theme in ('light', 'dark'):
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t', theme)
                    page.wait_for_timeout(50)
                    label = f'{route} {width} {theme}'
                    fits = page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    check(fits, label + ' page fits')
                    if not fits and theme == 'light':
                        report.setdefault('overflow', {})[label] = page.evaluate('''()=>[...document.querySelectorAll('body *')].filter(x=>{
                            const r=x.getBoundingClientRect();return r.width&&r.right>innerWidth+1 && getComputedStyle(x).position!=='fixed';
                        }).slice(0,12).map(x=>({tag:x.tagName,classes:x.className,width:x.getBoundingClientRect().width,right:x.getBoundingClientRect().right}))''')
                    geometry = page.locator('.ui-query-bar').evaluate_all('''forms=>forms.map(f=>{
                        const button=f.querySelector('.ui-query-actions button');
                        const a=button.getBoundingClientRect();
                        const fields=[...f.querySelectorAll('.ui-field input,.ui-field select')].filter(x=>x.type!=='hidden');
                        const b=fields.at(-1).getBoundingClientRect();
                        const sameRow=Math.abs(a.bottom-b.bottom)<=1;
                        const gap=a.left-b.right;
                        const links=[...f.querySelectorAll('.ui-query-actions a')];
                        return {gap,baseline:Math.abs(a.bottom-b.bottom),height:a.height,
                            close:!sameRow || gap>=0&&gap<=17,
                            fit:a.right<=innerWidth+1,stack:innerWidth>=1024||a.top>=b.bottom,
                            labels:fields.every(x=>!!f.querySelector('label[for="'+x.id+'"]')),
                            mobile:innerWidth>=600||links.every(x=>Math.abs(x.getBoundingClientRect().top-a.top)<1),
                            font:parseFloat(getComputedStyle(button).fontSize)>=14};
                    })''')
                    for row in geometry:
                        report.setdefault('filter_geometry', {})[label]=row
                        check(row['close'] and row['fit'] and row['stack'] and row['mobile'] and row['labels'] and row['font'] and row['height']>=44, label + ' inline filter controls')
                    if args.only and page.locator('.ui-administration,.ui-planning').count():
                        check(page.locator('main h1:visible').count()==1,label+' single visible page title')
                        check(page.locator('.ui-administration > .ui-print-only:visible').count()==0,label+' print register hidden on screen')
                        controls=page.locator('main input:not([type=hidden]):not(.ui-number-source),main select,main textarea,main button').evaluate_all('''xs=>xs.filter(x=>x.checkVisibility()).map(x=>({height:x.getBoundingClientRect().height,font:parseFloat(getComputedStyle(x).fontSize),label:x.tagName!=='BUTTON'?!!document.querySelector('label[for="'+x.id+'"]'):true}))''')
                        check(all(x['height']>=43.5 and x['font']>=14 and x['label'] for x in controls),label+' controls, labels and type size')
                        if page.locator('.ui-planning-kpi').count():
                            table=page.locator('.ui-planning-kpi')
                            check(table.evaluate('x=>getComputedStyle(x).tableLayout==="auto"'),label+' KPI automatic column sizing')
                            check(table.locator('input:not(.ui-number-source):visible').evaluate_all('xs=>xs.every(x=>x.getBoundingClientRect().width>=110)'),label+' KPI input readable width')
                            if width>=1440:
                                check(table.evaluate('x=>x.getBoundingClientRect().width<=x.parentElement.clientWidth+1'),label+' KPI actions fit wide table')
                        if width in (1440,390):page.screenshot(path=str(output/(route.strip('/').replace('/','-')+f'-{width}-{theme}.png')),full_page=True)
                    if width == 1440:
                        grids = page.locator('.ui-planning-grid,.ui-layout-split,.ui-detail-grid,.ui-detail-sections,.ui-finance-grid,.ui-recruitment-grid,.ui-report-export-grid,.report-visuals,.report-section-grid,.timesheet-summary-layout,.ui-form-grid:not(.ui-form-grid--three)').evaluate_all('''xs=>xs.filter(x=>x.getBoundingClientRect().width && !x.closest('.hcns-paper,.hcns-editor')).map(x=>getComputedStyle(x).gridTemplateColumns.split(' ').map(parseFloat))''')
                        for cols in grids:
                            if len(cols) == 2:
                                check(abs(cols[0]/sum(cols)-.6)<.003, label + ' split 60/40')
            if args.only or route in ('/portal/timesheet/', '/portal/inventory/', '/portal/hr-decisions/', '/portal/reports/', '/portal/hr/contracts/'):
                page.set_viewport_size({'width':1440,'height':1000})
                page.screenshot(path=str(output / (route.strip('/').replace('/', '-') + '.png')), full_page=True)
            # Exercise the actual GET with keyboard, preserving all field values.
            for index in range(page.locator('.ui-query-bar').count()):
                form = page.locator('.ui-query-bar').nth(index)
                names = form.locator('[name]').evaluate_all('xs=>xs.map(x=>({name:x.name,value:x.value}))')
                submit = form.locator('button[type=submit]')
                if submit.count():
                    submit.first.focus()
                    with page.expect_navigation(wait_until='domcontentloaded'):
                        page.keyboard.press('Enter')
                    from urllib.parse import parse_qs, urlparse
                    query = parse_qs(urlparse(page.url).query, keep_blank_values=True)
                    check(all(query.get(n['name'], [None])[0] == n['value'] for n in names), route + ' keyboard GET values preserved')
        page.goto(base + '/portal/inventory/')
        name = 'SYNTHETIC-LAYOUT-' + uuid.uuid4().hex[:10]
        page.locator('[name=session_name]').fill(name)
        page.locator('[name=office_name]').fill('Synthetic office with a long label for responsive testing')
        page.locator('[name=inventory_datetime]').fill('2026-10-13T10:00')
        page.locator('form.ui-inline-create button').click()
        page.wait_for_load_state('networkidle')
        check(InventorySession.objects.filter(session_name=name).count() == 1, 'inventory POST saved exactly once')
        check(name in page.locator('main').inner_text(), 'inventory saved record visible at destination')
        check('csrf' not in page.locator('main').inner_text().lower(), 'inventory CSRF accepted')
        # Fresh records only; cover both transitions and supply issue from new screens.
        employee = User.objects.get(username='demo-hr').employee
        stamp = uuid.uuid4().hex[:12]
        room = MeetingRoom.objects.create(room_code='LAYOUT-' + stamp, room_name='Synthetic meeting room with a long descriptive name')
        vehicle = Vehicle.objects.create(vehicle_code='LAYOUT-' + stamp, vehicle_name='Synthetic vehicle', plate_number='FAKE-' + stamp[:8])
        item = SupplyItem.objects.create(item_code='LAYOUT-' + stamp, item_name='Synthetic office item', quantity_in_stock=10)
        start = timezone.now() + timedelta(days=30)
        for action in ('Approved', 'Rejected'):
            bookings = [
                (RoomBooking.objects.create(room=room, employee=employee, start_time=start, end_time=start + timedelta(hours=1), purpose='Synthetic office UAT'), 'room_booking_approval_list', 'room_booking_approve'),
                (VehicleBooking.objects.create(vehicle=vehicle, employee=employee, start_time=start, end_time=start + timedelta(hours=1), destination='Synthetic destination', purpose='Synthetic office UAT'), 'vehicle_booking_approval_list', 'vehicle_booking_approve'),
            ]
            supply = SupplyRequest.objects.create(request_no='LAYOUT-' + stamp + action, employee=employee, request_date=timezone.localdate())
            SupplyRequestItem.objects.create(supply_request=supply, item=item, quantity_requested=3)
            bookings.append((supply, 'supply_request_approval_list', 'supply_request_approve'))
            for record, list_name, action_name in bookings:
                page.goto(base + reverse('portal:' + list_name))
                form = page.locator('form[action="' + reverse('portal:' + action_name, args=[record.pk]) + '"]')
                form.locator('button[value="' + action + '"]').click()
                if page.locator('#ui-confirm-dialog').is_visible():
                    page.keyboard.press('Escape')
                    record.refresh_from_db()
                    check(record.status == 'Pending', list_name+' confirmation Escape does not write')
                    form.locator('button[value="' + action + '"]').click()
                    page.locator('[data-ui-confirm-accept]').click()
                page.wait_for_load_state('networkidle')
                record.refresh_from_db()
                check(record.status == action, list_name + ' UI saved ' + action)
                check(page.url.endswith(reverse('portal:' + list_name)), list_name + ' correct destination')
                check(page.locator('.ui-alert--success').count() > 0, list_name + ' success message')
            if action == 'Approved':
                page.locator('form[action="' + reverse('portal:supply_request_issue', args=[supply.pk]) + '"] button').click()
                page.wait_for_load_state('networkidle')
                supply.refresh_from_db(); item.refresh_from_db()
                check(supply.status == 'Issued' and item.quantity_in_stock == 7, 'supply issue saved and stock decremented once')
            start += timedelta(days=1)
        browser.close()
    report['passed'] = not report['problems']
    (output / 'browser-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']), 'pages':len(report['pages']), 'problems':report['problems']},ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
