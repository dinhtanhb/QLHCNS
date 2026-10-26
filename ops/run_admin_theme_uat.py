"""Verify rendered Jazzmin themes in Edge on an external synthetic QA runtime."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys


SURFACES = r"""() => {
 const root=document.documentElement;
 const color=token=>{const el=document.createElement('span');el.style.color=`var(${token})`;document.body.append(el);const value=getComputedStyle(el).color;el.remove();return value};
 const visible=x=>x.checkVisibility()&&x.getBoundingClientRect().width>1;
 const surface=color('--ui-surface'),text=color('--ui-text');
 const components=[...document.querySelectorAll('.card,.timeline-item,.form-control,.form-select,textarea,.select2-selection--single,.select2-selection--multiple,.select2-dropdown,.dropdown-menu.show')].filter(x=>visible(x)&&!x.disabled);
 const mismatches=components.filter(x=>getComputedStyle(x).backgroundColor!==surface).map(x=>({selector:x.id?'#'+x.id:x.tagName+'.'+x.className,background:getComputedStyle(x).backgroundColor,expected:surface}));
 const links=[...document.querySelectorAll('.app-main .card a:not(.btn):not(.nav-link):not(.dropdown-item)')].filter(visible);
 const assets=[...document.querySelectorAll('link[rel="stylesheet"],script[src]')].map(x=>new URL(x.href||x.src,location.href)).filter(x=>['/css/admin.css','/js/theme.js','/css/ui_controls.css','/js/ui_numbers.js'].some(path=>x.pathname.endsWith(path))).map(x=>({path:x.pathname,hash:x.searchParams.get('v')}));
 return {theme:root.dataset.theme,bootstrap:root.dataset.bsTheme,palette:root.dataset.palette,surface,text,components:components.length,mismatches,assets,links:links.map(x=>({color:getComputedStyle(x).color,expected:x.matches('.submit-row a.deletelink,.submit-row a.closelink')?'rgb(255, 255, 255)':color('--ui-link')})),overflow:root.scrollWidth>innerWidth+1};
}"""


CONTRAST = r"""el => {
 const rgba=value=>{const xs=value.match(/[\d.]+/g).map(Number);return [...xs.slice(0,3),xs.length>3?xs[3]:1]};
 const blend=(fg,bg)=>[...fg.slice(0,3).map((v,i)=>v*fg[3]+bg[i]*(1-fg[3])),1];
 let bg=[255,255,255,1];const chain=[];for(let x=el;x;x=x.parentElement)chain.unshift(x);
 for(const x of chain)bg=blend(rgba(getComputedStyle(x).backgroundColor),bg);
 const style=getComputedStyle(el),fg=blend(rgba(style.color),bg);
 const luminance=rgb=>rgb.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const a=luminance(fg),b=luminance(bg);
 return {foreground:style.color,background:style.backgroundColor,effectiveBackground:bg.slice(0,3),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),text:el.textContent.trim(),href:el.getAttribute('href')};
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--palette', choices=('viethealth', 'chamdong', 'thanam'), required=True)
    parser.add_argument('--widths', type=int, nargs='+', default=[1920, 1756, 1440, 1280, 1024, 768, 390])
    parser.add_argument('--actions-only', action='store_true', help='Focused contrast regression; still requires both real submit actions.')
    parser.add_argument('--submit-style', choices=('jazzmin', 'django'), default='jazzmin', help='Label the installed template or external Django submit-row compatibility fixture.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('QA runtime and evidence must remain outside source.')
    if json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    with sqlite3.connect(f'file:{(folder / "synthetic.sqlite3").as_posix()}?mode=ro', uri=True) as db:
        user_id = db.execute('SELECT id FROM tblUser WHERE username=?', ('demo-layout-admin',)).fetchone()[0]
        department_id = db.execute('SELECT id FROM tblDepartment WHERE IsDeleted=0 ORDER BY id LIMIT 1').fetchone()[0]
    password = next(line.split(': ', 1)[1] for line in (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright

    output = folder / ('admin-theme-' + args.palette + ('-django' if args.submit_style == 'django' else ''))
    output.mkdir(exist_ok=True)
    report = {'synthetic_only': True, 'palette': args.palette, 'submit_style': args.submit_style, 'checks': [], 'errors': [], 'cases': [], 'actions': [], 'screenshots': []}
    base = f'http://127.0.0.1:{args.port}'

    def check(ok, label):
        report['checks'].append(label)
        if not ok:
            report['errors'].append(label)

    def inspect(page, label, theme):
        data = page.evaluate(SURFACES)
        report['cases'].append(dict(label=label, **data))
        check(data['theme'] == data['bootstrap'] == theme, label + ' both theme attributes')
        check(data['palette'] == args.palette, label + ' server palette')
        check(not data['mismatches'], label + ' semantic surfaces ' + str(data['mismatches']))
        # Every link is checked, including Django's white submit actions;
        # actual button contrast is independently required below.
        check(all(link['color'] == link['expected'] for link in data['links']), label + ' semantic link colors')
        check(not data['overflow'], label + ' no document overflow')
        check(sum(asset['path'].endswith('/css/admin.css') for asset in data['assets']) == 1, label + ' admin CSS loaded once')
        check(all(asset['hash'] and len(asset['hash']) == 8 and all(c in '0123456789abcdef' for c in asset['hash']) for asset in data['assets']), label + ' content hashes for theme/control assets')

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            for theme in (() if args.actions_only else ('light', 'dark')):
                context = browser.new_context(viewport={'width': 1756, 'height': 1000}, locale='vi-VN', service_workers='block')
                # A stale vendor preference must not compete with the IHRMS toggle.
                context.add_init_script('if(!localStorage.getItem("ihrms-theme"))localStorage.setItem("ihrms-theme",' + json.dumps(theme) + ');localStorage.setItem("jazzmin-theme-mode",' + json.dumps('light' if theme == 'dark' else 'dark') + ');')
                page = context.new_page()
                page.on('pageerror', lambda error: report['errors'].append(str(error)))
                page.goto(base + '/admin/login/', wait_until='load')
                inspect(page, theme + ' login', theme)
                page.screenshot(path=str(output / ('login-' + theme + '.png')), full_page=True)
                page.locator('[name=username]').fill('demo-layout-admin')
                page.locator('[name=password]').fill(password)
                page.locator('button[type=submit]').click()
                page.wait_for_load_state('load')
                for width in args.widths:
                    page.set_viewport_size({'width': width, 'height': 1000})
                    for name, route in (
                        ('index', '/admin/'), ('users', '/admin/security/user/'),
                        ('user-form', f'/admin/security/user/{user_id}/change/'),
                        ('department-add', '/admin/organization/department/add/'),
                        ('history', f'/admin/security/user/{user_id}/history/'),
                    ):
                        response = page.goto(base + route, wait_until='load')
                        label = f'{name} {width} {theme}'
                        check(response.status == 200, label + ' opens')
                        inspect(page, label, theme)
                        if width in (1756, 390):
                            filename = f'{name}-{width}-{theme}.png'
                            page.screenshot(path=str(output / filename), full_page=True)
                            report['screenshots'].append(filename)
                        if name == 'index':
                            menu = page.locator('#jazzy-navbar [data-bs-toggle="dropdown"]:visible').last
                            check(menu.count() > 0, label + ' account menu present')
                            if menu.count():
                                menu.click()
                                check(page.locator('.dropdown-menu.show:visible').count() > 0, label + ' account menu opens')
                                inspect(page, label + ' account menu', theme)
                                page.keyboard.press('Escape')
                        if name == 'user-form':
                            selection = page.locator('.select2-selection--single:visible').first
                            if not selection.count():
                                for pane in page.locator('.tab-pane').all():
                                    if pane.locator('.select2-selection--single').count():
                                        pane_id = pane.get_attribute('id')
                                        trigger = page.locator(f'a[href="#{pane_id}"],button[data-bs-target="#{pane_id}"]').first
                                        if trigger.count():
                                            trigger.click()
                                            break
                                selection = page.locator('.select2-selection--single:visible').first
                            check(selection.count() > 0, label + ' visible Select2 exercised')
                            if selection.count():
                                selection.click()
                                check(page.locator('.select2-dropdown:visible').count() > 0, label + ' dropdown opens')
                                inspect(page, label + ' open Select2', theme)
                                page.keyboard.press('Escape')
                    page.goto(base + '/admin/', wait_until='load')
                    toggle = page.locator('[data-theme-toggle]')
                    toggle.focus()
                    page.keyboard.press('Enter')
                    opposite = 'light' if theme == 'dark' else 'dark'
                    inspect(page, f'{width} keyboard toggle', opposite)
                    check(page.evaluate('localStorage.getItem("ihrms-theme")') == opposite, 'saved toggle ' + str(width))
                    page.reload(wait_until='load')
                    inspect(page, f'{width} persisted reload', opposite)
                    # Mirror a second tab changing the one shared preference.
                    page.evaluate('(theme)=>{localStorage.setItem("ihrms-theme",theme);dispatchEvent(new StorageEvent("storage",{key:"ihrms-theme",newValue:theme}))}', theme)
                    inspect(page, f'{width} storage event', theme)
                context.close()
            for mode in (() if args.actions_only else ('light', 'dark')):
                context = browser.new_context(color_scheme=mode, service_workers='block')
                context.add_init_script('Object.defineProperty(window,"localStorage",{get(){throw new Error("QA storage blocked")}})')
                page = context.new_page()
                page.goto(base + '/admin/login/', wait_until='load')
                inspect(page, 'storage blocked system ' + mode, mode)
                opposite = 'light' if mode == 'dark' else 'dark'
                page.emulate_media(color_scheme=opposite)
                page.wait_for_function('(theme)=>document.documentElement.dataset.bsTheme===theme', arg=opposite)
                inspect(page, 'storage blocked system change ' + mode, opposite)
                context.close()
            # Existing SYS_ADMIN QA can view Department but cannot change it;
            # use that real read-only form for Close, never change app permissions.
            for account, action in (('demo-layout-admin', 'delete'), ('demo-sys', 'close')):
                for theme in ('light', 'dark'):
                    context = browser.new_context(viewport={'width': 1756, 'height': 1000}, service_workers='block')
                    context.add_init_script('localStorage.setItem("ihrms-theme",' + json.dumps(theme) + ');')
                    page = context.new_page()
                    page.goto(base + '/admin/login/', wait_until='load')
                    page.locator('[name=username]').fill(account)
                    page.locator('[name=password]').fill(password)
                    page.locator('button[type=submit],input[type=submit]').first.click()
                    page.wait_for_load_state('load')
                    for width in args.widths:
                        page.set_viewport_size({'width': width, 'height': 1000})
                        response = page.goto(base + f'/admin/organization/department/{department_id}/change/', wait_until='load')
                        label = f'{action} {width} {theme}'
                        check(response.status == 200, label + ' form opens')
                        attributes = page.locator('html').evaluate('x=>({theme:x.dataset.theme,bootstrap:x.dataset.bsTheme,palette:x.dataset.palette})')
                        check(attributes['theme'] == attributes['bootstrap'] == theme and attributes['palette'] == args.palette, label + ' actual requested palette/theme')
                        if args.submit_style == 'django':
                            selector = '.submit-row a.' + ('deletelink' if action == 'delete' else 'closelink')
                        elif action == 'delete':
                            selector = '#jazzy-actions a.btn[href*="/delete/"]'
                        else:
                            selector = '#jazzy-actions a.btn[href="/admin/organization/department/"]'
                        button = page.locator(selector)
                        check(button.count() == 1 and button.is_visible(), label + ' actual submit button present')
                        if button.count() != 1:
                            continue
                        for state in ('default', 'hover', 'focus'):
                            page.mouse.move(0, 0)
                            button.evaluate('x=>x.blur()')
                            if state == 'hover':
                                button.hover()
                            elif state == 'focus':
                                button.focus()
                            button.evaluate('async x=>Promise.all(x.getAnimations().filter(a=>a.effect.getComputedTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{})))')
                            sample = button.evaluate(CONTRAST)
                            report['actions'].append(dict(action=action, width=width, theme=theme, state=state, **sample))
                            check(sample['ratio'] >= 4.5, label + ' ' + state + ' contrast ' + str(round(sample['ratio'], 4)))
                        if width in (1756, 390):
                            filename = f'{action}-form-{width}-{theme}.png'
                            page.screenshot(path=str(output / filename), full_page=True)
                            report['screenshots'].append(filename)
                    context.close()
            browser.close()
    except Exception as error:
        report['errors'].append(str(error))
    (output / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks': len(report['checks']), 'cases': len(report['cases']), 'action_samples': len(report['actions']), 'errors': report['errors'], 'output': str(output)}))
    return bool(report['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
