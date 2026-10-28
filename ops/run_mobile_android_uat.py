"""Install and exercise the standalone QA APK on an isolated Android emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--serial', default='emulator-5556')
    args = parser.parse_args()
    if not args.serial.startswith('emulator-'):
        parser.error('Only an isolated emulator may be used; this clears its QA app data')
    marker = json.loads((args.directory/'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:
        parser.error('Only synthetic QA credentials may be used')
    password = next(line.split(': ', 1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    args.output.mkdir(parents=True, exist_ok=True)
    adb = args.sdk/'platform-tools/adb.exe'
    checks = []
    def run(*command, timeout=45):
        try:
            value = subprocess.run([str(adb), '-s', args.serial, *command], capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError('ADB QA timed out; credential arguments not printed') from None
        if value.returncode:
            raise RuntimeError('ADB QA operation failed; credential arguments not printed')
        return value.stdout
    def xml():
        run('shell', 'uiautomator', 'dump', '/sdcard/ihrms-qa-ui.xml')
        return ET.fromstring(run('exec-out', 'cat', '/sdcard/ihrms-qa-ui.xml'))
    def find(label, tree=None):
        tree = tree if tree is not None else xml()
        nodes = list(tree.iter('node'))
        return next((n for n in nodes if n.get('content-desc') == label), next((n for n in nodes if n.get('text') == label), None))
    def tap_node(node):
        b = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
        if len(b) != 4 or b[2] <= b[0] or b[3] <= b[1]:
            raise RuntimeError('QA control has no visible bounds')
        run('shell', 'input', 'tap', str((b[0]+b[2])//2), str((b[1]+b[3])//2))
    def tap(label):
        for _ in range(5):
            node = find(label)
            if node is not None:
                tap_node(node); return
            run('shell', 'input', 'swipe', '540', '1755', '540', '585', '250')
        raise RuntimeError('QA control not found: '+label)
    def wait_text(label):
        for _ in range(15):
            tree = xml()
            if find(label, tree) is not None:
                return tree
            time.sleep(1)
        raise RuntimeError('Native QA screen not reached: '+label)
    def screenshot(name):
        (args.output/(name+'.png')).write_bytes(run('exec-out', 'screencap', '-p'))
    def enter(node, value):
        if not re.fullmatch(r'[A-Za-z0-9_:/.-]+', value):
            raise RuntimeError('Unsupported synthetic input characters')
        tap_node(node); run('shell', 'input', 'text', value)
    package = 'vn.ihrms.internal.qa'
    run('install', '-r', str(args.apk.resolve()), timeout=120)
    checks.append('QA APK installs on Android emulator')
    run('shell', 'am', 'force-stop', package)
    run('shell', 'pm', 'clear', package)
    run('reverse', 'tcp:8789', 'tcp:8789')
    run('shell', 'wm', 'size', '1080x2340')
    run('shell', 'wm', 'density', '440')
    run('shell', 'settings', 'put', 'secure', 'show_ime_with_hard_keyboard', '1')
    run('shell', 'cmd', 'uimode', 'night', 'no')
    run('shell', 'settings', 'put', 'system', 'screen_off_timeout', '2147483647')
    run('shell', 'input', 'keyevent', '82')
    run('logcat', '-c')
    run('shell', 'monkey', '-p', package, '1')
    tree = wait_text('Đăng nhập')
    editors = [n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText']
    if len(editors) != 3:
        raise RuntimeError('Expected QA server, username and password controls')
    for index, value in enumerate(('http://127.0.0.1:8789', 'demo-employee', password)):
        tree = xml(); editors = [n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText']
        enter(editors[index], value)
        run('shell', 'input', 'keyevent', '4')
    tap('Đăng nhập'); wait_text('Hồ sơ của tôi')
    checks.append('Native login through isolated real API without Metro')
    screenshot('native-profile-light')
    tap('Chấm công'); wait_text('8.00 giờ làm việc')
    checks.append('Native attendance displays server record')
    screenshot('native-attendance-light')
    tap('Nghỉ phép'); wait_text('Tạo đơn nghỉ phép')
    checks.append('Native leave list and create action render')
    screenshot('native-leaves-light')
    run('shell', 'cmd', 'uimode', 'night', 'yes'); time.sleep(2)
    tap('Tôi'); wait_text('Hồ sơ của tôi'); screenshot('native-profile-dark')
    checks.append('Native automatic dark mode renders')
    tap('Đăng xuất'); wait_text('Đăng xuất IHRMS?'); tap('Xác nhận'); wait_text('Đăng nhập')
    checks.append('Native logout confirmation returns to login')
    screenshot('native-logout-dark')
    errors = run('logcat', '-d', '-s', 'AndroidRuntime', 'ReactNativeJS').decode('utf-8', errors='replace')
    (args.output/'native-runtime.log').write_text(errors, encoding='utf-8')
    if 'FATAL EXCEPTION' in errors or 'JavascriptException' in errors:
        raise RuntimeError('Native fatal error present; inspect isolated runtime evidence')
    checks.append('No fatal Android/React Native exception')
    result = {'synthetic_only': True, 'package': package, 'serial': args.serial,
        'android_api': run('shell', 'getprop', 'ro.build.version.sdk').decode().strip(),
        'apk_sha256': hashlib.sha256(args.apk.read_bytes()).hexdigest(), 'checks': checks,
        'count': len(checks), 'physical_device_tested': False}
    (args.output/'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'native_emulator': True, 'errors': 0}))


if __name__ == '__main__':
    main()
