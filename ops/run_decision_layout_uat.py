"""Exercise grouped decision actions and their persisted outcomes in real Edge."""
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
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('Demo must be outside source.')
    marker = json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    os.environ.update(APP_ENV='test', DB_ENGINE='django.db.backends.sqlite3', DJANGO_SETTINGS_MODULE='config.settings',
        SECRET_KEY=marker['secret_key'], M365_STORAGE_ENABLED='False', DJANGO_ALLOW_ASYNC_UNSAFE='true')
    sys.path.insert(0, str(root / 'src'))
    sys.path.insert(0, str(args.packages_dir.resolve()))
    import config.settings as cfg
    cfg.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(folder / 'synthetic.sqlite3')}}
    cfg.MEDIA_ROOT = folder / 'media'
    cfg.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = str(folder / ('decision-uat-' + Path(handler['filename']).name))
    import django
    django.setup()
    from django.utils import timezone
    from apps.security.models import User
    from apps.document.models import PersonnelDecision, PersonnelDecisionHistory
    from apps.document.hcns.catalog import FORMS
    from apps.document.hcns.forms import initial_document_data
    from apps.document.hcns.rendering import document_context
    from apps.document.hcns.views import _json_safe
    from playwright.sync_api import sync_playwright
    hr = User.objects.get(username='demo-hr')
    spec=FORMS['salary-decision']
    values,tables=initial_document_data(spec,{}, {},user=hr)
    values['full_name']='Nhân viên giả lập có họ tên dài để kiểm tra bản xem trước và bố cục các thao tác'
    rendered=_json_safe(document_context(spec,values,tables,'Synthetic layout fixture'))
    drafts = [PersonnelDecision.objects.create(employee=hr.employee, template_slug='salary-decision',
        decision_no='LAYOUT-' + uuid.uuid4().hex[:12], decision_date=timezone.localdate(), status='Draft',
        created_by=hr, content_snapshot={'synthetic_only':True,'rendered':rendered}) for _ in range(3)]
    password = next(line.split(': ', 1)[1] for line in (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    output = folder / 'decision-layout-uat'
    output.mkdir(exist_ok=True)
    checks = []
    base = f'http://127.0.0.1:{args.port}'

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        for index, action in enumerate(('approve', 'reject')):
            decision = drafts[index]
            for account in ('demo-hr', 'demo-director'):
                context = browser.new_context(service_workers='block')
                page = context.new_page()
                page.goto(base + '/portal/login/')
                page.locator('[name=username]').fill(account)
                page.locator('[name=password]').fill(password)
                with page.expect_navigation(wait_until='networkidle'):
                    page.locator('main form button[type=submit]').click()
                url = base + f'/portal/hr-decisions/{decision.pk}/'
                response = page.goto(url, wait_until='networkidle')
                check(response.status == 200, account + ' decision opens')
                transition = 'submit' if account == 'demo-hr' else action
                form = page.locator(f'form[action$="/{transition}/"]')
                for width in (1920,1440,1024,768,390):
                    page.set_viewport_size({'width':width,'height':1000})
                    for theme in ('light','dark'):
                        page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{account} {action} {width} {theme} fits')
                        check(page.locator('.ui-workflow').count()==1,account+' one workflow panel')
                        if width in (1440,390):
                            page.screenshot(path=str(output/f'{account}-{action}-{width}-{theme}.png'))
                if index==0 and account=='demo-hr':
                    page.emulate_media(media='print')
                    check(not page.locator('.ui-workflow').is_visible(),'workflow excluded from printed decision')
                    check(page.locator('.hcns-paper').is_visible(),'decision paper retained')
                    page.pdf(path=str(output/'decision-preview.pdf'),prefer_css_page_size=True,print_background=True)
                    page.emulate_media(media='screen')
                if account=='demo-hr':
                    disclosure=page.locator('.ui-workflow-secondary')
                    check(not disclosure.evaluate('x=>x.open'), 'cancel initially collapsed')
                    disclosure.locator('summary').focus();page.keyboard.press('Enter')
                    disclosure.locator('[name=comment]').fill('Synthetic cancellation draft')
                    disclosure.locator('[data-ui-disclosure-close]').click()
                    check(disclosure.locator('summary').evaluate('x=>x===document.activeElement'),'close restores disclosure focus')
                    check(disclosure.locator('[name=comment]').input_value()=='Synthetic cancellation draft','close keeps draft input')
                if transition=='reject':
                    form.locator('xpath=..').locator('summary').click()
                    form.locator('button[type=submit]').click()
                    check(form.locator('[data-ui-errors]').is_visible(),'reject requires reason inline')
                    check(not page.get_by_role('dialog').is_visible(),'invalid form does not confirm')
                if transition != 'submit':
                    form.locator('[name=comment]').fill('Synthetic layout UAT ' + action)
                form.locator('button[type=submit]').click()
                page.get_by_role('dialog').wait_for(state='visible')
                # Exercise cancelling the confirmation before the actual POST.
                page.keyboard.press('Escape')
                check(not page.get_by_role('dialog').is_visible(), account + ' Escape cancels confirmation')
                form.locator('button[type=submit]').focus(); page.keyboard.press('Enter')
                page.get_by_role('dialog').wait_for(state='visible')
                with page.expect_navigation(wait_until='networkidle'):
                    page.locator('[data-ui-confirm-accept]').click()
                check(page.url == url, account + ' destination retained')
                decision.refresh_from_db()
                expected = 'PendingApproval' if transition == 'submit' else 'Approved' if action == 'approve' else 'Rejected'
                check(decision.status == expected, account + ' saved state ' + expected)
                check('Đã cập nhật trạng thái' in page.locator('main').inner_text(), account + ' success message')
                check(PersonnelDecisionHistory.objects.filter(decision=decision, action='Submitted' if transition=='submit' else 'Approved' if action=='approve' else 'Rejected').count() == 1, account + ' single event saved')
                response = page.goto(base + '/portal/', wait_until='networkidle')
                check(response.status == 200 and decision.decision_no in page.locator('#phase2-history').inner_text(), account + ' dashboard history updated')
                page.locator('#phase2-history').screenshot(path=str(output / f'{action}-{account}.png'))
                context.close()
        # Issue the approved decision and cancel a separate draft through the UI.
        context=browser.new_context(service_workers='block');page=context.new_page()
        page.goto(base+'/portal/login/')
        page.locator('[name=username]').fill('demo-hr');page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
        for decision,action in ((drafts[0],'issue'),(drafts[2],'cancel')):
            url=base+f'/portal/hr-decisions/{decision.pk}/'
            page.goto(url,wait_until='networkidle')
            form=page.locator(f'form[action$="/{action}/"]')
            if action=='cancel':form.locator('xpath=..').locator('summary').click()
            form.locator('[name=comment]').fill('Synthetic '+action+' preserved input')
            if action=='issue':
                # An invalid PDF must preserve the comment through the server redirect.
                form.locator('[name=issued_file]').set_input_files({'name':'synthetic.pdf','mimeType':'application/pdf','buffer':b'not a PDF'})
                form.locator('button[type=submit]').click()
                with page.expect_navigation(wait_until='networkidle'):page.locator('[data-ui-confirm-accept]').click()
                decision.refresh_from_db()
                check(decision.status=='Approved','invalid signed PDF does not issue')
                check(form.locator('[name=comment]').input_value()=='Synthetic issue preserved input','server validation retains comment')
                check(form.locator('.ui-field-error[role=alert]').is_visible(),'server validation shown within workflow')
                form.locator('[name=issued_file]').set_input_files({'name':'synthetic.pdf','mimeType':'application/pdf','buffer':b'%PDF-1.4\nsynthetic signed copy'})
            form.locator('button[type=submit]').click()
            with page.expect_navigation(wait_until='networkidle'):page.locator('[data-ui-confirm-accept]').click()
            decision.refresh_from_db()
            check(decision.status==('Issued' if action=='issue' else 'Cancelled'),action+' state persisted')
            check('Đã cập nhật trạng thái' in page.locator('main').inner_text(),action+' success message')
            check(page.locator('.ui-workflow').count()==0,action+' completed workflow hidden')
            if action=='issue':check(page.get_by_role('link',name='Tải PDF đã ký').count()==1,'signed PDF available')
            page.screenshot(path=str(output/f'{action}-final.png'),full_page=True)
            page.goto(base+'/portal/',wait_until='networkidle')
            check(decision.decision_no in page.locator('#phase2-history').inner_text(),action+' dashboard history refreshed')
        context.close()
        browser.close()
    (output / 'browser-result.json').write_text(json.dumps({'synthetic_only':True,'checks':checks,'passed':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(checks),'screenshots':len(list(output.glob('*.png'))),'synthetic_only':True}))


if __name__ == '__main__':
    main()
