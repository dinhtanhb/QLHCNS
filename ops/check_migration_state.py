"""Read Django migration state without applying or creating migrations.

Exit 1 when a migration recorded in source is not applied in the selected
database.  The command deliberately never calls ``migrate`` or writes data.
"""
from __future__ import annotations

import argparse
from io import StringIO
import os
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="default", help="Django database alias to inspect")
    parser.add_argument("--app", action="append", dest="apps", help="Limit report to an app label; repeatable")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

    from django.core.management import call_command
    from django.db import connections
    from django.db.migrations.loader import MigrationLoader

    connection = connections[args.database]
    try:
        loader = MigrationLoader(connection, ignore_no_migrations=True)
    except Exception as exc:
        print(f"Cannot read migration state for database alias {args.database!r}: {exc.__class__.__name__}", file=sys.stderr)
        return 2
    apps = set(args.apps or [])
    disk = set(loader.disk_migrations)
    if apps:
        disk = {node for node in disk if node[0] in apps}
    applied = set(loader.applied_migrations)
    missing = sorted(disk - applied)

    plan = StringIO()
    call_command("showmigrations", "--plan", database=args.database, stdout=plan)
    print(plan.getvalue().rstrip())
    print("\nMigration source:", ", ".join(f"{app}.{name}" for app, name in sorted(disk)))
    if missing:
        print("Outstanding:", ", ".join(f"{app}.{name}" for app, name in missing))
        return 1
    print("Outstanding: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
