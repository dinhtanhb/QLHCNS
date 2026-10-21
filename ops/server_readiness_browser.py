"""Additional real-browser regressions, called only by the disposable UAT runner."""
from datetime import date
from decimal import Decimal


def run(login, go, check, capture, accounts, today):
    from django.urls import reverse
    from apps.asset.models import AssetType, Asset, AssetDisposalRequest, AssetDisposalItem
    from apps.document.models import Document, DocumentCategory
    from apps.payroll.models import EmployeeSalary, Payroll, PayrollPeriod
    from apps.hrm.models import Employee

    hr = accounts['HR_OFFICER-linked']
    hr.is_staff = True
    hr.save(update_fields=['is_staff'])
    director = accounts['DIRECTOR-linked'].employee
    kind = AssetType.objects.create(asset_type_code='UAT-SIT', asset_type_name='Synthetic readiness')
    asset = Asset.objects.create(asset_code='UAT-SIT', asset_name='Synthetic readiness asset', asset_type=kind)
    request = AssetDisposalRequest.objects.create(
        request_no='UAT-SIT', request_date=today, location_name='Synthetic readiness',
        requested_by=hr.employee, created_by=hr,
    )
    item = AssetDisposalItem.objects.create(request=request, asset=asset, damage_description='Synthetic damage')
    context, page = login(hr)
    page.goto(page.url.split('/portal/')[0] + reverse('admin:asset_assetdisposalrequest_change', args=[request.pk]), wait_until='networkidle')
    check(page.locator('select[name=status]').count() == 0, 'SIT admin cannot edit disposal approval status')
    context.close()

    context, page = login(accounts['DIRECTOR-linked'])
    go(page, 'portal:disposal_request_detail', args=[request.pk])
    page.locator('form').filter(has=page.locator('[name=action][value=approve]')).locator('button[type=submit]').click()
    page.get_by_role('dialog').wait_for(state='visible')
    with page.expect_navigation(wait_until='networkidle'):
        page.locator('[data-ui-confirm-accept]').click()
    request.refresh_from_db()
    check(request.status == 'Approved', 'SIT director approval persists through browser confirmation')
    context.close()

    context, page = login(hr)
    go(page, 'portal:disposal_request_detail', args=[request.pk])
    form = page.locator('form').filter(has=page.locator('[name=action][value=add_item]'))
    form.locator('[name=asset]').select_option(str(asset.pk))
    form.locator('[name=damage_description]').fill('Synthetic forbidden addition')
    with page.expect_navigation(wait_until='networkidle'):
        form.locator('button[type=submit]').click()
    check(request.items.count() == 1, 'SIT approved contents reject additional assets through browser')
    check('không thể thay đổi nội dung' in page.locator('main').inner_text(), 'SIT approved contents show rejection message')
    page.locator('details').filter(has=page.locator('form[action*="minutes"]')).locator('summary').click()
    form = page.locator('form').filter(has=page.locator('[name=conclusion]'))
    form.locator('[name=decision_date]').fill(today.isoformat())
    form.locator('[name=conclusion]').fill('Synthetic approved disposal')
    form.locator('button[type=submit]').click()
    page.get_by_role('dialog').wait_for(state='visible')
    with page.expect_navigation(wait_until='networkidle'):
        page.locator('[data-ui-confirm-accept]').click()
    asset.refresh_from_db()
    check(asset.status == 'Disposed' and hasattr(AssetDisposalItem.objects.get(pk=item.pk), 'minutes'), 'SIT minutes persist and dispose approved asset')
    form = page.locator('form').filter(has=page.locator('[name=action][value=issue_decision]'))
    form.locator('[name=decision_no]').fill('UAT-SIT-DECISION')
    form.locator('[name=decision_date]').fill(today.isoformat())
    form.locator('[name=decided_by]').select_option(str(director.pk))
    with page.expect_navigation(wait_until='networkidle'):
        form.locator('button[type=submit]').click()
    request.refresh_from_db()
    check(request.decision_no == 'UAT-SIT-DECISION', 'SIT decision number and signer persist from browser')
    form = page.locator('form').filter(has=page.locator('[name=action][value=record_execution]'))
    form.locator('[name=execution_datetime]').fill(today.isoformat() + 'T09:00')
    form.locator('[name=execution_end_time]').fill('10:00')
    with page.expect_navigation(wait_until='networkidle'):
        form.locator('button[type=submit]').click()
    request.refresh_from_db()
    check(request.status == 'Completed' and request.execution_datetime is not None, 'SIT execution completes disposal through browser')
    check(page.locator('a[href="' + reverse('portal:disposal_execution_print', args=[request.pk]) + '"]').count() == 1, 'SIT completed execution print link remains visible')
    capture(page, 'sit-disposal-completed')

    category = DocumentCategory.objects.create(category_code='UAT-SIT', category_name='Synthetic readiness')
    document = Document.objects.create(document_no='UAT-SIT', document_name='Synthetic readiness', category=category)
    page.goto(page.url.split('/portal/')[0] + reverse('admin:document_document_change', args=[document.pk]), wait_until='networkidle')
    check(page.locator('[name=status] option[value=Approved]').count() == 0, 'SIT HR admin cannot select issued document status')
    context.close()

    person = accounts['EMPLOYEE-linked'].employee
    person.join_date = today.replace(day=15)
    person.save(update_fields=['join_date'])
    EmployeeSalary.objects.create(employee=person, effective_date=person.join_date, current_basic_salary=Decimal('10000000'))
    import calendar
    period = PayrollPeriod.objects.create(
        payroll_year=today.year, payroll_month=today.month, start_date=today.replace(day=1),
        end_date=today.replace(day=calendar.monthrange(today.year, today.month)[1]),
    )
    context, page = login(accounts['FINANCE_OFFICER-linked'])
    go(page, 'portal:finance_payroll_run', args=[period.pk])
    form = page.locator('form[action="' + reverse('portal:finance_payroll_generate', args=[period.pk]) + '"]')
    with page.expect_navigation(wait_until='networkidle'):
        form.locator('button[type=submit]').click()
    check(Payroll.objects.filter(employee=person, payroll_period=period, basic_salary=Decimal('10000000')).exists(), 'SIT midmonth hire is included in payroll through browser')
    capture(page, 'sit-midmonth-payroll')
    context.close()

    from apps.hrm.models import EmployeeTransfer
    from apps.hrm.services import apply_due_employee_changes
    from apps.organization.models import Department
    original_department = person.department
    destination = Department.objects.create(
        department_code='UAT-SIT-HR', department_name='Synthetic transfer destination', organization=original_department.organization,
    )
    EmployeeTransfer.objects.create(employee=person, from_department=original_department, to_department=destination, effective_date=date(2020,1,1))
    context, page = login(accounts['HR_MANAGER-linked'])
    go(page, 'portal:hr_employee_edit', args=[person.pk])
    page.locator('[name=department]').select_option(str(original_department.pk))
    with page.expect_navigation(wait_until='networkidle'):
        page.locator('main form button[type=submit]').click()
    person.refresh_from_db()
    check(person.department_id == original_department.pk, 'SIT direct HR correction persists from browser')
    apply_due_employee_changes()
    person.refresh_from_db()
    check(person.department_id == original_department.pk, 'SIT historical transfer no longer overwrites direct correction')
    go(page, 'portal:hr_employee_detail', args=[person.pk])
    capture(page, 'sit-hr-correction')
    context.close()

    from apps.document.models import DispatchBook, OfficialDispatch
    from apps.project.models import Project
    from apps.activity.models import Activity
    book = DispatchBook.objects.create(book_code='UAT-SIT', book_name='Synthetic', book_type='Outgoing', year=today.year)
    dispatch = OfficialDispatch.objects.create(
        dispatch_book=book, dispatch_no='UAT-SIT', dispatch_type='Outgoing', title='Synthetic cancelled activity',
        issue_date=today, received_or_sent_date=today, signer=director,
    )
    project = Project.objects.create(project_code='UAT-SIT', project_name='Synthetic readiness')
    activity = Activity.objects.create(
        activity_code='UAT-SIT', activity_name='Synthetic cancelled activity', project=project,
        lead_cbda=hr.employee, coordinator=director, outgoing_document=dispatch, start_date=today, end_date=today,
    )
    task = activity.tasks.get()
    activity.status = 'Cancelled'
    activity.save()
    context, page = login(hr)
    go(page, 'portal:task_detail', args=[task.pk])
    form = page.locator('form').filter(has=page.locator('[name=action][value=update_status]'))
    form.locator('[name=status]').select_option('InProgress')
    with page.expect_navigation(wait_until='networkidle'):
        form.locator('button[type=submit]').click()
    task.refresh_from_db()
    check(task.status == 'Cancelled', 'SIT browser cannot reopen cancelled activity task')
    check('không thể mở lại' in page.locator('main').inner_text(), 'SIT cancelled task explains rejected transition')
    capture(page, 'sit-cancelled-task')
    context.close()

    from apps.recruitment.models import Candidate, Offer
    candidate = Candidate.objects.create(candidate_code='UAT-SIT', full_name='Nguyen Van An', phone_number='0000000000', email='synthetic@example.test')
    Offer.objects.create(candidate=candidate, offer_date=today, expected_join_date=today, salary_offer=Decimal('10000000'), status='Accepted')
    context, page = login(hr)
    go(page, 'portal:hr_candidate_detail', args=[candidate.pk])
    form = page.locator('form[action="' + reverse('portal:hr_candidate_onboard', args=[candidate.pk]) + '"]')
    form.locator('button[type=submit]').click()
    page.get_by_role('dialog').wait_for(state='visible')
    with page.expect_navigation(wait_until='networkidle'):
        page.locator('[data-ui-confirm-accept]').click()
    check(page.locator('[name=first_name]').input_value() == 'An' and page.locator('[name=last_name]').input_value() == 'Nguyen Van', 'SIT onboarding prefills Vietnamese given and family names correctly')
    candidate.refresh_from_db()
    check(candidate.status == 'Hired', 'SIT onboarding persists candidate status and redirects to employee form')
    capture(page, 'sit-onboarding-prefill')
    context.close()

    manager = accounts['DEPT_MANAGER-linked']
    manager.is_staff = True
    manager.save(update_fields=['is_staff'])
    context, page = login(manager)
    host = page.url.split('/portal/')[0]
    response = page.goto(host + reverse('admin:document_officialdispatch_delete', args=[dispatch.pk]), wait_until='networkidle')
    check(response.status == 403, 'SIT shared dispatch reader cannot open admin delete form')
    dispatch.refresh_from_db()
    check(not dispatch.is_deleted, 'SIT denied admin delete preserves dispatch')
    context.close()

    context, page = login(accounts['HR_MANAGER-linked'])
    host = page.url.split('/portal/')[0]
    response = page.goto(host + '/portal/reports/export/xlsx/?from_date=2026-02-31', wait_until='networkidle')
    check(response.status == 400, 'SIT impossible report date returns validation error in browser')
    context.close()
