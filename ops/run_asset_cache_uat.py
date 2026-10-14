"""Verify a warm, stale CSS/service-worker session updates without clearing data."""
import argparse
import json
from pathlib import Path
import sys
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8770)
    parser.add_argument('--baseline-port', type=int, default=8771)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('Synthetic runtime must be outside source.')
    if json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8')).get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    password = next(line.split(': ', 1)[1] for line in (folder / 'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright
    output = folder / 'asset-cache-uat'
    output.mkdir(exist_ok=True)
    state = {'port': args.baseline_port}
    old_cache = 'ihrms-static-v18-dispatch-register-20261014'
    new_cache = 'ihrms-static-v19-planning-20261014'
    old_css = """@media screen {
    .portal-app .ui-main .ui-query-bar {display:grid !important;grid-template-columns:minmax(0,1fr) auto !important;}
    .portal-app .ui-main .ui-query-actions {grid-column:2 !important;}
    }"""
    checks = []

    def check(ok, label):
        if not ok:
            raise AssertionError(label)
        checks.append(label)

    class Proxy(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            connection = http.client.HTTPConnection('127.0.0.1', state['port'])
            connection.request(self.command, self.path, body=body, headers=dict(self.headers))
            response = connection.getresponse()
            payload = response.read()
            if state['port'] == args.baseline_port and self.path.startswith('/static/css/tailwind.css'):
                payload += old_css.encode()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in ('content-length','transfer-encoding','connection','server','date'):
                    self.send_header(key, value)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            connection.close()

        do_POST = do_GET

    proxy = ThreadingHTTPServer(('127.0.0.1', 0), Proxy)
    Thread(target=proxy.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(proxy.server_port)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width':1440, 'height':1000})
        page = context.new_page()
        page.goto(base + '/portal/login/')
        page.locator('[name=username]').fill('demo-hr')
        page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click()
        page.wait_for_load_state('networkidle')
        page.goto(base + '/portal/hr/employees/', wait_until='networkidle')
        page.evaluate('async()=>{await navigator.serviceWorker.ready;}')
        page.wait_for_function('()=>!!navigator.serviceWorker.controller')
        page.reload(wait_until='networkidle')
        check(old_cache in page.evaluate('()=>caches.keys()'), 'previous release worker cache populated')
        gap = """()=>{const f=document.querySelector('.ui-query-bar');const x=f.querySelector('.ui-field input').getBoundingClientRect();const b=f.querySelector('button[type=submit]').getBoundingClientRect();return b.left-x.right;}"""
        before = page.evaluate(gap)
        check(before > 100, 'stale retained CSS reproduces detached action')
        page.screenshot(path=str(output / 'stale-css.png'), full_page=True)
        # Normal reload, retaining cookies, browser cache and the old CacheStorage.
        state['port'] = args.port
        page.reload(wait_until='networkidle')
        after = page.evaluate(gap)
        check(0 <= after <= 17, 'normal reload loads new inline asset URLs')
        check(page.locator('.ui-results-card .ui-query-bar').count() == 1, 'updated result grouping visible')
        page.evaluate('async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();}')
        for _ in range(100):
            keys = page.evaluate('()=>caches.keys()')
            if new_cache in keys and old_cache not in keys:
                break
            page.wait_for_timeout(100)
        check(new_cache in keys, 'new worker cache activated')
        check(old_cache not in keys, 'old worker cache retired')
        page.reload(wait_until='networkidle')
        check(0 <= page.evaluate(gap) <= 17, 'layout survives controlling worker reload')
        page.goto(base+'/portal/timesheet/?month=9&year=2026',wait_until='networkidle')
        check(page.locator('link[href*="print_forms.css"]').get_attribute('href').endswith('v=20261014-dispatch-register'), 'fresh print stylesheet URL loaded')
        page.emulate_media(media='print')
        check(page.locator('.ui-personal-timesheet-table').evaluate('x=>getComputedStyle(x).fontFamily.includes("Times New Roman")&&parseFloat(getComputedStyle(x).fontSize)>=13.33'), 'warm cache loads BCC print font')
        page.emulate_media(media='screen')
        page.screenshot(path=str(output / 'updated-css.png'), full_page=True)
        browser.close()
    proxy.shutdown()
    proxy.server_close()
    (output / 'result.json').write_text(json.dumps({'checks':checks,'before_gap':before,'after_gap':after,'passed':True,'synthetic_only':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(checks),'before_gap':before,'after_gap':after,'passed':True}))


if __name__ == '__main__':
    main()
