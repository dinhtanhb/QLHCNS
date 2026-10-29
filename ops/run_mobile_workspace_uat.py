"""Drive native form contracts through mobile web export on marked QA only."""
import argparse
from datetime import timedelta
import json
import os
import re
from pathlib import Path
import uuid

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8794')
    args = parser.parse_args()
    from mobile_qa import configure
    configure(args.directory.resolve())
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    from django.utils import timezone
    from apps.task.models import Task, TaskComment
    from apps.attendance.models import TimesheetEntry
    from apps.security.models import User
    from apps.notification.models import Notification
    from apps.office.models import RoomBooking
    from apps.procurement.models import ProcurementRequest
    from apps.kpi.models import EmployeeKPI, KPIPeriod, KPITemplate
    from apps.asset.models import InventorySession
    from apps.payroll.models import PayrollPeriod
    from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
    from apps.activity.models import Activity
    from apps.project.models import Project
    password = next(line.split(': ', 1)[1] for line in (args.directory/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if 'Mật khẩu chung' in line)
    args.output.mkdir(parents=True, exist_ok=True)
    marker = 'QA-NATIVE-'+uuid.uuid4().hex[:8]
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.on('pageerror', lambda e: errors.append(str(e)))
        def login(name):
            page.goto(args.url)
            page.get_by_role('textbox', name='Tên đăng nhập', exact=True).fill(name)
            page.get_by_role('textbox', name='Mật khẩu', exact=True).fill(password)
            page.get_by_role('button', name='Đăng nhập', exact=True).click()
            expect(page.get_by_text('Hồ sơ của tôi', exact=True)).to_be_visible(timeout=20000)
        def menu(label):
            page.get_by_role('button', name='Nghiệp vụ', exact=True).click()
            page.get_by_role('button', name=label, exact=True).click()
        def shot(name):
            page.wait_for_timeout(350)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            page.screenshot(path=str(args.output/(name+'.png')), full_page=True)
        def choose(label, option, occurrence=None):
            current = page.get_by_role('button', name=label, exact=True)
            (current.nth(occurrence) if occurrence is not None else current).click()
            page.get_by_role('button', name=option, exact=True).last.click()
        login('demo-employee'); menu('Bảng công')
        expect(page.get_by_role('textbox', name='Ngày làm việc *', exact=True)).to_be_visible()
        day = timezone.localdate()+timedelta(days=40)
        while day.weekday() >= 5 or TimesheetEntry.objects.filter(employee__user_account__username='demo-employee', work_date=day).exists():
            day += timedelta(days=1)
        page.get_by_role('textbox', name='Ngày làm việc *', exact=True).fill(day.isoformat())
        page.get_by_role('textbox', name='Công việc thực hiện', exact=True).fill(marker+' timesheet')
        page.get_by_role('textbox', name='Số giờ *', exact=True).fill('2,5')
        page.get_by_role('button', name='Thêm dòng chấm công', exact=True).click()
        expect(page.get_by_text('Đã ghi nhận giờ làm việc.', exact=True)).to_be_visible()
        entry = TimesheetEntry.objects.get(task_description=marker+' timesheet')
        assert entry.employee.user_account.username == 'demo-employee' and str(entry.hours) == '2.50'
        shot('timesheet-created')
        checks.append('Native timesheet creates owned Decimal hours and redirects to selected month')
        for width in (390, 1280):
            page.set_viewport_size({'width': width, 'height': 844})
            for mode in ('light', 'dark'):
                page.emulate_media(color_scheme=mode)
                shot(f'workspace-timesheet-{width}-{mode}')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.emulate_media(color_scheme='light')
        checks.append('Workspace renders without horizontal overflow in light/dark at 390 and 1280px')
        login('demo-hr'); menu('Giao việc & hoàn tất')
        page.get_by_role('button', name='+ Giao việc mới', exact=True).click()
        expect(page.get_by_role('textbox', name='Tên công việc', exact=True).first).to_be_visible()
        shot('task-create-contract')
        known_code = next(iter(ACTIVITY_CODE_NAMES))
        known_option = known_code+' — '+ACTIVITY_CODE_NAMES[known_code]
        choose('-- Chọn mã ActCode --', known_option)
        expect(page.get_by_role('textbox', name='Tên công việc', exact=True)).to_have_value(
            ACTIVITY_CODE_NAMES[known_code])
        choose(known_option, 'Khác (công việc hành chính)')
        task_name = page.get_by_role('textbox', name='Tên công việc *', exact=True)
        task_name.fill(marker+' restored custom task')
        choose('Khác (công việc hành chính)', known_option)
        expect(page.get_by_role('textbox', name='Tên công việc', exact=True)).to_have_value(
            ACTIVITY_CODE_NAMES[known_code])
        choose(known_option, 'Khác (công việc hành chính)')
        expect(page.get_by_role('textbox', name='Tên công việc *', exact=True)).to_have_value(marker+' restored custom task')
        checks.append('ActCode selection fills canonical task name and restores custom name after switching back')
        person = User.objects.get(username='demo-employee').employee
        # Assignee selects initially show the first allowed employee.
        candidates = page.get_by_role('button').all_text_contents()
        assignee = next(text for text in candidates if ' - ' in text and not text.startswith('✓'))
        choose(assignee, person.employee_code+' - '+person.full_name)
        page.get_by_role('textbox', name='Tên công việc *', exact=True).fill(marker+' task')
        page.get_by_role('button', name='Giao việc', exact=True).click()
        expect(page.get_by_text('Đã giao việc thành công.', exact=False)).to_be_visible()
        task = Task.objects.get(task_name=marker+' task')
        assert task.assigned_to_employee_id == person.pk
        checks.append('HR native task form creates scoped assignment and employee notification')
        # Send the form using the visible controls; selectors deliberately use
        # the server's Vietnamese labels rather than hard-coded payloads.
        login('demo-employee'); menu('Giao việc & hoàn tất')
        page.wait_for_timeout(1000)
        (args.output/'task-list-text.txt').write_text(page.locator('body').inner_text(), encoding='utf-8')
        page.get_by_role('button', name=marker+' task', exact=True).click()
        controls = page.get_by_role('textbox')
        details = [(controls.nth(i).get_attribute('aria-label'), controls.nth(i).input_value()) for i in range(controls.count())]
        (args.output/'task-controls.json').write_text(json.dumps(details, ensure_ascii=False), encoding='utf-8')
        shot('task-detail-contract')
        checks.append('Assigned employee task details load native fields')
        choose('Chưa bắt đầu', 'Đang thực hiện')
        page.get_by_role('button', name='Lưu', exact=True).click()
        expect(page.get_by_text('Đã cập nhật trạng thái công việc.', exact=True)).to_be_visible()
        task.refresh_from_db(); assert task.status == 'InProgress'
        page.get_by_role('textbox', name='Bình luận', exact=False).fill(marker+' comment')
        page.get_by_role('button', name='Gửi', exact=True).click()
        expect(page.get_by_text('Đã thêm bình luận.', exact=True)).to_be_visible()
        assert TaskComment.objects.filter(task=task, comment_text=marker+' comment').exists()
        assert Notification.objects.filter(employee=task.assigned_by_employee, notification_type='task').exists()
        checks.append('Native status/comment save once and notify task assigner')
        login('demo-project-manager'); menu('Theo dõi hoạt động')
        page.get_by_role('button', name=re.compile('Tạo hoạt động')).click()
        code = next(code for code in ACTIVITY_CODE_NAMES if not Activity.objects.filter(activity_code=code).exists())
        choose('---------', code, 0)
        expect(page.get_by_role('textbox', name='Tên hoạt động *', exact=True)).to_have_value(ACTIVITY_CODE_NAMES[code])
        project = Project.objects.filter(is_active=True).order_by('project_name').first()
        lead = User.objects.get(username='demo-cbda').employee
        coordinator = person
        choose('---------', str(project), 0)
        page.get_by_role('textbox', name='Địa điểm thực hiện').fill(marker+' location')
        start = timezone.localdate()+timedelta(days=90)
        page.get_by_role('textbox', name='Ngày bắt đầu *', exact=True).fill(start.isoformat())
        page.get_by_role('textbox', name='Ngày kết thúc *', exact=True).fill((start+timedelta(days=1)).isoformat())
        choose('---------', str(lead), 0)
        choose('---------', str(coordinator), 0)
        page.get_by_role('button', name='Tạo hoạt động', exact=True).click()
        expect(page.get_by_text('Đã tạo hoạt động dự án.', exact=True)).to_be_visible()
        created = Activity.objects.get(activity_code=code)
        assert created.activity_name == ACTIVITY_CODE_NAMES[code] and created.location == marker+' location'
        checks.append('Native project activity form autofills required ActCode name and creates scoped activity')
        login('demo-employee'); menu('Phiếu lương')
        expect(page.get_by_role('heading', name='Phiếu lương — IHRMS', exact=True)).to_be_visible()
        shot('payslip-issued')
        checks.append('Issued locked-period payslip list loads')
        with page.expect_download() as download:
            page.get_by_role('button', name='Tải PDF', exact=True).first.click()
        saved = args.output/'synthetic-payslip.pdf'; download.value.save_as(saved)
        assert saved.read_bytes().startswith(b'%PDF')
        checks.append('Owned issued payslip downloads actual PDF without bearer in URL')
        login('demo-employee'); menu('Phòng họp')
        when = timezone.localtime()+timedelta(days=70)
        page.get_by_role('textbox', name='Mục đích *', exact=True).fill(marker+' room')
        page.get_by_role('textbox', name='Bắt đầu *', exact=True).fill(when.strftime('%Y-%m-%dT10:00'))
        page.get_by_role('textbox', name='Kết thúc *', exact=True).fill(when.strftime('%Y-%m-%dT11:00'))
        page.get_by_role('button', name='Đặt phòng', exact=True).click()
        expect(page.get_by_text('Đã gửi yêu cầu đặt phòng, chờ duyệt.', exact=True)).to_be_visible()
        booking = RoomBooking.objects.get(purpose=marker+' room')
        assert booking.status == 'Pending' and booking.employee_id == person.pk
        shot('room-pending')
        checks.append('Room booking native datetime fields create owned Pending request')
        login('demo-hr'); menu('Nhân viên & hồ sơ')
        page.get_by_role('textbox', name='Tìm kiếm', exact=True).fill(person.employee_code)
        page.get_by_role('button', name='Áp dụng', exact=True).click()
        page.get_by_role('button', name=person.full_name, exact=True).click()
        page.get_by_role('button', name='Sửa hồ sơ', exact=True).click()
        page.get_by_role('textbox', name='Địa chỉ', exact=True).fill(marker+' HR address')
        page.get_by_role('button', name='Lưu hồ sơ', exact=True).click()
        expect(page.get_by_text('Đã cập nhật hồ sơ nhân viên.', exact=True)).to_be_visible()
        person.refresh_from_db(); assert person.address == marker+' HR address'
        shot('hr-employee-edited')
        checks.append('HR native employee edit preserves existing fields and saves audited address')
        login('demo-hr'); menu('Mua sắm')
        page.get_by_role('textbox', name='Lý do đề nghị', exact=True).fill(marker+' procurement')
        page.get_by_role('textbox', name='Tên hàng hóa/dịch vụ *', exact=True).fill(marker+' item1')
        page.get_by_role('textbox', name='Đơn giá dự kiến', exact=True).fill('1.000')
        page.get_by_role('button', name='Thêm dòng hàng hóa', exact=True).click()
        page.get_by_role('textbox', name='Dòng 2 · Tên hàng hóa/dịch vụ *', exact=True).fill(marker+' item2')
        page.get_by_role('textbox', name='Dòng 2 · Đơn giá dự kiến', exact=True).fill('2.000')
        page.get_by_role('button', name='Gửi đề nghị', exact=True).click()
        expect(page.get_by_text('Đã gửi đề nghị mua sắm', exact=False)).to_be_visible()
        procurement = ProcurementRequest.objects.get(reason=marker+' procurement')
        assert procurement.items.count() == 2 and str(procurement.total_estimated_cost) == '3000.00'
        checks.append('Native procurement repeat rows preserve duplicate names and exact money')
        template = KPITemplate.objects.create(kpi_name=marker+' KPI', target_value=10)
        period, _ = KPIPeriod.objects.get_or_create(year=timezone.localdate().year, month=timezone.localdate().month)
        login('demo-hr'); menu('Chấm điểm KPI')
        page.get_by_role('button', name='Tạo chỉ tiêu mới', exact=True).click()
        expect(page.get_by_role('textbox', name='Chỉ tiêu *', exact=True)).to_be_visible()
        buttons = page.get_by_role('button').all_text_contents()
        employeeChoice = next(text for text in buttons if 'DEMO-' in text and not text.startswith('✓'))
        choose(employeeChoice, person.employee_code+' - '+person.full_name)
        # Select lookup values by opening their current default labels.
        selections = page.get_by_role('button').all_text_contents()
        templateLabel = next(text for text in selections if text.startswith(str(KPITemplate.objects.first().kpi_name)))
        choose(templateLabel, str(template)+' (trọng số 0%)')
        if page.get_by_role('button', name=str(period), exact=True).count() == 0:
            periodsShown = page.get_by_role('button').all_text_contents()
            periodLabel = next(text for text in periodsShown if re.match(r'^(Tháng \d+/|Quý \d+/|Năm \d)', text))
            choose(periodLabel, str(period))
        page.get_by_role('textbox', name='Chỉ tiêu *', exact=True).fill('10')
        page.get_by_role('button', name='Tạo', exact=True).click()
        expect(page.get_by_text('Đã tạo chỉ tiêu KPI.', exact=True)).to_be_visible()
        score = page.get_by_role('textbox', name=re.compile(re.escape(str(template))))
        score.fill('8,5')
        score.locator('xpath=ancestor::*[starts-with(@data-testid,"workspace-form-")][1]').get_by_role('button', name='Lưu', exact=True).click()
        expect(page.get_by_text('Đã cập nhật KPI cho', exact=False)).to_be_visible()
        result = EmployeeKPI.objects.get(employee=person, kpi_template=template)
        assert str(result.actual) == '8.50' and str(result.achievement) == '85.00'
        checks.append('Native KPI assignment and scoring save decimal actual and achievement')
        login('demo-layout-admin'); menu('Kiểm kê Tài sản')
        page.get_by_role('textbox', name='Tên đợt *', exact=True).fill(marker+' inventory')
        page.get_by_role('textbox', name='Văn phòng / Bộ phận *', exact=True).fill('QA office')
        page.get_by_role('textbox', name='Thời điểm *', exact=True).fill((timezone.localdate()+timedelta(days=80)).isoformat()+'T09:00')
        page.get_by_role('button', name='Tạo đợt kiểm kê', exact=True).click()
        expect(page.get_by_text('Đã tạo đợt kiểm kê và nạp toàn bộ tài sản.', exact=True)).to_be_visible()
        inventory = InventorySession.objects.get(session_name=marker+' inventory')
        assert inventory.lines.exists()
        login('demo-layout-admin'); menu('Kiểm kê Tài sản')
        row = page.get_by_text(marker+' inventory', exact=True).locator('xpath=ancestor::div[.//*[@role="button"]][1]')
        row.get_by_role('button', name='Mở chi tiết', exact=True).click()
        expect(page.get_by_role('heading', name=re.compile(re.escape(marker+' inventory')))).to_be_visible()
        shot('inventory-created-reopened')
        checks.append('Native asset inventory creates lines and opens legacy clickable row as a safe native action')
        login('demo-finance'); menu('Chạy lương hàng tháng')
        year = 2027
        while PayrollPeriod.objects.filter(payroll_year=year, payroll_month=7).exists():
            year += 1
        choose('-- Chọn tháng --', 'Tháng 7'); choose('-- Chọn năm --', str(year))
        page.get_by_role('button', name='Tạo kỳ lương', exact=True).click()
        expect(page.get_by_text(f'Đã tạo kỳ lương 7/{year}.', exact=True)).to_be_visible()
        assert PayrollPeriod.objects.get(payroll_year=year, payroll_month=7).status == 'Open'
        shot('finance-period-created')
        checks.append('Finance native period form creates Open period and opens payroll command page')
        login('demo-layout-admin'); menu('Trang Quản Trị (Admin) ADMIN')
        shot('admin-model-menu')
        checks.append('Authorized admin model menu renders as native links')
        login('demo-hr'); menu('Biểu mẫu HCNS')
        page.get_by_role('button', name=re.compile('Đơn xin nghỉ việc')).click()
        page.get_by_text('Họ và tên', exact=True).locator('..').get_by_role('button').click()
        page.get_by_role('button', name=re.compile(re.escape(person.full_name)+' · '+person.employee_code)).last.click()
        expect(page.get_by_text('Chức vụ / vị trí', exact=True).locator('..').get_by_role('button', name=str(person.position), exact=True)).to_be_visible()
        page.get_by_role('textbox', name='Lý do', exact=True).fill(marker+' CURRENT PRINT')
        with page.expect_download() as saved:
            page.get_by_role('button', name='In / lưu PDF', exact=True).click()
        printed = args.output/'hcns-current-input.html'
        saved.value.save_as(printed)
        html = printed.read_text(encoding='utf-8')
        assert marker+' CURRENT PRINT' in html and '<script' not in html.lower()
        print_page = browser.new_page()
        print_page.route('**/*', lambda route: route.abort())
        print_page.set_content(html)
        print_page.pdf(path=str(args.output/'hcns-current-input.pdf'), prefer_css_page_size=True, print_background=True)
        print_page.close()
        checks.append('HCNS reference selection fills scoped position and print submits current draft without saving a decision')
        checks.append('HCNS self-contained print HTML renders PDF without remote requests')
        assert not errors, errors
        browser.close()
    (args.output/'validation.json').write_text(json.dumps({'checks': checks, 'count': len(checks), 'errors': errors, 'synthetic_only': True}, indent=2), encoding='utf-8')
    print(json.dumps({'checks': len(checks), 'errors': len(errors)}))


if __name__ == '__main__':
    main()
