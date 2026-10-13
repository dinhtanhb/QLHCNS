"""Render every HCNS form and shared print screens using synthetic Edge sessions."""
import argparse
import json
import os
import uuid
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--probe-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('Synthetic runtime must be outside the repository.')
    marker = json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    sys.path.insert(0, str(root / 'src'))
    sys.path.insert(0, str(args.packages_dir.resolve()))
    os.environ.update(APP_ENV='test', DB_ENGINE='django.db.backends.sqlite3', DJANGO_SETTINGS_MODULE='config.settings', SECRET_KEY=marker['secret_key'], M365_STORAGE_ENABLED='False')
    import config.settings as cfg
    cfg.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3', 'NAME':str(folder/'synthetic.sqlite3')}}
    cfg.MEDIA_ROOT = folder/'media'
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = str(folder/('print-uat-' + Path(handler['filename']).name))
    import django
    django.setup()
    from django.utils import timezone
    from apps.security.models import User
    from apps.asset.models import AssetType, Asset, InventorySession, InventoryLine, AssetDisposalRequest, AssetDisposalItem, AssetDisposalMinutes
    employee = User.objects.get(username='demo-hr').employee
    stamp = 'PRINT-' + uuid.uuid4().hex[:12]
    kind = AssetType.objects.create(asset_type_code=stamp, asset_type_name='Synthetic print equipment')
    asset = Asset.objects.create(asset_type=kind, asset_code=stamp, asset_name='Synthetic equipment with a long descriptive name for wrapping', purchase_value=5000000, location='Synthetic office')
    session = InventorySession.objects.create(session_name=stamp, office_name='Synthetic office', inventory_datetime=timezone.now())
    InventoryLine.objects.create(session=session, asset=asset)
    disposal = AssetDisposalRequest.objects.create(request_no=stamp, request_date=timezone.localdate(), location_name='Synthetic office', requested_by=employee)
    item = AssetDisposalItem.objects.create(request=disposal, asset=asset, damage_description='Synthetic print test damage description')
    minutes = AssetDisposalMinutes.objects.create(item=item, decision_date=timezone.localdate(), conclusion='Synthetic conclusion', original_value=5000000, manufacture_year=2020)
    from apps.document.hcns.catalog import FORMS
    from playwright.sync_api import sync_playwright
    password = next(line.split(': ', 1)[1] for line in (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    output = folder / ('print-probe' if args.probe_only else 'print-layout-uat')
    output.mkdir(exist_ok=True)
    routes = {'timesheet': '/portal/timesheet/?month=10&year=2026',
        'report-timesheet': '/portal/reports/timesheet/',
        'report-headcount': '/portal/reports/headcount/',
        'report-budget': '/portal/reports/budget/',
        'report-personnel': '/portal/reports/personnel-changes/',
        'dispatches': '/portal/dispatches/'}
    routes.update({slug: '/portal/hcns-forms/' + slug + '/' for slug in FORMS})
    routes.update({'legacy-inventory':f'/portal/inventory/{session.pk}/print/',
        'legacy-disposal-request':f'/portal/disposal/{disposal.pk}/print/',
        'legacy-disposal-decision':f'/portal/disposal/{disposal.pk}/decision-print/',
        'legacy-disposal-execution':f'/portal/disposal/{disposal.pk}/execution-print/',
        'legacy-disposal-minutes':f'/portal/disposal/minutes/{minutes.pk}/print/'})
    report = {'checks': [], 'failures': [], 'documents': {}, 'synthetic_only': True}
    base = f'http://127.0.0.1:{args.port}'

    def check(ok, label):
        report['checks' if ok else 'failures'].append(label)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width':794,'height':1123}, locale='vi-VN', service_workers='block')
        page = context.new_page()
        def login(account):
            context.clear_cookies()
            page.goto(base + '/portal/login/')
            page.locator('[name=username]').fill(account)
            page.locator('[name=password]').fill(password)
            page.locator('main form button[type=submit]').click()
            page.wait_for_load_state('networkidle')
        login('demo-hr')
        account = 'demo-hr'
        for index, (name, route) in enumerate(routes.items()):
            needed = 'demo-finance' if name == 'salary-scale' else 'demo-hr'
            if needed != account:
                login(needed)
                account = needed
            response = page.goto(base + route, wait_until='networkidle')
            check(response.status == 200, name + ' opens')
            # Use the actual shared success-alert markup to catch the reported giant icon.
            page.evaluate('''()=>{
                const alert=document.createElement('div');alert.className='ui-alert ui-alert--success';
                alert.innerHTML='<svg class="ui-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg><span>PRINT_UAT_FLASH_MUST_NOT_APPEAR</span>';
                document.querySelector('main').prepend(alert);
            }''')
            page.emulate_media(media='print')
            if args.probe_only:
                # Baseline: disable only the new paper stylesheet, keeping current templates.
                page.evaluate('''()=>[...document.querySelectorAll('link[href*="print_forms.css"]')].forEach(x=>x.disabled=true)''')
            for theme in ('light', 'dark'):
                page.evaluate('(t)=>document.documentElement.dataset.theme=t', theme)
                check(not page.locator('.ui-alert').first.is_visible(), name + ' ' + theme + ' flash excluded')
                check(not page.locator('.ui-topbar').is_visible(), name + ' ' + theme + ' shell excluded')
                check(page.locator('main svg.ui-icon').evaluate_all('xs=>xs.every(x=>!x.checkVisibility())'), name + ' ' + theme + ' control icons excluded')
            if name in FORMS:
                paper = page.locator('.hcns-paper')
                check(paper.count() == 1, name + ' paper present')
                check(not page.locator('.hcns-editor').is_visible(), name + ' editor excluded')
                check(paper.evaluate('x=>getComputedStyle(x).fontFamily.includes("Times New Roman")'), name + ' paper typeface retained')
                check(paper.locator('input,select,textarea,button').count() == 0, name + ' paper has no app controls')
            if name == 'timesheet':
                table = page.locator('.ui-personal-timesheet-table')
                check(table.evaluate('x=>getComputedStyle(x).borderCollapse==="collapse" && x.getBoundingClientRect().width > document.querySelector("main").getBoundingClientRect().width*.95'), 'timesheet full-width paper table')
                check(table.evaluate('x=>{const a=x.getBoundingClientRect(),b=document.querySelector("main").getBoundingClientRect();return a.left>=b.left-1&&a.right<=b.right+1}'), 'timesheet borders stay inside paper margins')
                check(table.locator('tbody tr').count() >= 34, 'timesheet all days and totals retained')
                check(page.locator('.timesheet-summary-layout').evaluate('x=>getComputedStyle(x).display==="grid"'), 'timesheet summary and signatures in columns')
                check(page.locator('.timesheet-leave-row input,.timesheet-leave-row .ui-number-display').evaluate_all('xs=>xs.every(x=>!x.checkVisibility())'), 'timesheet controls excluded')
                check(page.locator('.timesheet-leave-row .ui-print-only').evaluate_all('xs=>xs.length===5&&xs.every(x=>x.checkVisibility())'), 'timesheet saved leave values visible')
            if name.startswith('legacy-'):
                check('None' not in page.locator('main').inner_text(), name + ' missing values stay blank')
            if name == 'legacy-inventory':
                check(page.locator('.ui-print-landscape').evaluate('x=>getComputedStyle(x).page==="inventory-landscape"'), 'inventory uses landscape paper')
            if not args.probe_only:
                path = output / (name + '.pdf')
                page.pdf(path=str(path), prefer_css_page_size=True, print_background=True, display_header_footer=False)
                report['documents'][name] = str(path)
            page.emulate_media(media='screen')
        browser.close()
    report['passed'] = not report['failures']
    (output / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']), 'pdfs':len(report['documents']), 'failures':report['failures']}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
