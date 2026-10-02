#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Management commands may run with stdout/stderr redirected by Task Scheduler,
# CI, or a shell pipeline. On Windows those streams can default to a legacy
# code page that cannot encode Vietnamese output. Configure them once here so
# every command launched through manage.py uses UTF-8 and never crashes on an
# unencodable character.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
