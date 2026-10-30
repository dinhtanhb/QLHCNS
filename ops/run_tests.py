"""Run tests against an isolated database, with real-data storage disabled."""
import argparse
import os
from pathlib import Path
import secrets
import sys
import tempfile
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--backend', choices=('configured', 'sqlite', 'sqlserver'), required=True,
        help='Choose the test backend explicitly; prefer sqlite or sqlserver.',
    )
    parser.add_argument('labels', nargs='*')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    root = Path(__file__).resolve().parent.parent
    # Run before importing Django or touching a test database. Both CI and
    # Run-Tests.ps1 use this entry point, including focused test labels.
    from check_mobile_kpi_limit import check_limits
    try:
        frontend, backend = check_limits(root)
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        print(f'Mobile KPI preflight failed: {error}', file=sys.stderr)
        return 1
    print(f'Mobile KPI preflight OK: frontend={frontend}, backend={backend}', flush=True)
    os.chdir(root / 'src')
    sys.path.insert(0, str(root / 'src'))
    os.environ.update(
        DJANGO_SETTINGS_MODULE='config.settings',
        APP_ENV='test',  # Test HTTPS/storage isolation must not inherit production guards.
        SECRET_KEY=secrets.token_urlsafe(64),
        DEBUG='False',
        M365_STORAGE_ENABLED='False',
        ENABLE_HTTPS_ENFORCEMENT='False',
        MOBILE_PUSH_ENABLED='False',  # Never deliver external push from isolated regression runs.
    )
    if args.backend == 'sqlite':
        os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.test.runner import DiscoverRunner

    cfg = settings.DATABASES['default']
    if connection.vendor == 'sqlite':
        if args.backend == 'sqlserver':
            parser.error('SQL Server was requested but is not configured.')
        cfg['NAME'] = ':memory:'
        cfg['TEST'] = {**cfg.get('TEST', {}), 'NAME': ':memory:'}
    elif connection.vendor == 'microsoft':
        test_name = 'test_ihrms_' + uuid.uuid4().hex
        if test_name == cfg['NAME']:
            raise RuntimeError('Refusing to reuse the application database.')
        with connection.cursor() as cursor:
            cursor.execute('SELECT DB_ID(%s)', [test_name])
            if cursor.fetchone()[0] is not None:
                raise RuntimeError('Test database already exists; refusing to delete or reuse it.')
        cfg['TEST'] = {**cfg.get('TEST', {}), 'NAME': test_name}
        print('Disposable SQL Server database:', test_name)
    else:
        parser.error('Only SQLite and SQL Server are supported by this test wrapper.')

    class NonEmptyRunner(DiscoverRunner):
        def build_suite(self, *suite_args, **suite_kwargs):
            suite = super().build_suite(*suite_args, **suite_kwargs)
            count = suite.countTestCases()
            print('Discovered tests:', count)
            if count == 0:
                raise RuntimeError('No tests discovered; refusing to report success.')
            return suite

    with tempfile.TemporaryDirectory(prefix='ihrms-test-media-') as media_root:
        settings.MEDIA_ROOT = media_root
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        settings.M365_STORAGE_ENABLED = False
        print('Test backend:', connection.vendor)
        failures = NonEmptyRunner(verbosity=1, interactive=False).run_tests(args.labels or ['.'])
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())

