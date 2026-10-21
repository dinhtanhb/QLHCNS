"""Live Edge UAT on a newly created disposable DB; never uses application data.

Install optional Playwright outside the repository and pass --packages-dir.
Example: python ops/run_browser_uat.py --backend sqlserver --packages-dir TEMP/packages
Both seeded scenarios and records submitted through the UI are synthetic.
"""
import argparse
from hashlib import sha256
from datetime import date, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=('sqlite', 'sqlserver'), required=True)
    parser.add_argument('--packages-dir', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--reproduce-only', action='store_true')
    parser.add_argument('--layout-only', action='store_true', help='Run affected HR flows, KPI clicks and responsive checks; omit the already covered approval/role loop.')
    parser.add_argument('--readiness-only', action='store_true', help='Run only the server-readiness business regressions on a fresh disposable DB.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.stdout.reconfigure(encoding='utf-8')
    sys.path.insert(0, str(root / 'src'))
    if args.packages_dir:
        sys.path.insert(0, str(args.packages_dir.resolve()))
    from playwright.sync_api import sync_playwright

    output = args.output_dir or Path(tempfile.mkdtemp(prefix='ihrms-live-uat-'))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'screenshots').mkdir(exist_ok=True)
    os.environ.update(DJANGO_SETTINGS_MODULE='config.settings', APP_ENV='test',
                      SECRET_KEY=secrets.token_urlsafe(64), DEBUG='False',
                      M365_STORAGE_ENABLED='False', ENABLE_HTTPS_ENFORCEMENT='False')
    # Playwright's sync driver owns an event loop in this parent test process.
    # Fixture writes and ORM assertions are sequential, after completed UI requests,
    # on a disposable DB. This setting never changes application configuration.
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    if args.backend == 'sqlite':
        os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
    import config.settings as cfg
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = str(output / Path(handler['filename']).name)
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection, connections
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.test.runner import DiscoverRunner
    from django.test.testcases import LiveServerThread
    from django.urls import reverse
    from django.utils import timezone
    from apps.organization.models import Organization, Department, Position
    from apps.hrm.models import Employee
    from apps.security.models import User, Role
    from apps.contract.models import Contract, ContractType
    from apps.leave.models import LeaveType, LeaveRequest, LeaveBalance, LeaveApproval
    from apps.planning.models import HeadcountPlan

    database = settings.DATABASES['default']
    database['CONN_MAX_AGE'] = 0
    name = 'test_ihrms_browser_' + uuid.uuid4().hex
    if args.backend == 'sqlserver':
        if connection.vendor != 'microsoft':
            parser.error('SQL Server requested but not configured.')
        with connection.cursor() as cursor:
            cursor.execute('SELECT DB_ID(%s)', [name])
            if cursor.fetchone()[0] is not None:
                raise RuntimeError('Disposable database already exists; refusing reuse.')
        database['TEST'] = {**database.get('TEST', {}), 'NAME': name}
    else:
        database['TEST'] = {**database.get('TEST', {}), 'NAME': str(output / (name + '.sqlite3'))}
    if database['TEST']['NAME'] == database['NAME']:
        raise RuntimeError('Refusing application database.')
    settings.MEDIA_ROOT = str(output / 'media')
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.M365_STORAGE_ENABLED = False
    runner = DiscoverRunner(verbosity=0, interactive=False)
    old_config = runner.setup_databases()
    live = None
    browser_db = None
    report = {'backend': args.backend, 'checks': [], 'screenshots': [],
              'errors': [], 'synthetic_only': True, 'db_destroyed': False}
    password = secrets.token_urlsafe(32)
    today = timezone.localdate()
    report['operational_date'] = today.isoformat()

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        report['checks'].append(label)

    def capture(page, label):
        path = output / 'screenshots' / (label + '.png')
        page.screenshot(path=str(path), full_page=True)
        report['screenshots'].append(path.name)

    try:
        check(connection.settings_dict['NAME'] == database['TEST']['NAME'], 'Fresh isolated DB selected')
        org = Organization.objects.create(organization_code='UAT', organization_name='Trung tâm giả UAT')
        dept = Department.objects.create(department_code='UAT-A', department_name='Phòng thử nghiệm A', organization=org)
        other = Department.objects.create(department_code='UAT-B', department_name='Phòng thử nghiệm B', organization=org)
        missing = Department.objects.create(department_code='UAT-C', department_name='Phòng chưa có kế hoạch', organization=org)
        position = Position.objects.create(position_code='UAT', position_name='Chuyên viên giả')

        def employee(code, status='Active', department=dept, full_name=None):
            return Employee.objects.create(employee_code=code, first_name='Giả', last_name='UAT',
                full_name=full_name or code, date_of_birth=date(1990, 1, 1), gender='Other',
                national_id='SYN-' + sha256(code.encode()).hexdigest()[:12], company_email=code.lower() + '@example.test',
                mobile_phone='0000000000', join_date=date(2020, 1, 1),
                department=department, position=position, employment_status=status)

        accounts = {}
        roles = ('EMPLOYEE', 'DEPT_MANAGER', 'HR_OFFICER', 'HR_MANAGER', 'DIRECTOR',
                 'FINANCE_OFFICER', 'SYS_ADMIN', 'SUPER_ADMIN')
        for role_code in roles:
            role, _ = Role.objects.get_or_create(role_code=role_code, defaults={'role_name': role_code})
            for linked in (True, False):
                label = role_code + ('-linked' if linked else '-unlinked')
                person = employee('UAT-' + label) if linked else None
                if role_code == 'DEPT_MANAGER' and linked:
                    person.managed_departments.add(dept)
                accounts[label] = User.objects.create_user(username=label, password=password, role=role, employee=person)
        accounts['superuser'] = User.objects.create_user(username='uat-superuser', password=password, is_superuser=True, is_staff=True)
        emp_linked = accounts['EMPLOYEE-linked'].employee
        dept_mgr_linked = accounts['DEPT_MANAGER-linked'].employee
        hr_mgr_linked = accounts['HR_MANAGER-linked'].employee
        dir_linked = accounts['DIRECTOR-linked'].employee
        if emp_linked and dept_mgr_linked:
            emp_linked.manager = dept_mgr_linked
            emp_linked.save(update_fields=['manager'])
        if dept_mgr_linked and hr_mgr_linked:
            dept_mgr_linked.manager = hr_mgr_linked
            dept_mgr_linked.save(update_fields=['manager'])
        if hr_mgr_linked and dir_linked:
            hr_mgr_linked.manager = dir_linked
            hr_mgr_linked.save(update_fields=['manager'])
        kind = ContractType.objects.create(contract_type_code='UAT-FIXED', contract_type_name='Hợp đồng thử nghiệm có thời hạn')
        kind2 = ContractType.objects.create(contract_type_code='UAT-OPEN', contract_type_name='Hợp đồng không xác định thời hạn thử nghiệm')
        leave_type = LeaveType.objects.create(leave_type_code='UAT', leave_type_name='Phép năm giả UAT')
        for account in accounts.values():
            if account.employee_id:
                LeaveBalance.objects.create(employee=account.employee, year=today.year, allocated_days=30)

        live = LiveServerThread('127.0.0.1', StaticFilesHandler, port=0)
        live.daemon = True
        live.start()
        live.is_ready.wait(timeout=30)
        if live.error:
            raise live.error
        base = f'http://127.0.0.1:{live.port}'
        def go(page, route, **kwargs):
            response = page.goto(base + reverse(route, **kwargs), wait_until='networkidle')
            check(response.status == 200, 'GET 200: ' + route)
            return response

        with sync_playwright() as pw:
            browser_db = connections['default']
            browser = pw.chromium.launch(channel='msedge', headless=not args.headed)
            def login(account):
                context = browser.new_context(viewport={'width':1440, 'height':1000})
                page = context.new_page()
                page.on('pageerror', lambda error: report['errors'].append(str(error)))
                go(page, 'portal:login')
                page.locator('[name=username]').fill(account.username)
                page.locator('[name=password]').fill(password)
                with page.expect_navigation(wait_until='networkidle'):
                    page.locator('main form button[type=submit]').click()
                check(page.url == base + reverse('portal:dashboard'), 'Real browser login: ' + account.username)
                return context, page

            if args.readiness_only:
                from server_readiness_browser import run as run_server_readiness
                run_server_readiness(login, go, check, capture, accounts, today)
                check(not report['errors'], 'No uncaught browser JavaScript errors')
                browser.close()
                return 0

            context, page = login(accounts['HR_MANAGER-linked'])
            check(page.locator('#dashboard-contract-types').count() == 0, 'Empty contract distribution is hidden without a zero card')
            check('Chưa nhập kế hoạch' in page.locator('#dashboard-headcount').inner_text(), 'Missing plan not silently zero')
            capture(page, 'dashboard-empty')

            # Registration is a UI POST with genuine CSRF, then contract creation.
            go(page, 'portal:hr_employee_create')
            long_name = 'QA SUPER_ADMIN Nhân viên thử nghiệm tên dài để kiểm tra bố cục'
            fields = dict(employee_code='UAT-UI-NEW', first_name='Giả', last_name='UAT',
                          full_name=long_name, date_of_birth='1990-01-01', national_id='SYN-UI-NEW',
                          company_email='uat-ui-new@example.test', mobile_phone='0000000000', join_date=today.isoformat())
            for key, value in fields.items():
                page.locator('[name=' + key + ']').fill(value)
            page.locator('[name=gender]').select_option('Other')
            page.locator('[name=department]').select_option(str(dept.pk))
            page.locator('[name=position]').select_option(str(position.pk))
            with page.expect_navigation(wait_until='networkidle'):
                page.locator('main form button[type=submit]').click()
            person = Employee.objects.get(employee_code='UAT-UI-NEW')
            check(person.full_name == long_name, 'Employee created through UI and persisted')
            go(page, 'portal:hr_employee_list')
            check('UAT-UI-NEW' not in page.locator('main').inner_text(), 'Uncontracted profile excluded from directory')
            go(page, 'portal:hr_contract_create')
            page.locator('[name=employee]').select_option(str(person.pk))
            page.locator('[name=contract_type]').select_option(str(kind.pk))
            page.locator('[name=contract_no]').fill('UAT-UI-1-26/HĐLĐ-VH')
            page.locator('[name=start_date]').fill(today.isoformat())
            page.locator('[name=end_date]').fill((today + timedelta(days=15)).isoformat())
            page.locator('.ui-number-display').fill('5.000.000')
            page.locator('[name=status]').select_option('Active')
            with page.expect_navigation(wait_until='networkidle'):
                page.locator('main form button[type=submit]').click()
            contract = Contract.objects.get(contract_no='UAT-UI-1-26/HĐLĐ-VH')
            check(contract.basic_salary == Decimal('5000000'), 'Vietnamese input persisted as canonical numeric value')
            check(page.url == base + reverse('portal:hr_contract_list'), 'Contract creation redirects to list')
            capture(page, 'contract-after-create')
            link = page.locator('tbody a').filter(has_text='UAT-UI-NEW').first
            within = link.evaluate('(a)=>{const x=a.getBoundingClientRect(), c=a.closest("td").getBoundingClientRect();return x.left>=c.left&&x.right<=c.right+1}')
            check(within, 'Long employee contract link stays inside its table cell')
            if args.reproduce_only:
                return 0
            link.click()
            check(page.url.endswith(reverse('portal:hr_employee_detail', args=[person.pk])), 'Contract employee link opens correct profile')
            go(page, 'portal:hr_employee_list')
            page.locator('main [name=q]').fill('UAT-UI-NEW')
            with page.expect_navigation(wait_until='networkidle'):
                page.get_by_role('button', name='Áp dụng', exact=True).click()
            check(page.locator('tbody tr').count() == 1, 'Contracted employee found by search')
            button = page.locator('button[popovertarget]')
            button.focus(); page.keyboard.press('Enter')
            menu = page.locator('[popover]:popover-open')
            check(menu.count() == 1, 'Employee dropdown opens with keyboard')
            page.keyboard.press('Escape')
            check(menu.count() == 0 and button.evaluate('(x)=>x===document.activeElement'), 'Dropdown closes and restores focus')
            page.locator('button[popovertarget]').click()
            page.get_by_role('link', name='Sửa hồ sơ', exact=True).click()
            page.locator('[name=full_name]').fill(long_name + ' đã sửa')
            with page.expect_navigation(wait_until='networkidle'):
                page.locator('main form button[type=submit]').click()
            person.refresh_from_db()
            check(person.full_name.endswith('đã sửa'), 'Profile edit through dropdown persisted')

            # Independent fixture boundaries from the approved phase-one spec.
            employee('UAT-PROBATION', 'Probation')
            employee('UAT-ONLEAVE', 'OnLeave')
            employee('UAT-RESIGNED', 'Resigned')
            employee('UAT-OTHER', department=other)
            deleted = employee('UAT-DELETED'); deleted.delete()
            seed_person = accounts['EMPLOYEE-linked'].employee
            for i, end in enumerate((0, 7, 30, 60, 61, -1, None)):
                Contract.objects.create(employee=seed_person, contract_type=kind if i%2 == 0 else kind2,
                    contract_no=f'UAT-BOUND-{i}', start_date=today-timedelta(days=90),
                    end_date=today+timedelta(days=end) if end is not None else None, basic_salary=100, status='Active')
            for status in ('Draft', 'Expired', 'Terminated'):
                Contract.objects.create(employee=seed_person, contract_type=kind, contract_no='UAT-'+status,
                    start_date=today-timedelta(days=90), end_date=today+timedelta(days=7), basic_salary=100, status=status)
            Contract.objects.create(employee=seed_person, contract_type=kind, contract_no='UAT-FUTURE',
                start_date=today+timedelta(days=1), end_date=today+timedelta(days=10), basic_salary=100, status='Active')
            for i in range(2):
                LeaveRequest.objects.create(employee=seed_person, leave_type=leave_type, from_date=today,
                    to_date=today, status='Approved', reason='Giả UAT chỉ dùng kiểm thử')
            HeadcountPlan.objects.create(year=today.year, department=dept, planned_headcount=2)
            HeadcountPlan.objects.create(year=today.year, department=other, planned_headcount=0)
            statuses = list(Contract.objects.values_list('pk','status','end_date'))
            go(page, 'portal:dashboard')
            values = page.locator('#dashboard-status .ui-kpi-value').all_text_contents()
            check([x.strip() for x in values] == ['12','1','5','0'], 'Grouped main managed/approved/upcoming/queue counts match fixed fixture')
            check('Đang làm 10 · Thử việc 1 · Nghỉ dài hạn 1' in page.locator('#dashboard-status').inner_text(), 'Status breakdown remains visible without duplicate cards')
            check(values[2].strip() == '5' and page.locator('#dashboard-contracts .home-contracts>li').count() == 5, 'D to D+60 inclusive count retained; HR preview shows five rows')
            check('Quá hạn cần rà soát · 1' in page.locator('#dashboard-contracts').inner_text(), 'Overdue separate from upcoming')
            check(page.locator('.dashboard-donut-total strong').inner_text() == '7' and page.locator('.dashboard-donut-total span').inner_text() == 'hợp đồng', 'Effective contracts count contracts, not employees')
            check(page.locator('.home-type-list li').count() == 2, 'Two contract types have directly labelled tracks plus data table')
            check(any(value.strip().endswith('/ 0') for value in page.locator('.home-capacity-value').all_text_contents()) and 'Chưa nhập kế hoạch' in page.locator('#dashboard-headcount').inner_text(), 'Explicit zero plan and missing plan are distinct')
            page.locator('#dashboard-headcount summary').click()
            check('450' in page.locator('#dashboard-headcount').inner_text(), 'Over-plan ratio retained above 100 percent')
            page.locator('#dashboard-headcount summary').click()
            check(statuses == list(Contract.objects.values_list('pk','status','end_date')), 'Dashboard GET never changes contract statuses/dates')
            all_links = page.locator('#dashboard-status a.home-main-metric').evaluate_all('(xs)=>xs.map(a=>a.getAttribute("href"))')
            links = [href for href in all_links if href.startswith(reverse('portal:dashboard_people'))]
            check(len(links) == 2 and len(all_links) == 4, 'Managed/approved exact person drilldowns, contract list, and approval queue link retained')
            for href, expected in zip(links, (12, 1)):
                go(page, 'portal:dashboard')
                with page.expect_navigation(wait_until='networkidle') as navigation:
                    page.locator(f'#dashboard-status a.home-main-metric[href="{href}"]').click()
                check(navigation.value.status == 200 and page.locator('.ui-results-count').inner_text() == f'Có {expected} người phù hợp.', 'KPI destination equals displayed count: ' + href)
                check(page.locator('tbody tr').count() == expected, 'KPI detail rows match count')
            go(page, 'portal:dashboard')

            for width in (1920, 1440, 1024, 768, 360):
                page.set_viewport_size({'width':width, 'height':1000})
                for theme in ('light','dark'):
                    page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;localStorage.setItem("ihrms-theme",theme)}', theme)
                    for route, label in (('portal:dashboard','dashboard'),('portal:hr_contract_list','contracts'),('portal:hr_employee_list','employees')):
                        go(page, route)
                        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), f'{label} no page overflow {width} {theme}')
                        if label == 'contracts':
                            check(page.locator('tbody a').evaluate_all('(xs)=>xs.every(a=>{const x=a.getBoundingClientRect(),c=a.closest("td").getBoundingClientRect();return x.right<=c.right+1})'), f'All contract names bounded {width} {theme}')
                        if label == 'dashboard':
                            check(page.locator('#dashboard-status a.home-main-metric').count() == 4, f'Four clickable main metric links {width} {theme}')
                            if width >= 1440:
                                cards=page.locator('.home-row').first.locator(':scope > section').evaluate_all('(xs)=>xs.map(x=>x.getBoundingClientRect().width)')
                        # Atoms reference gives the department chart more width;
                        # the current approved layout is 60:40, with aligned cards.
                            check(len(cards)==2 and abs(cards[0]-1.5*cards[1])<=2,
                                  f'Dashboard chart width ratio 60:40 {width} {theme}')
                        capture(page, f'{label}-{width}-{theme}')
            context.close()

            if args.layout_only:
                check(not report['errors'], 'No uncaught browser JavaScript errors')
                browser.close()
                return 0

            # Actual leave submission -> scoped dashboard queue -> confirmation -> approval.
            context, page = login(accounts['EMPLOYEE-linked'])
            future = today+timedelta(days=8)
            while future.weekday() > 4:
                future += timedelta(days=1)
            go(page, 'portal:leave_create')
            page.locator('[name=leave_type]').select_option(str(leave_type.pk))
            page.locator('[name=from_date]').fill(future.isoformat())
            page.locator('[name=to_date]').fill(future.isoformat())
            page.locator('[name=reason]').fill('UAT-UI-LEAVE')
            with page.expect_navigation(wait_until='networkidle'):
                page.get_by_role('button', name='Gửi đơn', exact=True).click()
            request = LeaveRequest.objects.get(reason='UAT-UI-LEAVE')
            check(request.status == 'Pending' and request.total_days == 1, 'Leave UI submission uses business day calculation')
            context.close()
            context, page = login(accounts['HR_MANAGER-linked'])
            check(page.locator('#dashboard-queue strong').inner_text() == '1', 'Dashboard queue agrees with submitted pending leave')
            page.locator('#dashboard-queue a').click()
            row = page.locator('tbody tr').filter(has_text='UAT-UI-LEAVE')
            check(row.count() == 1, 'Queue drill-down contains exactly requested leave')
            row.get_by_role('button', name='Duyệt', exact=True).click()
            page.get_by_role('dialog').wait_for(state='visible')
            with page.expect_navigation(wait_until='networkidle'):
                page.locator('[data-ui-confirm-accept]').click()
            request.refresh_from_db()
            check(request.status == 'Approved' and LeaveApproval.objects.filter(leave_request=request).count() == 1, 'Confirmed UI approval persists once')
            go(page, 'portal:dashboard')
            check(page.locator('#dashboard-queue strong').count() == 0 and 'Không có việc cần xử lý hôm nay' in page.locator('#dashboard-queue').inner_text(), 'Queue updates to compact empty state after approval')
            context.close()

            for label, account in accounts.items():
                context, page = login(account)
                role = account.role.role_code if account.role_id else 'superuser'
                linked = bool(account.employee_id)
                check(page.locator('#dashboard-contracts').count() == int(role in ('HR_MANAGER','HR_OFFICER','superuser')), label+' contract gate')
                check(page.locator('#dashboard-headcount').count() == int(role in ('HR_MANAGER','DIRECTOR','superuser')), label+' headcount gate')
                check(page.locator('#dashboard-status').count() == int(role in ('HR_MANAGER','HR_OFFICER','DIRECTOR','superuser') or role=='DEPT_MANAGER' and linked), label+' status gate')
                check(page.locator('#profile-warning-title').count() == int(not linked), label+' profile guard')
                text = page.locator('.home-dashboard').inner_text()
                check(all(word not in text for word in ('Tổng Gross','Quỹ lương','Phụ cấp kỳ lương','5.000.000')), label+' no dashboard money')
                if role == 'DEPT_MANAGER' and linked:
                    check('Phòng ban đang quản lý' in text, 'Department manager scope explicit')
                # All rendered dashboard links must reach a readable page for this account.
                links = page.locator('.home-dashboard a[href]').evaluate_all('(xs)=>[...new Set(xs.map(a=>a.getAttribute("href")))]')
                for href in links:
                    response = page.goto(base + href, wait_until='networkidle')
                    check(response.status == 200 and not page.url.endswith(reverse('portal:login')), label+' dashboard destination '+href)
                context.close()
            from server_readiness_browser import run as run_server_readiness
            run_server_readiness(login, go, check, capture, accounts, today)
            check(not report['errors'], 'No uncaught browser JavaScript errors')
            browser.close()
    except Exception as exc:
        report['errors'].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if live:
            live.terminate()
        if browser_db:
            browser_db.close()
        connections.close_all()
        runner.teardown_databases(old_config)
        report['db_destroyed'] = True
        (output / 'browser-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'checks':len(report['checks']), 'screenshots':len(report['screenshots']),
                          'db_destroyed':report['db_destroyed'], 'output':str(output)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
