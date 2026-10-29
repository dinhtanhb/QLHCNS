"""Populate remaining native-workspace fixtures only in a marked external QA DB."""
import argparse
import calendar
from datetime import date
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    folder = args.directory.resolve()
    root = Path(__file__).resolve().parents[1]
    if folder == root or root in folder.parents:
        parser.error('Synthetic QA must be outside the repository')
    from mobile_qa import configure
    configure(folder)
    from django.utils import timezone
    from apps.security.models import Role, User
    from apps.hrm.models import Employee
    from apps.payroll.models import PayrollPeriod, Payroll, Payslip
    from apps.planning.models import TrainingCourse, TrainingEnrollment
    password = next(line.split(': ', 1)[1] for line in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    for name, code, staff, superuser in [('demo-layout-admin', 'SUPER_ADMIN', True, True), ('demo-sys', 'SYS_ADMIN', True, False),
            ('demo-project-manager', 'PROJECT_MANAGER', True, False), ('demo-project-coordinator', 'PROJECT_COORDINATOR', True, False),
            ('demo-cbda', 'CBDA', True, False), ('demo-unlinked', 'EMPLOYEE', False, False)]:
        role, _ = Role.objects.get_or_create(role_code=code, defaults={'role_name': 'QA '+code})
        if not User.objects.filter(username=name).exists():
            employee = Employee.objects.filter(user_account__isnull=True).first() if name != 'demo-unlinked' else None
            User.objects.create_user(username=name, password=password, role=role, employee=employee, is_staff=staff, is_superuser=superuser)
    today = timezone.localdate()
    year, month = (today.year, today.month-1) if today.month > 1 else (today.year-1, 12)
    period, _ = PayrollPeriod.objects.get_or_create(payroll_year=year, payroll_month=month,
        defaults={'start_date': date(year, month, 1), 'end_date': date(year, month, calendar.monthrange(year, month)[1]), 'status': 'Locked'})
    employee = User.objects.get(username='demo-employee').employee
    payroll, _ = Payroll.objects.get_or_create(payroll_period=period, employee=employee, defaults={'basic_salary': '10000000'})
    Payslip.objects.get_or_create(payroll=payroll)
    course, _ = TrainingCourse.objects.get_or_create(course_code='QA-NATIVE-COURSE', defaults={'course_name': 'Khóa học giả lập native', 'start_date': today, 'end_date': today})
    TrainingEnrollment.objects.get_or_create(course=course, employee=employee)
    from run_layout_alignment_audit import seed_missing_fixtures
    seed_missing_fixtures()
    (folder/'workspace-fixtures.txt').write_text('Synthetic workspace fixtures only; extra accounts share the fixture password in DEMO_ACCOUNTS.txt.\n', encoding='utf-8')
    print('Seeded isolated workspace roles and fixtures; no credentials printed')


if __name__ == '__main__':
    main()
