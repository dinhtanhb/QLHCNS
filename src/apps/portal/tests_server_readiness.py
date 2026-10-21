from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.test import TestCase, RequestFactory
from django.urls import reverse

from apps.portal import tests as fixtures
from apps.asset.models import Asset, AssetType, AssetDisposalRequest, AssetDisposalItem, AssetDisposalMinutes
from apps.document.models import Document, DocumentCategory, OfficialDispatch, DispatchBook
from apps.payroll.models import EmployeeSalary, PayrollPeriod, Payroll
from apps.security.permissions import has_permission


class ServerReadinessRegressionTests(TestCase):
    setUpTestData = classmethod(fixtures.PortalSensitiveWorkflowTests.setUpTestData.__func__)
    make_employee = fixtures.PortalSensitiveWorkflowTests.make_employee
    make_user = fixtures.PortalSensitiveWorkflowTests.make_user

    def setUp(self):
        self.employee = self.make_employee('SIT-HR')
        self.user = self.make_user('HR_OFFICER', self.employee, 'sit-hr')
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.request = AssetDisposalRequest.objects.create(
            request_no='SIT-REQUEST', request_date=date(2026,10,21), location_name='Synthetic', requested_by=self.employee,
        )
        kind = AssetType.objects.create(asset_type_code='SIT-TYPE', asset_type_name='Synthetic')
        self.asset = Asset.objects.create(asset_code='SIT-ASSET', asset_name='Synthetic', asset_type=kind)

    def test_admin_cannot_forge_disposal_approval(self):
        url = reverse('admin:asset_assetdisposalrequest_change', args=[self.request.pk])
        form = self.client.get(url).context['adminform'].form
        data = {key: form[key].value() for key in form.fields if form[key].value() is not None}
        data.update(status='Approved', _save='Save')
        self.client.post(url, data)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'Pending')
        self.assertNotIn('status', form.fields)

    def test_stale_admin_form_cannot_overwrite_portal_approval(self):
        from types import SimpleNamespace
        request = RequestFactory().post('/admin/')
        request.user = self.user
        stale = AssetDisposalRequest.objects.get(pk=self.request.pk)
        AssetDisposalRequest.objects.filter(pk=stale.pk).update(status='Approved')
        model_admin = admin.site._registry[AssetDisposalRequest]
        with self.assertRaises(ValidationError):
            model_admin.save_model(request, stale, SimpleNamespace(changed_data=['location_name']), True)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'Approved')
        self.assertFalse(model_admin.has_delete_permission(request, stale))

    def test_pending_soft_deleted_workflow_record_can_be_restored(self):
        from types import SimpleNamespace
        request = RequestFactory().post('/admin/')
        request.user = self.user
        stale = AssetDisposalRequest.objects.get(pk=self.request.pk)
        self.request.delete(user=self.user)
        self.assertTrue(admin.site._registry[AssetDisposalRequest].has_delete_permission(request, self.request))
        with self.assertRaises(ValidationError):
            admin.site._registry[AssetDisposalRequest].save_model(request, stale, SimpleNamespace(changed_data=[]), True)

    def test_onboard_candidate_maps_vietnamese_given_and_family_names(self):
        from urllib.parse import urlsplit, parse_qs
        from apps.recruitment.models import Candidate, Offer
        candidate = Candidate.objects.create(candidate_code='SIT-NAME',full_name='Nguyen Van An',phone_number='0000000000',email='synthetic@example.test')
        Offer.objects.create(candidate=candidate,offer_date=date(2026,10,1),expected_join_date=date(2026,10,21),salary_offer=Decimal('10000000'),status='Accepted')
        response = self.client.post(reverse('portal:hr_candidate_onboard',args=[candidate.pk]))
        params = parse_qs(urlsplit(response.url).query)
        self.assertEqual(params['first_name'], ['An'])
        self.assertEqual(params['last_name'], ['Nguyen Van'])

    def test_admin_cannot_approve_document_or_edit_issued_contents(self):
        category = DocumentCategory.objects.create(category_code='SIT', category_name='Synthetic')
        document = Document.objects.create(document_no='SIT', document_name='Synthetic', category=category)
        request = RequestFactory().post('/admin/'); request.user = self.user
        model_admin = admin.site._registry[Document]
        form = model_admin.get_form(request, document)(data={
            'document_no':'SIT', 'document_name':'Synthetic', 'category':category.pk, 'version_no':'1.0', 'status':'Approved',
        }, instance=document)
        self.assertFalse(has_permission(self.user, 'approve_document'))
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
        document.status = 'Approved'; document.save()
        self.assertFalse(model_admin.has_change_permission(request, document))

    def test_shared_dispatch_read_does_not_grant_admin_delete(self):
        manager = self.make_user('DEPT_MANAGER', self.make_employee('SIT-MANAGER'), 'sit-manager')
        manager.is_staff = True; manager.save()
        book = DispatchBook.objects.create(book_code='SIT', book_name='Synthetic', book_type='Incoming', year=2026)
        dispatch = OfficialDispatch.objects.create(
            dispatch_book=book, dispatch_no='SIT', dispatch_type='Incoming', title='Synthetic',
            issue_date=date(2026,10,21), received_or_sent_date=date(2026,10,21),
        )
        self.client.force_login(manager)
        response = self.client.post(reverse('admin:document_officialdispatch_delete', args=[dispatch.pk]), {'post':'yes'})
        self.assertEqual(response.status_code, 403)
        dispatch.refresh_from_db(); self.assertFalse(dispatch.is_deleted)
        request = RequestFactory().get('/admin/'); request.user = manager
        self.assertTrue(admin.site._registry[OfficialDispatch].has_view_permission(request, dispatch))

    def test_approved_request_rejects_added_asset_and_member(self):
        self.request.status = 'Approved'; self.request.save()
        url = reverse('portal:disposal_request_detail', args=[self.request.pk])
        for data in ({'action':'add_item', 'asset':self.asset.pk, 'damage_description':'Synthetic'},
                     {'action':'add_member', 'employee':self.employee.pk}):
            response = self.client.post(url, data, follow=True)
            self.assertContains(response, 'không thể thay đổi nội dung')
        self.assertFalse(self.request.items.exists())
        self.assertFalse(self.request.members.exists())

    def test_disposal_decision_and_execution_persist_once_and_print_remains_visible(self):
        self.request.status = 'Approved'; self.request.save()
        item = AssetDisposalItem.objects.create(request=self.request, asset=self.asset, damage_description='Synthetic')
        AssetDisposalMinutes.objects.create(item=item, decision_date=date(2026,10,21), conclusion='Synthetic')
        director = self.make_employee('SIT-DIRECTOR', position=self.director_position)
        url = reverse('portal:disposal_request_detail', args=[self.request.pk])
        response = self.client.post(url, {'action':'issue_decision', 'decision_no':'SIT-DEC', 'decision_date':'2026-10-21', 'decided_by':director.pk}, follow=True)
        self.assertContains(response, 'Đã ban hành quyết định thanh lý.')
        self.request.refresh_from_db(); self.assertEqual(self.request.decision_no, 'SIT-DEC')
        self.client.post(url, {'action':'issue_decision','decision_no':'REPLACE','decision_date':'2026-10-21','decided_by':director.pk})
        self.request.refresh_from_db(); self.assertEqual(self.request.decision_no, 'SIT-DEC')
        response = self.client.post(url, {'action':'record_execution','execution_datetime':'2026-10-21T09:00','execution_end_time':'10:00'}, follow=True)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'Completed')
        self.assertIsNotNone(self.request.execution_datetime)
        self.assertContains(response, reverse('portal:disposal_execution_print', args=[self.request.pk]))

    def test_disposal_cannot_complete_without_decision_or_issue_without_minutes(self):
        self.request.status = 'Approved'; self.request.save()
        url = reverse('portal:disposal_request_detail', args=[self.request.pk])
        self.client.post(url, {'action':'issue_decision','decision_no':'SIT-DEC','decision_date':'2026-10-21'})
        self.client.post(url, {'action':'record_execution','execution_datetime':'2026-10-21T09:00'})
        self.request.refresh_from_db()
        self.assertIsNone(self.request.decision_no)
        self.assertEqual(self.request.status, 'Approved')

    def test_new_midmonth_hire_uses_join_date_salary(self):
        employee = self.make_employee('SIT-NEW'); employee.join_date=date(2026,10,15); employee.save()
        EmployeeSalary.objects.create(employee=employee,effective_date=date(2026,10,15),current_basic_salary=Decimal('10000000'))
        period = PayrollPeriod.objects.create(payroll_year=2026,payroll_month=10,start_date=date(2026,10,1),end_date=date(2026,10,31))
        finance = self.make_user('FINANCE_OFFICER', self.make_employee('SIT-FIN'), 'sit-finance')
        self.client.force_login(finance)
        self.client.post(reverse('portal:finance_payroll_generate', args=[period.pk]))
        self.assertEqual(Payroll.objects.get(employee=employee,payroll_period=period).basic_salary, Decimal('10000000'))

    def test_impossible_export_dates_return_400(self):
        hr = self.make_user('HR_MANAGER', self.make_employee('SIT-MGR'), 'sit-hr-manager')
        self.client.force_login(hr)
        from apps.portal.views.reports_planning import report_hub_export
        for key in ('from_date','to_date'):
            request = RequestFactory().get('/portal/reports/export/xlsx/', {key:'2026-02-31'})
            request.user = hr
            self.assertEqual(report_hub_export(request,'xlsx').status_code,400)


from apps.activity import tests as activity_fixtures
from django.core.exceptions import ValidationError
from apps.task.models import Task


class CancelledActivityTaskRegressionTests(activity_fixtures.ActivityTestDataMixin, TestCase):
    def test_cancelled_task_cannot_be_reopened_by_save_or_portal(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = activity.tasks.get()
        activity.status = "Cancelled"; activity.save()
        task.refresh_from_db(); self.assertEqual(task.status, "Cancelled")
        task.status = "InProgress"
        with self.assertRaises(ValidationError):
            task.save()
        task.refresh_from_db(); self.assertEqual(task.status, "Cancelled")

    def test_done_task_remains_editable_when_parent_is_cancelled(self):
        activity = self.make_activity(dispatch=self.dispatch)
        task = activity.tasks.get()
        task.status = "Done"; task.report_file = "activity-reports/synthetic.pdf"; task.save()
        activity.status = "Cancelled"; activity.save()
        task.refresh_from_db(); self.assertEqual(task.status, "Done")
        task.description = "Synthetic corrected description"; task.save()
        task.refresh_from_db(); self.assertEqual(task.description, "Synthetic corrected description")
