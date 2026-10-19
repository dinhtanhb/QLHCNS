"""Check complete row hover/focus coverage on synthetic list pages."""
import argparse
import json
from pathlib import Path
import sys

from run_layout_alignment_audit import configure


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--packages-dir',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8836)
    parser.add_argument('--baseline-port',type=int,default=8837)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];folder=args.directory.resolve()
    if folder==root or root in folder.parents:parser.error('External synthetic runtime required')
    configure(root,folder);sys.path.insert(0,str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    from PIL import Image,ImageDraw
    password=next(x.split(': ',1)[1] for x in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
    routes={'employees':'/portal/hr/employees/','tasks':'/portal/tasks/?scope=assigned_by_me',
            'leave':'/portal/leave/','contracts':'/portal/hr/contracts/'}
    output=folder/'table-hover-uat';output.mkdir(exist_ok=True)
    report={'synthetic_only':True,'cases':[],'failures':[]}

    def check(ok,label):
        if not ok:report['failures'].append(label)

    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        for phase,port in (('before',args.baseline_port),('after',args.port)):
            ctx=browser.new_context(service_workers='block',viewport={'width':1756,'height':1050},locale='vi-VN');page=ctx.new_page();base=f'http://127.0.0.1:{port}'
            page.goto(base+'/portal/login/');page.locator('[name=username]').fill('demo-hr');page.locator('[name=password]').fill(password);page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
            for name,url in routes.items():
                response=page.goto(base+url,wait_until='networkidle')
                check(response.status==200,phase+'/'+name+' HTTP200')
                row=page.locator('.ui-table tbody tr').filter(has=page.locator('td:not([colspan])')).first
                check(row.count()>0,phase+'/'+name+' required populated row')
                if not row.count():continue
                for width in (1756,1440,1024,390):
                    page.set_viewport_size({'width':width,'height':1050 if width>600 else 844})
                    for theme in ('light','dark'):
                        page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme);page.mouse.move(0,0)
                        page.evaluate('()=>document.activeElement?.blur()')
                        normal=row.evaluate('r=>[...r.children].map(x=>({tag:x.tagName,bg:getComputedStyle(x).backgroundColor,padding:getComputedStyle(x).padding,border:getComputedStyle(x).borderBottom,height:x.getBoundingClientRect().height}))')
                        row.locator('td,th').first.hover()
                        hovered=row.evaluate('r=>[...r.children].map(x=>({bg:getComputedStyle(x).backgroundColor,height:x.getBoundingClientRect().height}))')
                        file=f'{phase}-{name}-{width}-{theme}.png';page.screenshot(path=str(output/file),full_page=True)
                        case={'phase':phase,'route':name,'width':width,'theme':theme,'normal':normal,'hovered':hovered}
                        report['cases'].append(case)
                        if phase=='after':
                            check(len({x['bg'] for x in hovered})==1 and hovered[0]['bg']!='rgba(0, 0, 0, 0)',f'{name}/{width}/{theme} all cells hover same background')
                            check(all(a['height']==b['height'] for a,b in zip(normal,hovered)),f'{name}/{width}/{theme} no height shift')
                            check(len({x['border'] for x in normal})==1,f'{name}/{width}/{theme} continuous row borders')
                            if normal[0]['tag']=='TH':
                                check(normal[0]['bg']==normal[1]['bg'] and normal[0]['padding']==normal[1]['padding'],f'{name}/{width}/{theme} row header body styling')
                            page.mouse.move(0,0)
                            focus_target=row.locator('a,button').first
                            if not focus_target.count():
                                focus_target=row.locator('td').first
                                focus_target.evaluate('x=>x.tabIndex=0')
                            focus_target.focus()
                            focused=row.evaluate('r=>[...r.children].map(x=>getComputedStyle(x).backgroundColor)')
                            check(len(set(focused))==1 and focused[0]==hovered[0]['bg'],f'{name}/{width}/{theme} focus covers all cells')
                            focus_target.evaluate('x=>{x.blur();if(x.tagName==="TD")x.removeAttribute("tabindex");}')
                if phase=='after' and name=='employees':
                    button=row.locator('[popovertarget]');menus=page.locator('.ui-row-popover')
                    check(menus.evaluate_all('xs=>xs.every(x=>!x.matches(":popover-open"))'),'employee action menus initially closed')
                    button.click();menu=page.locator('.ui-row-popover:popover-open');check(menu.count()==1,'only clicked action menu opens')
                    item=menu.locator('a').first;item.hover();check(item.evaluate('x=>getComputedStyle(x).backgroundColor!=="rgba(0, 0, 0, 0)"'),'menu item hover retained');item.press('Escape');check(page.locator('.ui-row-popover:popover-open').count()==0,'Escape closes menu')
            ctx.close()
        browser.close()
    for width in (1756,390):
        for theme in ('light','dark'):
            sheet=Image.new('RGB',(1400,1760),'#e5e7eb');draw=ImageDraw.Draw(sheet)
            for index,name in enumerate(routes):
                draw.text((8,index*440+5),f'{name} {width}/{theme} BEFORE / AFTER',fill='black')
                for col,phase in enumerate(('before','after')):
                    file=output/f'{phase}-{name}-{width}-{theme}.png'
                    if not file.exists():continue
                    with Image.open(file) as im:
                        tile=im.crop((0,0,im.width,min(im.height,1050 if width>600 else 844)));tile.thumbnail((690,410));sheet.paste(tile,(col*700,index*440+25))
            sheet.save(output/f'contact-{width}-{theme}.png')
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'cases':len(report['cases']),'failures':report['failures']}))
    return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
