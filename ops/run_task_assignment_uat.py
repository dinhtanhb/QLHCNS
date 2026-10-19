"""Synthetic-only task assignment browser flows and before/after visual evidence."""
import argparse
import json
from pathlib import Path
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

from run_layout_alignment_audit import configure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8836)
    parser.add_argument('--baseline-port', type=int, default=8837)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('External synthetic runtime required')
    configure(root, folder)
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
    from apps.task.models import Task
    # Playwright's sync loop is an async context: perform ORM checks in a worker.
    workers = ThreadPoolExecutor(max_workers=1)
    orm = lambda fn: workers.submit(fn).result()
    password = next(line.split(': ', 1)[1] for line in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    out = folder/'task-assignment-uat'
    out.mkdir(exist_ok=True)
    report = {'synthetic_only': True, 'checks': [], 'failures': [], 'screenshots': []}

    def check(ok, label):
        report['checks' if ok else 'failures'].append(label)

    def login(page, base):
        page.goto(base+'/portal/login/')
        page.locator('[name=username]').fill('demo-hr')
        page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click()
        page.wait_for_load_state('networkidle')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        base = f'http://127.0.0.1:{args.port}'
        context = browser.new_context(service_workers='block', viewport={'width':1756,'height':1050}, locale='vi-VN')
        page = context.new_page()
        login(page, base)
        code = next(iter(ACTIVITY_CODE_NAMES))
        stamp = 'TASK-UAT-'+uuid.uuid4().hex[:10]
        before = orm(lambda: Task.objects.filter(act_code=code).count())
        saved_codes = []
        for iteration in range(3):
            page.goto(base+'/portal/tasks/create/', wait_until='networkidle')
            search = page.locator('[data-ui-choice-source="task_create-act_code"]')
            native = page.locator('[name=act_code]')
            search.fill(code)
            check(native.input_value() == '', 'typing alone leaves empty value '+str(iteration))
            search.press('ArrowDown'); search.press('Enter')
            name = page.locator('[name=task_name]')
            check(name.input_value() == ACTIVITY_CODE_NAMES[code] and name.get_attribute('readonly') is not None, 'catalog title read-only '+str(iteration))
            page.locator('[name=description]').fill(stamp+'-'+str(iteration))
            page.locator('main form button[type=submit]').click()
            page.wait_for_load_state('networkidle')
            check('/portal/tasks/' in page.url and '/create/' not in page.url, 'task target '+str(iteration))
            check(page.locator('.ui-alert--success').count() == 1, 'success '+str(iteration))
            task = orm(lambda: Task.objects.get(description=stamp+'-'+str(iteration)))
            saved_codes.append(task.task_code)
            check(task.task_name == ACTIVITY_CODE_NAMES[code], 'stored canonical title '+str(iteration))
            check(task.task_code in page.locator('.ui-alert--success').inner_text(), 'success contains internal code '+str(iteration))
            page.goto(base+'/portal/tasks/?scope=assigned_by_me', wait_until='networkidle')
            check('ActCode '+code in page.locator('main').inner_text(), 'list ActCode '+str(iteration))
            page.goto(base+f'/portal/tasks/{task.pk}/', wait_until='networkidle')
            check('ActCode '+code in page.locator('main').inner_text(), 'detail ActCode '+str(iteration))
        check(len(set(saved_codes)) == 3 and orm(lambda: Task.objects.filter(act_code=code).count()) == before+3, 'same catalog three distinct internal codes')
        page.goto(base+'/portal/tasks/create/', wait_until='networkidle')
        search = page.locator('[data-ui-choice-source="task_create-act_code"]')
        search.fill('hanh chinh'); search.press('ArrowDown'); search.press('Enter')
        name = page.locator('[name=task_name]')
        check(name.get_attribute('readonly') is None and name.get_attribute('required') is not None, 'Other editable required title')
        page.locator('[name=description]').fill(stamp+'-other')
        name.fill('Administrative '+stamp)
        # Force one server error, then check every important bound value.
        page.locator('[name=priority]').evaluate('(x)=>{const o=new Option("Invalid","INVALID");x.add(o);x.value="INVALID";}')
        assignee = page.locator('[name=assigned_to_employee]').input_value()
        page.locator('main form button[type=submit]').click(); page.wait_for_load_state('networkidle')
        check(page.locator('[name=act_code]').input_value() == '__OTHER__', 'Other choice retained after error')
        check(page.locator('[name=task_name]').input_value() == 'Administrative '+stamp, 'typed name retained after error')
        check(page.locator('[name=description]').input_value() == stamp+'-other' and page.locator('[name=assigned_to_employee]').input_value() == assignee, 'description/assignee retained')
        page.locator('[name=priority]').select_option('Normal')
        page.locator('main form button[type=submit]').click(); page.wait_for_load_state('networkidle')
        other = orm(lambda: Task.objects.get(description=stamp+'-other'))
        check(other.act_code is None and other.task_name == 'Administrative '+stamp, 'administrative task saves NULL')
        page.goto(base+'/portal/tasks/create/', wait_until='networkidle')
        search = page.locator('[data-ui-choice-source="task_create-act_code"]')
        search.fill('NO_MATCH_SENTINEL')
        check(page.locator('[name=act_code]').input_value() == '' and not search.evaluate('x=>x.checkValidity()'), 'unselected typed query cannot submit')
        search.press('Escape');check(search.input_value() == '', 'Escape restores current choice')
        search.focus();search.press('ArrowDown');check(bool(search.get_attribute('aria-activedescendant')), 'Arrow activates option');search.press('Escape');search.press('Tab');check(page.evaluate('document.activeElement.checkVisibility()'), 'Tab reaches visible control')
        context.close()
        nojs = browser.new_context(java_script_enabled=False, service_workers='block')
        page = nojs.new_page();login(page, base)
        for choice, title in ((code, ''), ('__OTHER__', 'No JS administrative '+stamp)):
            page.goto(base+'/portal/tasks/create/')
            page.locator('[name=act_code]').select_option(choice)
            check(page.locator('[name=task_name]').is_editable(), 'native name usable '+choice)
            page.locator('[name=task_name]').fill(title)
            page.locator('[name=description]').fill(stamp+'-nojs-'+choice)
            page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
            task = orm(lambda: Task.objects.get(description=stamp+'-nojs-'+choice))
            check(task.task_name == (ACTIVITY_CODE_NAMES[choice] if choice != '__OTHER__' else title), 'no-JS server derives or accepts title '+choice)
        nojs.close()
        for phase, port in (('before', args.baseline_port), ('after', args.port)):
            ctx = browser.new_context(service_workers='block', viewport={'width':1756,'height':1050}, locale='vi-VN')
            page = ctx.new_page();origin=f'http://127.0.0.1:{port}';login(page, origin)
            page.goto(origin+'/portal/tasks/create/', wait_until='networkidle')
            for width in (1756,1440,1280,1024,768,390,360):
                page.set_viewport_size({'width':width,'height':1050 if width>600 else 844})
                for theme in ('light','dark'):
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t', theme)
                    page.mouse.move(0,0)
                    file=f'{phase}-{width}-{theme}.png';page.screenshot(path=str(out/file), full_page=True);report['screenshots'].append(file)
                    if phase == 'after':
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), f'{width}/{theme} no overflow')
                        if width >= 1280:
                            rows=page.locator('.ui-task-assignment .ui-field').evaluate_all('xs=>xs.slice(-4).map(x=>x.getBoundingClientRect().y)')
                            check(max(rows)-min(rows)<=1, f'{width}/{theme} last four fields share row')
                        if width == 360:
                            search=page.locator('[data-ui-choice-source="task_create-act_code"]');search.focus();search.press('ArrowDown')
                            check(page.locator('.ui-choice-popover:popover-open').evaluate('x=>{const r=x.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1}'), '360 popup inside viewport '+theme);search.press('Escape')
            ctx.close()
        browser.close()
    for width in (1756,390):
        for theme in ('light','dark'):
            sheet=Image.new('RGB',(1400,1200),'#e5e7eb');draw=ImageDraw.Draw(sheet)
            for col,phase in enumerate(('before','after')):
                draw.text((col*700+8,5),f'{phase} / {width}px / {theme}',fill='black')
                with Image.open(out/f'{phase}-{width}-{theme}.png') as im:
                    im.thumbnail((690,1160));sheet.paste(im,(col*700,30))
            sheet.save(out/f'contact-{width}-{theme}.png')
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    workers.shutdown(wait=True)
    print(json.dumps({'checks':len(report['checks']),'failures':report['failures'],'screenshots':len(report['screenshots'])}))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
