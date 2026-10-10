"""Reset only a named IHRMS QA database and create three synthetic users per role.

Run only after an independently verified backup. Credentials are written outside Git.
"""

import argparse
import csv
import os
from pathlib import Path
import re
import secrets
import sys
from datetime import date


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def quoted(identifier):
    return "[" + identifier.replace("]", "]]") + "]"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--backup-file", type=Path, required=True,
                        help="Existing non-empty .bak outside the repository; restore must be verified separately")
    parser.add_argument("--credentials", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    import django
    django.setup()
    from django.conf import settings
    from django.db import connection, transaction
    from apps.hrm.models import Employee
    from apps.organization.models import Department, Position
    from apps.security.models import Role, User
    from apps.security.permissions import (
        CBDA, DEPT_MANAGER, DIRECTOR, EMPLOYEE, FINANCE_OFFICER,
        HR_MANAGER, HR_OFFICER, PROJECT_COORDINATOR, PROJECT_MANAGER,
        SUPER_ADMIN, SYS_ADMIN,
    )

    if connection.vendor != "microsoft" or settings.DATABASES["default"]["NAME"] != args.database:
        raise RuntimeError("Refusing to reset a database other than the explicitly named SQL Server database")
    if settings.APP_ENV != "test":
        raise RuntimeError("QA reset requires APP_ENV=test on a disposable database copy")
    if not re.fullmatch(r"(?:qlhcns|ihrms)_uat_[A-Za-z0-9_]+|qlhcns_reset_preview_20261009", args.database):
        raise RuntimeError("Database name must explicitly identify a disposable QA/UAT copy")
    backup_file = args.backup_file.resolve()
    if (not args.backup_file.is_absolute() or backup_file.is_relative_to(ROOT)
            or backup_file.suffix.lower() != ".bak" or not backup_file.is_file()
            or backup_file.stat().st_size == 0):
        raise RuntimeError("A non-empty .bak outside the repository is required")
    if not args.credentials.is_absolute() or args.credentials.exists():
        raise RuntimeError("Credentials path must be an unused absolute path")
    if args.credentials.resolve().is_relative_to(ROOT):
        raise RuntimeError("Credentials must be stored outside the repository")
    if not args.credentials.parent.is_dir():
        raise RuntimeError("Credentials directory is missing")

    roles = (
        SUPER_ADMIN, SYS_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER,
        DEPT_MANAGER, FINANCE_OFFICER, EMPLOYEE, PROJECT_MANAGER,
        PROJECT_COORDINATOR, CBDA,
    )
    if set(Role.objects.values_list("role_code", flat=True)) != set(roles):
        raise RuntimeError("Existing role catalog does not match the 11 expected roles")
    department = Department.objects.order_by("pk").first()
    position = Position.objects.order_by("pk").first()
    if department is None or position is None:
        raise RuntimeError("Department and position catalogs must exist")

    keep = {
        "django_migrations", "django_content_type", "auth_permission",
        "auth_group", "auth_group_permissions", "tblRole",
        "tblOrganization", "tblDepartment", "tblPosition", "tblJobTitle",
        "tblLeaveType", "tblContractType", "tblHoliday", "tblWorkingCalendar",
        "tblInsuranceRateConfig", "tblPersonalIncomeTaxBracket",
        "tblTaxDeductionConfig", "tblAssetType", "tblDocumentCategory",
        "tblChecklistTemplate", "tblChecklistTemplateItem", "tblKPITemplate",
        "tblWorkShift", "tblSupplyItem", "tblMeetingRoom", "tblVehicle",
        "tblTrainingCourse", "tblDispatchBook",
    }
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT CAST(value AS nvarchar(50)) FROM sys.extended_properties
            WHERE class = 0 AND name = 'IHRMS_DISPOSABLE_QA'
        """)
        marker = cursor.fetchone()
        if not marker or marker[0] != "YES":
            raise RuntimeError("Database must have IHRMS_DISPOSABLE_QA=YES marker")
        cursor.execute("SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('dbo')")
        tables = {row[0] for row in cursor.fetchall()}
        if len(tables) != 107:
            raise RuntimeError(f"Unexpected table count: {len(tables)} (expected 107)")
        if not keep <= tables:
            raise RuntimeError(f"Expected catalog tables missing: {sorted(keep - tables)}")
        cursor.execute("""
            SELECT OBJECT_NAME(fk.parent_object_id), parent.name,
                   OBJECT_NAME(fk.referenced_object_id), parent.is_nullable
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
            JOIN sys.columns parent ON parent.object_id = fkc.parent_object_id
                AND parent.column_id = fkc.parent_column_id
            WHERE fk.parent_object_id IN (SELECT object_id FROM sys.tables)
        """)
        nullable_links = []
        for source, column, target, nullable in cursor.fetchall():
            if source in keep and target not in keep:
                if not nullable:
                    raise RuntimeError(f"Catalog {source}.{column} requires data from {target}")
                nullable_links.append((source, column))
    clear = sorted(tables - keep)
    print(f"Database={args.database}; clear_tables={len(clear)}; keep_catalog_tables={len(keep)}")
    if not args.apply:
        return

    credentials = []
    for role in roles:
        for index in range(1, 4):
            username = f"qa20261009_{role.lower()}_{index}"
            credentials.append((role, username, secrets.token_urlsafe(22)))
    with args.credentials.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("role", "username", "password"))
        writer.writerows(credentials)

    with transaction.atomic():
        with connection.cursor() as cursor:
            for table in sorted(tables):
                cursor.execute(f"ALTER TABLE [dbo].{quoted(table)} NOCHECK CONSTRAINT ALL")
            for table, column in sorted(set(nullable_links)):
                cursor.execute(f"UPDATE [dbo].{quoted(table)} SET {quoted(column)} = NULL")
            for table in clear:
                cursor.execute(f"DELETE FROM [dbo].{quoted(table)}")
            for table in sorted(tables):
                cursor.execute(f"ALTER TABLE [dbo].{quoted(table)} WITH CHECK CHECK CONSTRAINT ALL")

        for sequence, (role_code, username, password) in enumerate(credentials, 1):
            employee = Employee.objects.create(
                employee_code=f"QA20261009-{sequence:02d}",
                first_name="QA", last_name=f"{role_code} {((sequence - 1) % 3) + 1}",
                full_name=f"QA {role_code} {((sequence - 1) % 3) + 1}",
                date_of_birth=date(1990, 1, 1), gender="Other",
                national_id=f"QA20261009{sequence:010d}",
                company_email=f"{username}@example.invalid",
                mobile_phone="0900000000", join_date=date(2026, 10, 9),
                department=department, position=position,
                employment_status="Active",
            )
            user = User.objects.create_user(
                username=username, password=password, employee=employee,
                email=f"{username}@example.invalid",
                role=Role.objects.get(role_code=role_code),
            )
            user.is_staff = role_code in (SUPER_ADMIN, SYS_ADMIN)
            user.is_superuser = role_code == SUPER_ADMIN
            user.save(update_fields=("is_staff", "is_superuser"))
        if User.objects.count() != 33 or Employee.objects.count() != 33:
            raise RuntimeError("QA account count verification failed")
        if any(User.objects.filter(role__role_code=role).count() != 3 for role in roles):
            raise RuntimeError("QA role distribution verification failed")
        # Give one synthetic department manager an explicit scope for workflow UAT.
        department.manager = User.objects.get(
            username="qa20261009_dept_manager_1"
        ).employee
        department.save(update_fields=("manager",))
    print("RESET_OK users=33 employees=33 roles=11; credentials stored outside Git")


if __name__ == "__main__":
    main()
