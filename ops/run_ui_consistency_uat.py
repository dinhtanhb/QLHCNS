"""Compare the three approved sample pages on an external synthetic database."""
import argparse
from datetime import timedelta
import json
from pathlib import Path
import sys
import uuid

from run_layout_alignment_audit import configure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8792)
    parser.add_argument('--baseline-port', type=int, default=8791)
    parser.add_argument('--flows', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('External synthetic runtime required')
    configure(root, folder)
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    from django.urls import reverse
    from django.utils import timezone

    password = next(line.split(': ', 1)[1] for line in
                    (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines()
                    if line.startswith('Mật khẩu'))
    output = folder/'consistency-uat'
    output.mkdir(exist_ok=True)
    report = {'synthetic_only': True, 'checks': [], 'failures': [], 'screenshots': []}

    def check(value, label):
        report['checks' if value else 'failures'].append(label)

    routes = {'dashboard': reverse('portal:dashboard'),
              'recruitment': reverse('portal:recruitment_hub'),
              'assets': reverse('portal:asset_admin_list')}
    stamp = 'CONS-'+uuid.uuid4().hex[:10]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        for phase, port in (('before', args.baseline_port), ('after', args.port)):
            context = browser.new_context(viewport={'width':1756, 'height':1080},
                                          locale='vi-VN', service_workers='block', reduced_motion='reduce')
            page = context.new_page()
            page.on('pageerror', lambda e: report['failures'].append(str(e)))
            base = f'http://127.0.0.1:{port}'
            page.goto(base+'/portal/login/')
            page.locator('[name=username]').fill('demo-hr')
            page.locator('[name=password]').fill(password)
            page.locator('main form button[type=submit]').click()
            page.wait_for_load_state('networkidle')
            check('/login/' not in page.url, phase+' login')
            for width in (1756, 390):
                page.set_viewport_size({'width': width, 'height':1080 if width>600 else 844})
                for theme in ('light', 'dark'):
                    page.evaluate('(t)=>localStorage.setItem("ihrms-theme",t)', theme)
                    for name, route in routes.items():
                        response = page.goto(base+route, wait_until='networkidle')
                        page.evaluate('(t)=>document.documentElement.dataset.theme=t', theme)
                        check(response.status == 200, f'{phase}/{width}/{theme}/{name} opens')
                        filename = f'{phase}-{name}-{width}-{theme}.png'
                        page.screenshot(path=str(output/filename), full_page=True)
                        report['screenshots'].append(filename)
                        if phase == 'before':
                            continue
                        label = f'{width}/{theme}/{name}'
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), label+' no page overflow')
                        styles = page.locator('.ui-card:not(.ui-card--table):not(.ui-card--sectioned)').evaluate_all(
                            '(xs)=>xs.filter(x=>x.checkVisibility()).map(x=>parseFloat(getComputedStyle(x).paddingLeft))')
                        check(bool(styles) and all(x >= (16 if width<768 else 24) for x in styles), label+' card insets')
                        sizes = page.locator('.ui-button').evaluate_all(
                            '(xs)=>xs.filter(x=>x.checkVisibility()).map(x=>({h:x.getBoundingClientRect().height,font:parseFloat(getComputedStyle(x).fontSize)}))')
                        check(bool(sizes) and all(x['h']>=43.5 and x['font']>=14 for x in sizes), label+' buttons 44px/14px')
                        if name == 'recruitment':
                            check(page.locator('.ui-recruitment-step').count()==6, label+' six steps')
                            geometry = page.locator('.ui-recruitment-steps').evaluate(
                                '(x)=>({width:x.clientWidth,columns:getComputedStyle(x).gridTemplateColumns.split(" ").length})')
                            expected = 3 if geometry['width']>=1024 else 2 if geometry['width']>=640 else 1
                            check(geometry['columns']==expected, label+' container columns')
                        if name == 'dashboard':
                            titles = page.locator('.home-card-header h3').evaluate_all('(xs)=>xs.map(x=>parseFloat(getComputedStyle(x).fontSize))')
                            check(bool(titles) and all(x==18 for x in titles), label+' 18px content card titles')
                        if name == 'assets':
                            titles = page.locator('.ui-card-title').evaluate_all('(xs)=>xs.map(x=>parseFloat(getComputedStyle(x).fontSize))')
                            check(all(x==18 for x in titles), label+' 18px card titles')
                            check(page.locator('form:has([name=asset_code])').evaluate('(x)=>x.querySelector(".ui-form-actions").getBoundingClientRect().top>=x.querySelector("[name=note]").getBoundingClientRect().bottom'), label+' actions below last field')
                            page.locator('[name=asset_code]').focus()
                            page.keyboard.press('Tab')
                            check(page.locator('[name=asset_name]').evaluate('(x)=>x===document.activeElement'), label+' keyboard field order')

            # Query real forms at exact container boundaries, independent of viewport.
            if phase == 'after':
                for width in (360,768,1024,1440):
                    page.set_viewport_size({'width':width,'height':920})
                    for name,route in routes.items():
                        page.goto(base+route,wait_until='networkidle')
                        for theme in ('light','dark'):
                            page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                            check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{width}/{theme}/{name} no page overflow')
                page.goto(base+routes['recruitment'],wait_until='networkidle')
                page.set_viewport_size({'width':390,'height':844})
                page.locator('.ui-recruitment-step .ui-card-title').first.evaluate('(x)=>x.textContent="Tiêu đề bước tuyển dụng rất dài để kiểm tra khả năng xuống dòng trên màn hình hẹp"')
                check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'long recruitment title wraps without overflow')
                page.set_viewport_size({'width':1756, 'height':1080})
                page.goto(base+routes['assets'], wait_until='networkidle')
                form = page.locator('form[action*="assets"]').first
                if not form.count():
                    form = page.locator('form:has([name=asset_code])')
                # The asset form now follows the long-form 1/2/3-column contract.
                for width, expected in ((419,1),(420,2),(421,2),(639,2),(640,3),(641,3),(899,3),(900,3),(901,3)):
                    form.evaluate('(x,w)=>{x.style.width=w+"px";x.style.maxWidth="none"}', width)
                    columns = form.locator('.ui-form-grid').evaluate('(x)=>getComputedStyle(x).gridTemplateColumns.split(" ").length')
                    check(columns==expected, f'container {width}px -> {expected} columns')
                page.goto(base+routes['assets'], wait_until='networkidle')
                page.evaluate('document.documentElement.style.zoom="2"')
                check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), 'assets 200% zoom no page overflow')
                page.evaluate('document.documentElement.style.zoom=""')

                if args.flows:
                    def fill_number(name, value):
                        source = page.locator(f'[name="{name}"]')
                        control = source if source.is_visible() else page.locator('#'+source.get_attribute('id')+'-display')
                        control.fill(value)
                        control.press('Tab')

                    page.goto(base+routes['assets'], wait_until='networkidle')
                    page.locator('[name=asset_code]').fill(stamp)
                    page.locator('[name=asset_name]').fill('Tài sản giả lập tên dài để kiểm tra giao diện và dữ liệu lưu')
                    option = page.locator('[name=asset_type] option').evaluate_all('(xs)=>xs.find(x=>x.value)?.value')
                    page.locator('[name=asset_type]').select_option(option)
                    fill_number('quantity', '2')
                    page.locator('button:has-text("Thêm tài sản")').click()
                    page.wait_for_load_state('networkidle')
                    check(page.url.endswith(routes['assets']), 'asset redirects to list')
                    check('Đã thêm tài sản.' in page.locator('main').inner_text(), 'asset success message')
                    check(stamp in page.locator('table').inner_text(), 'asset visible in list')

                    page.goto(base+reverse('portal:recruitment_create'), wait_until='networkidle')
                    page.locator('[name=request_code]').fill(stamp)
                    for name in ('department', 'position'):
                        option = page.locator(f'[name={name}] option').evaluate_all('(xs)=>xs.find(x=>x.value)?.value')
                        page.locator(f'[name={name}]').select_option(option)
                    fill_number('required_quantity', '2')
                    page.locator('[name=required_date]').fill((timezone.localdate()+timedelta(days=30)).isoformat())
                    page.locator('[name=request_reason]').fill('Dữ liệu giả kiểm thử bố cục và luồng tạo đề xuất')
                    page.locator('button[type=submit]:has-text("Gửi đề xuất")').click()
                    page.wait_for_load_state('networkidle')
                    check(reverse('portal:recruitment_list') in page.url, 'recruitment redirects to list')
                    check('Đã gửi đề xuất tuyển dụng' in page.locator('main').inner_text(), 'recruitment success message')
                    page.goto(base+routes['dashboard'], wait_until='networkidle')
                    check(page.locator('.home-main-kpis').count()==1, 'dashboard refreshed after writes')
                    page.locator('a.ui-button:has-text("Tạo đơn nghỉ")').click()
                    page.wait_for_load_state('networkidle')
                    check(reverse('portal:leave_create') in page.url, 'dashboard create-leave action target')
            context.close()
        browser.close()

    if args.flows:
        from apps.asset.models import Asset
        from apps.recruitment.models import RecruitmentRequest
        check(Asset.objects.filter(asset_code=stamp, quantity=2).exists(), 'asset persisted with quantity 2')
        check(RecruitmentRequest.objects.filter(request_code=stamp, required_quantity=2, status='Pending').exists(), 'recruitment persisted Pending quantity 2')

    for width in (1756,390):
        for theme in ('light','dark'):
            sheet = Image.new('RGB', (1400, 1320), '#e5e7eb')
            draw = ImageDraw.Draw(sheet)
            for row, name in enumerate(routes):
                y=row*440
                draw.text((8,y+6), f'{name} {width}px {theme} - BEFORE / AFTER', fill='black')
                for col,phase in enumerate(('before','after')):
                    with Image.open(output/f'{phase}-{name}-{width}-{theme}.png') as source:
                        tile=source.crop((0,0,source.width,min(source.height,1080 if width>600 else 844)))
                        tile.thumbnail((690,410))
                        sheet.paste(tile,(col*700,y+26))
            sheet.save(output/f'contact-sheet-{width}-{theme}.png')
    (output/'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']), 'failures':report['failures'], 'screenshots':len(report['screenshots'])}, ensure_ascii=False))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
