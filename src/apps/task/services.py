"""Manual task creation: reserve annual codes without another schema counter."""
import re
import time

from django.db import IntegrityError, OperationalError, connections, transaction
from django.utils import timezone

from .models import Task


def create_manual_task(*, year=None, using="default", **values):
    """Serialize the indexed code range, then save; retry competing inserts/locks.

    SQL Server HOLDLOCK protects even an empty range. SQLite has no row locks:
    acquire its writer reservation before reading. Include soft-deleted codes.
    The outer caller must not open a transaction (retries need a fresh snapshot).
    """
    connection = connections[using]
    if connection.in_atomic_block:
        # TestCase's wrapping transaction is fine when no concurrent writers run;
        # real request callers are intentionally not atomic.
        if not any(getattr(block, "_from_testcase", False) for block in connection.atomic_blocks):
            raise RuntimeError("create_manual_task must own its transaction")
    year = year or timezone.localdate().year
    prefix = f"CV-{year}-"
    pattern = re.compile(re.escape(prefix) + r"(\d+)$")
    values.pop("task_code", None)
    candidate = Task(**values)
    candidate.full_clean(exclude=("task_code",))
    for attempt in range(8):
        try:
            with transaction.atomic(using=using):
                with connection.cursor() as cursor:
                    if connection.vendor == "microsoft":
                        cursor.execute("SELECT [TaskCode] FROM [tblTask] WITH (UPDLOCK, HOLDLOCK) WHERE [TaskCode] LIKE %s", [prefix + "%"])
                        codes = [row[0] for row in cursor.fetchall()]
                    elif connection.vendor == "sqlite":
                        cursor.execute('UPDATE "tblTask" SET "TaskCode" = "TaskCode" WHERE 1 = 0')
                        codes = list(Task.all_objects.using(using).filter(task_code__startswith=prefix).values_list("task_code", flat=True))
                    else:
                        raise RuntimeError("Unsupported task code allocation backend")
                highest = max((int(match.group(1)) for code in codes if (match := pattern.fullmatch(code))), default=0)
                candidate.task_code = f"{prefix}{highest + 1:04d}"
                candidate.save(using=using, force_insert=True)
                return candidate
        except (IntegrityError, OperationalError) as error:
            retryable = isinstance(error, IntegrityError) or any(word in str(error).lower() for word in ("locked", "deadlock", "1205"))
            if not retryable or attempt == 7:
                raise
            candidate.pk = None
            candidate._state.adding = True
            time.sleep(min(0.02 * 2 ** attempt, 0.5))
