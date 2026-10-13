"""Submit, approve and reject fresh synthetic decisions through real Edge UI."""
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
    from playwright.sync_api import sync_playwright
    hr = User.objects.get(username='demo-hr')
    drafts = [PersonnelDecision.objects.create(employee=hr.employee, template_slug='salary-decision',
        decision_no='LAYOUT-' + uuid.uuid4().hex[:12], decision_date=timezone.localdate(), status='Draft',
        created_by=hr, content_snapshot={'synthetic_only':True}) for _ in range(2)]
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
                if transition != 'submit':
                    form.locator('[name=comment]').fill('Synthetic layout UAT ' + action)
                form.locator('button').click()
                page.get_by_role('dialog').wait_for(state='visible')
                # Exercise cancelling the confirmation before the actual POST.
                page.keyboard.press('Escape')
                check(not page.get_by_role('dialog').is_visible(), account + ' Escape cancels confirmation')
                form.locator('button').focus(); page.keyboard.press('Enter')
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
        browser.close()
    (output / 'browser-result.json').write_text(json.dumps({'synthetic_only':True,'checks':checks,'passed':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(checks),'screenshots':4,'synthetic_only':True}))


if __name__ == '__main__':
    main()
