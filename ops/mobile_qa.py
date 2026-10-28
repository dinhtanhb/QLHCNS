"""Create/serve a synthetic backend and exported native UI on one QA origin.

Uses no production accounts, files, cookies or database. Credentials are written
only to the supplied directory outside the repository, never printed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import types


def configure(folder):
    root = Path(__file__).resolve().parents[1]
    marker = folder/'synthetic-demo.json'
    runtime = json.loads(marker.read_text(encoding='utf-8'))
    if runtime.get('synthetic_only') is not True or not (folder/'synthetic.sqlite3').is_file():
        raise RuntimeError('Not an initialized synthetic QA directory')
    os.environ.update(DJANGO_SETTINGS_MODULE='config.settings', APP_ENV='test',
        DB_ENGINE='django.db.backends.sqlite3', SECRET_KEY=runtime['secret_key'],
        DEBUG='True', M365_STORAGE_ENABLED='False', ENABLE_HTTPS_ENFORCEMENT='False',
        MOBILE_API_ENABLED='True', MOBILE_PUSH_ENABLED='False')
    sys.path.insert(0, str(root/'src'))
    import config.settings as cfg
    cfg.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(folder/'synthetic.sqlite3'), 'OPTIONS': {'timeout': 30}}}
    cfg.MEDIA_ROOT = folder/'media'
    cfg.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    cfg.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
    cfg.SYNTHETIC_DEMO = True
    import django
    django.setup()
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('create', 'serve'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8789)
    parser.add_argument('--bind', default='127.0.0.1', help='LAN IP only for isolated phone QA, default loopback')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('QA runtime must stay outside repository')
    if args.command == 'create':
        subprocess.run([sys.executable, str(root/'ops/dashboard_demo.py'), 'create', '--directory', str(folder)], check=True)
    root = configure(folder)
    if args.command == 'create':
        from django.utils import timezone
        from apps.security.models import User
        from apps.attendance.models import Attendance
        users = {name: User.objects.get(username='demo-'+name) for name in ('employee', 'manager', 'hr', 'director')}
        for child, parent in [('employee', 'manager'), ('manager', 'hr'), ('hr', 'director')]:
            employee = users[child].employee
            employee.manager = users[parent].employee
            employee.save(update_fields=['manager'])
        Attendance.objects.get_or_create(employee=users['employee'].employee, attendance_date=timezone.localdate(),
            defaults={'working_hours': 8, 'status': 'Present'})
        manifest = {'synthetic_only': True, 'origin': f'http://127.0.0.1:{args.port}',
            'accounts_file': 'DEMO_ACCOUNTS.txt', 'source': 'synthetic generated fixtures, no production copy'}
        (folder/'mobile-qa.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('Created isolated mobile QA. Credentials stay in', folder/'DEMO_ACCOUNTS.txt')
        return
    from django.conf import settings
    from django.core.management import call_command
    from django.urls import path, re_path
    from django.views.static import serve
    from config.urls import urlpatterns
    dist = root/'mobile/dist'
    if not (dist/'index.html').is_file():
        parser.error('Export mobile web QA first: cd mobile; npx expo export --platform web')
    def spa(request, asset=''):
        candidate = (dist/asset).resolve()
        if not candidate.is_relative_to(dist.resolve()):
            from django.http import Http404
            raise Http404
        return serve(request, asset if candidate.is_file() else 'index.html', document_root=dist)
    module = types.ModuleType('mobile_qa_urls')
    module.urlpatterns = [path('', spa)] + urlpatterns + [re_path(r'^(?P<asset>.*)$', spa)]
    sys.modules[module.__name__] = module
    settings.ROOT_URLCONF = module.__name__
    if args.bind not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append(args.bind)
    call_command('runserver', f'{args.bind}:{args.port}', use_reloader=False)


if __name__ == '__main__':
    main()
