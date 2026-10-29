import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from . import tests as mobile_fixtures
from .workspace_schema import NativeSchema


def flatten(blocks):
    for block in blocks:
        yield block
        if block['kind'] == 'form':
            yield from flatten(block['blocks'])
        if block['kind'] == 'table':
            for row in block['rows']:
                yield from flatten(row['blocks'])


@override_settings(MOBILE_API_ENABLED=True, AXES_ENABLED=False)
class WorkspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mobile_fixtures.MobileAPITests.setUpTestData.__func__(cls)

    post = mobile_fixtures.MobileAPITests.post
    login_as = mobile_fixtures.MobileAPITests.login_as

    def run_workspace(self, path, method='GET', fields=(), **extra):
        return self.post('workspace/', {'path': path, 'method': method, 'fields': [list(pair) for pair in fields], **extra})

    def test_bearer_only_and_local_registered_routes(self):
        self.assertEqual(self.run_workspace('/portal/tasks/').status_code, 401)
        self.client.force_login(self.users[0])
        self.assertEqual(self.run_workspace('/portal/tasks/').status_code, 401)
        self.login_as()
        for path in ('https://example.test/', '//example.test/', '/api/mobile/v1/me/', '/media/x.pdf', '/portal/login/', '/portal/../admin/', '/portal/%252e%252e/admin/'):
            self.assertIn(self.run_workspace(path).status_code, (403, 404))
        self.assertEqual(self.run_workspace('/admin/').status_code, 403)
        self.assertEqual(self.run_workspace('/portal/tasks/', 'DELETE').status_code, 400)

    def test_expired_during_request_does_not_raise_session_update_error(self):
        from unittest.mock import patch
        from django.contrib.sessions.backends.base import UpdateError
        self.login_as()
        with patch('django.contrib.sessions.backends.db.SessionStore.save', side_effect=UpdateError):
            self.assertEqual(self.run_workspace('/portal/tasks/').status_code, 401)

    def test_page_contract_preserves_forms_and_drops_csrf_and_executable_content(self):
        self.login_as(2)
        result = self.run_workspace('/portal/tasks/create/')
        self.assertEqual(result.status_code, 200, result.content)
        data = result.json(); self.assertEqual(data['kind'], 'page')
        forms = [block for block in flatten(data['blocks']) if block['kind'] == 'form']
        self.assertTrue(forms)
        names = {field['name'] for form in forms for field in form['fields']}
        self.assertIn('assigned_to_employee', names)
        self.assertIn('task_name', names)
        self.assertNotIn('csrfmiddlewaretoken', names)
        self.assertFalse(result.cookies)
        self.assertEqual(result['Cache-Control'].find('no-store') >= 0, True)

    def test_task_create_update_comment_and_scope_use_original_commands(self):
        from apps.task.models import Task, TaskComment
        from apps.notification.models import Notification
        self.login_as(2)
        fields = [('act_code', '__OTHER__'), ('task_name', 'Native QA task'), ('assigned_to_employee', str(self.people[0].pk)),
                  ('priority', 'Normal'), ('start_date', '2026-10-01')]
        result = self.run_workspace('/portal/tasks/create/', 'POST', fields)
        self.assertEqual(result.status_code, 200, result.content)
        task = Task.objects.get(task_name='Native QA task')
        self.assertEqual(task.assigned_by_employee_id, self.people[2].pk)
        self.assertTrue(Notification.objects.filter(employee=self.people[0], notification_type='task').exists())
        self.login_as(3)
        denied = self.run_workspace(f'/portal/tasks/{task.pk}/', 'POST', [('action', 'update_status'), ('status', 'Done')])
        self.assertEqual(denied.status_code, 200)
        task.refresh_from_db(); self.assertEqual(task.status, 'Todo')
        self.login_as()
        self.assertEqual(self.run_workspace(f'/portal/tasks/{task.pk}/', 'POST', [('action', 'update_status'), ('status', 'InProgress')]).status_code, 200)
        task.refresh_from_db(); self.assertEqual(task.status, 'InProgress')
        self.run_workspace(f'/portal/tasks/{task.pk}/', 'POST', [('action', 'add_comment'), ('comment_text', 'QA native comment')])
        self.assertEqual(TaskComment.objects.get(task=task).employee_id, self.people[0].pk)

    def test_timesheet_post_uses_owner_not_device_identity(self):
        from apps.attendance.models import TimesheetEntry
        self.login_as()
        fields = [('work_date', '2026-10-01'), ('hours', '2.5'), ('task_description', 'QA native timesheet'), ('employee', str(self.people[3].pk))]
        result = self.run_workspace('/portal/timesheet/create/', 'POST', fields)
        self.assertEqual(result.status_code, 200, result.content)
        entry = TimesheetEntry.objects.get(task_description='QA native timesheet')
        self.assertEqual(entry.employee_id, self.people[0].pk)
        self.assertEqual(str(entry.hours), '2.50')
        self.login_as(3)
        self.assertEqual(self.run_workspace(f'/portal/timesheet/{entry.pk}/delete/', 'POST').status_code, 404)
        self.login_as()
        self.assertEqual(self.run_workspace(f'/portal/timesheet/{entry.pk}/delete/', 'POST').status_code, 200)
        self.assertFalse(TimesheetEntry.objects.filter(pk=entry.pk).exists())

    def test_admin_internal_csrf_and_current_actor_permissions(self):
        from apps.security.models import Role
        self.users[2].is_staff = self.users[2].is_superuser = True
        self.users[2].save(update_fields=['is_staff', 'is_superuser'])
        self.client = Client(enforce_csrf_checks=True)
        self.login_as(2)
        path = reverse('admin:security_role_add')
        result = self.run_workspace(path, 'POST', [('role_code', 'NATIVE-QA-ROLE'), ('role_name', 'Native QA role'), ('_save', 'Lưu')])
        self.assertEqual(result.status_code, 200, result.content)
        self.assertTrue(Role.objects.filter(role_code='NATIVE-QA-ROLE').exists())
        data = self.run_workspace(reverse('admin:security_user_change', args=[self.users[0].pk])).json()
        self.assertNotIn(self.users[0].password, json.dumps(data))

    def test_assistant_json_uses_existing_search_and_session_history(self):
        self.login_as()
        result = self.run_workspace('/assistant/api/search/', 'POST', json={'question': 'QA tài liệu không tồn tại'})
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()['kind'], 'json')
        self.assertIn('results', result.json()['data'])
        history = self.run_workspace('/assistant/api/history/').json()['data']
        self.assertEqual(len(history['turns']), 1)
        self.assertEqual(self.run_workspace('/portal/tasks/', 'POST', json={'question': 'x'}).status_code, 400)

    def test_procurement_duplicate_fields_remain_two_distinct_items(self):
        from apps.procurement.models import ProcurementRequest
        self.login_as(2)
        result = self.run_workspace('/portal/procurement/create/', 'POST', [('reason', 'QA native two items'),
            ('item_name', 'QA item A'), ('quantity', '2'), ('estimated_cost', '1000.25'),
            ('item_name', 'QA item B'), ('quantity', '3'), ('estimated_cost', '2000.50')])
        self.assertEqual(result.status_code, 200, result.content)
        row = ProcurementRequest.objects.get(reason='QA native two items')
        self.assertEqual(row.requested_by_id, self.people[2].pk)
        self.assertEqual(row.status, 'Pending')
        self.assertEqual(row.items.count(), 2)
        self.assertEqual(str(row.total_estimated_cost), '8002.00')

    def test_kpi_assignment_and_scoring_preserve_scope_and_decimal(self):
        from apps.kpi.models import EmployeeKPI, KPIPeriod, KPITemplate
        period = KPIPeriod.objects.create(year=2026, month=10)
        template = KPITemplate.objects.create(kpi_name='Native QA KPI')
        self.login_as(2)
        result = self.run_workspace('/portal/kpi/assign/', 'POST', [('employee', str(self.people[0].pk)),
            ('kpi_template', str(template.pk)), ('kpi_period', str(period.pk)), ('target', '10')])
        self.assertEqual(result.status_code, 200, result.content)
        row = EmployeeKPI.objects.get(employee=self.people[0], kpi_template=template)
        self.run_workspace(f'/portal/kpi/score/{row.pk}/update/', 'POST', [('actual', '8.5')])
        row.refresh_from_db(); self.assertEqual(str(row.actual), '8.50'); self.assertEqual(str(row.achievement), '85.00')
        self.login_as(3)
        self.run_workspace(f'/portal/kpi/score/{row.pk}/update/', 'POST', [('actual', '100')])
        row.refresh_from_db(); self.assertEqual(str(row.actual), '8.50')

    def test_finance_period_creation_requires_finance_role(self):
        from apps.payroll.models import PayrollPeriod
        from apps.security.models import Role
        self.login_as()
        self.run_workspace('/portal/finance/periods/create/', 'POST', [('payroll_month', '7'), ('payroll_year', '2026')])
        self.assertFalse(PayrollPeriod.objects.filter(payroll_year=2026, payroll_month=7).exists())
        role, _ = Role.objects.get_or_create(role_code='FINANCE_OFFICER', defaults={'role_name': 'QA finance'})
        self.users[3].role = role; self.users[3].save(update_fields=['role'])
        self.login_as(3)
        result = self.run_workspace('/portal/finance/periods/create/', 'POST', [('payroll_month', '7'), ('payroll_year', '2026')])
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(PayrollPeriod.objects.get(payroll_year=2026, payroll_month=7).status, 'Open')

    def test_multipart_attachment_and_private_download_reauthorize_owner(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.hrm.models import EmployeeProfileChangeRequest
        self.login_as()
        payload = {'path': '/portal/profile/requests/new/', 'method': 'POST',
                   'fields': [['field_name', 'address'], ['new_value', 'QA native attachment']],
                   'uploads': [{'key': 'f0', 'name': 'attachment'}]}
        result = self.client.post('/api/mobile/v1/workspace/', {'payload': json.dumps(payload),
            'f0': SimpleUploadedFile('qa native file.pdf', b'%PDF-1.4\nQA native fixture\n%%EOF', content_type='application/pdf')})
        self.assertEqual(result.status_code, 200)
        item = EmployeeProfileChangeRequest.objects.get(new_value='QA native attachment')
        self.assertTrue(item.attachment)
        url = item.attachment.url
        result = self.run_workspace(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result['X-IHRMS-Document'], '1')
        content = b''.join(result.streaming_content) if result.streaming else result.content
        self.assertTrue(content.startswith(b'%PDF-1.4'))
        self.login_as(3)
        self.assertEqual(self.run_workspace(url).status_code, 404)

    def test_print_export_contains_no_scripts_remote_assets_or_authentication_fields(self):
        self.login_as()
        result = self.run_workspace('/portal/profile/', print=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result['X-IHRMS-Document'], '1')
        html = result.content.decode('utf-8')
        self.assertNotIn('<script', html.lower())
        self.assertNotIn('csrfmiddlewaretoken', html)
        self.assertNotIn('onclick=', html.lower())
        self.assertIn(self.people[0].full_name, html)

    def test_hcns_print_uses_current_post_fields_and_invalid_form_is_editable(self):
        from apps.document.tests_hcns import HCNSFormTests
        self.login_as(2)
        path = reverse('portal:hcns_draft', args=['resignation'])
        fields = HCNSFormTests.data(self, 'resignation', reason='CURRENT NATIVE PRINT QA', action='preview')
        response = self.run_workspace(path, 'POST', list(fields.items()), print=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-IHRMS-Document'], '1')
        self.assertIn('CURRENT NATIVE PRINT QA', response.content.decode('utf-8'))
        invalid = dict(fields, document_date='invalid-date')
        response = self.run_workspace(path, 'POST', list(invalid.items()), print=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['kind'], 'page')
        self.assertTrue(any(block['kind'] == 'notice' for block in flatten(response.json()['blocks'])))


class NativeSchemaTests(TestCase):
    def test_related_admin_link_uses_regular_navigation_instead_of_script_only_popup(self):
        html = '<main id="main-content"><a href="/admin/organization/department/add/?_to_field=id&amp;_popup=1">Thêm</a></main>'
        link = NativeSchema(html, '/admin/', lambda _: True).result()['blocks'][0]
        self.assertEqual(link['path'], '/admin/organization/department/add/?_to_field=id')

    def test_hcns_reference_metadata_and_print_submit_current_form(self):
        html = '''<main id="main-content"><form method="post"><select name="full_name" data-reference="employees" data-reference-key="full_name"><option value="1">QA</option></select>
        <button type="button" id="hcns-print">In / lưu PDF</button></form><script id="hcns-reference-data" type="application/json">{"employees":{"1":{"phone":"QA"}}}</script></main>'''
        form = NativeSchema(html, '/portal/hcns-forms/resignation/', lambda _: True).result()['blocks'][0]
        self.assertEqual(form['references']['employees']['1']['phone'], 'QA')
        self.assertEqual(form['fields'][0]['referenceKey'], 'full_name')
        self.assertEqual(form['actions'][0]['value'], 'preview')
        self.assertTrue(form['actions'][0]['print'])
        self.assertFalse(any(block['kind'] == 'print' for block in form['blocks']))

    def test_disabled_submit_does_not_get_replaced_with_enabled_fallback(self):
        html = '<main id="main-content"><form method="post"><button disabled>Hoàn tất</button></form></main>'
        form = NativeSchema(html, '/portal/', lambda _: True).result()['blocks'][0]
        self.assertEqual(form['actions'], [])

    def test_constant_asset_row_navigation_never_executes_javascript(self):
        html = '''<main id="main-content"><table><tr onclick="window.location='/portal/assets/inventory/1/'"><td>QA</td></tr>
        <tr onclick="window.location='/portal/assets/inventory/2/';alert(1)"><td>Rejected</td></tr></table></main>'''
        rows = NativeSchema(html, '/portal/', lambda value: value.startswith('/portal/')).result()['blocks'][0]['rows']
        self.assertEqual(rows[0]['blocks'][0]['path'], '/portal/assets/inventory/1/')
        self.assertEqual(rows[1]['blocks'], [])

    def test_procurement_repeat_and_disabled_fieldset_contract(self):
        html = '''<main id="main-content"><form method="post"><fieldset disabled><input name="locked" value="secret"><button>Locked</button></fieldset>
        <input name="item_name"><input type="number" name="quantity" value="1"><input type="number" name="estimated_cost">
        <button type="button" id="add-procurement-item">Thêm dòng</button><button name="save" value="1">Lưu</button></form></main>'''
        form = NativeSchema(html, '/portal/procurement/', lambda _: True).result()['blocks'][0]
        self.assertTrue(form['fields'][0]['disabled'])
        self.assertEqual([f['name'] for f in form['repeat']], ['item_name', 'quantity', 'estimated_cost'])
        self.assertEqual([a['label'] for a in form['actions']], ['Lưu'])

    def test_form_contract_types_defaults_options_and_duplicate_names(self):
        html = '''<main id="main-content"><form action="/portal/tasks/create/" method="post">
          <label for="title">Tên công việc</label><input id="title" name="title" value="QA &amp; native" required maxlength="100">
          <input name="csrfmiddlewaretoken" value="SECRET"><input type="password" name="password" value="SECRET">
          <input type="checkbox" name="same" value="one" checked><input type="checkbox" name="same" value="two">
          <select name="choice"><option value="a">A</option><option value="b" selected>B</option></select>
          <textarea name="body">QA &lt;script&gt;</textarea><button name="action" value="save">Lưu</button>
          <script>alert('not native')</script></form></main>'''
        result = NativeSchema(html, '/portal/', lambda _: True).result()
        form = result['blocks'][0]; names = [field['name'] for field in form['fields']]
        self.assertNotIn('csrfmiddlewaretoken', names)
        self.assertEqual(names.count('same'), 2)
        self.assertEqual(form['fields'][0]['value'], 'QA & native')
        self.assertEqual(form['fields'][1]['value'], '')
        self.assertEqual(form['fields'][-2]['value'], 'b')
        self.assertEqual(form['actions'][0]['value'], 'save')
        self.assertNotIn('alert(', json.dumps(result))

    def test_external_javascript_links_and_inline_templates(self):
        html = '''<main id="main-content"><a href="javascript:alert(1)">Bad</a><a href="https://example.test">External</a>
        <form method="post"><input type="hidden" name="items-TOTAL_FORMS" value="0"><div class="empty-form">
        <input name="items-__prefix__-name"></div><button>Lưu</button></form></main>'''
        result = NativeSchema(html, '/portal/tasks/', lambda value: value.startswith('/portal/')).result()
        links = [item for item in result['blocks'] if item['kind'] == 'link']
        self.assertEqual(len(links), 1); self.assertTrue(links[0]['external'])
        form = next(item for item in result['blocks'] if item['kind'] == 'form')
        self.assertEqual(len(form['fields']), 1)
        self.assertEqual(form['templates']['items'][0]['name'], 'items-__prefix__-name')
