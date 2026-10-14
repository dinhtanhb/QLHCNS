"""Administration UI contracts; genuine role guards and synthetic-only records."""
from datetime import date
from pathlib import Path
import re
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.portal.test_home_dashboard import HomeDashboardTests
from apps.portal.test_personal_ui import Forms
from apps.portal.ui_test_helpers import assert_internal_links
from apps.asset.models import InventorySession, AssetDisposalRequest
from apps.document.models import DispatchBook, OfficialDispatch


TEMPLATES = ('asset_admin_list','asset_list','dispatch_create','dispatch_detail','dispatch_list',
    'disposal_request_detail','disposal_request_form','disposal_request_list','document_approval_list',
    'document_list','event_list','inventory_session_detail','inventory_session_list','office_incoming_list',
    'office_outgoing_list','procurement_request_list','room_booking_approval_list','room_booking_list',
    'supply_request_approval_list','supply_request_list','vehicle_booking_approval_list','vehicle_booking_list')


class AdministrationUITests(TestCase):
    user = HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        HomeDashboardTests.setUpTestData.__func__(cls)
        cls.session=InventorySession.objects.create(session_name='ADMIN-TEST',office_name='Văn phòng giả',inventory_datetime=timezone.now())
        cls.book=DispatchBook.objects.create(book_code='ADMIN-TEST',book_name='Sổ giả',book_type='Incoming',year=2026)

    def test_templates_use_shared_presentations_and_keep_post_csrf(self):
        root=Path(__file__).parent/'templates/portal'
        for stem in TEMPLATES:
            text=(root/(stem+'.html')).read_text(encoding='utf-8')
            with self.subTest(template=stem):
                self.assertIn('portal/administration_base.html',text)
                self.assertNotIn('class=""',text)
                self.assertNotIn('style="',text)
                self.assertNotRegex(text,r'[\U0001f300-\U0001faff\u2600-\u27ff]')
                self.assertNotRegex(text,r'class="[^"]*\b(?:px-\d|py-\d|text-xs|text-sm|bg-gray-|grid-cols-|space-y-)')
                for form in re.findall(r'<form\b.*?</form>',text,re.S):
                    if 'method="post"' in form:self.assertIn('{% csrf_token %}',form)
                if '<table' in text:
                    self.assertIn('ui-table',text)
                    self.assertIn('<caption',text)
                    self.assertIn('scope="col"',text)

    def test_roles_links_and_csrf_keep_existing_denials_explicit(self):
        # These eight pre-existing navigation denials were reproduced BEFORE this UI change.
        # Permission changes require a separate project-owner decision.
        for code in ('EMPLOYEE','DEPT_MANAGER','HR_OFFICER','HR_MANAGER','DIRECTOR','FINANCE_OFFICER','SYS_ADMIN'):
            user=self.user(code,True);self.client.force_login(user)
            disposal=AssetDisposalRequest.objects.create(request_no='ADMIN-'+code,request_date=date(2026,10,1),location_name='Văn phòng giả',requested_by=user.employee)
            dispatch=OfficialDispatch.objects.create(dispatch_no='ADMIN-'+code,dispatch_type='Incoming',dispatch_book=self.book,title='Công văn giả',issuing_organization='Tổ chức giả',issue_date=date(2026,10,1),received_or_sent_date=date(2026,10,1),assigned_to=user.employee,department=self.department)
            names=[n for n in TEMPLATES if n not in ('office_incoming_list','office_outgoing_list','disposal_request_form','dispatch_detail','disposal_request_detail','inventory_session_detail')]
            routes=[reverse('portal:'+n) for n in names]+[reverse('portal:disposal_request_create'),reverse('portal:dispatch_detail',args=[dispatch.pk]),reverse('portal:disposal_request_detail',args=[disposal.pk]),reverse('portal:inventory_session_detail',args=[self.session.pk])]
            known={}
            if code in ('EMPLOYEE','DEPT_MANAGER'):
                known={f'/reports/export/dispatches/?type={kind}':403 for kind in ('Incoming','Outgoing')}
            for url in routes:
                with self.subTest(role=code,url=url):
                    response=self.client.get(url)
                    self.assertIn(response.status_code,(200,302))
                    if response.status_code!=200:continue
                    assert_internal_links(self,response,known_denials=known)
                    for form in Forms(response.content.decode()).forms:
                        if form['attrs'].get('method','').lower()=='post':
                            self.assertTrue(any(x.get('name')=='csrfmiddlewaretoken' for x in form['fields']))

    def test_dispatch_print_is_separate_from_screen_components(self):
        root=Path(__file__).parent/'templates/portal'
        screen=(root/'dispatch_list.html').read_text(encoding='utf-8')
        self.assertIn('ui-screen-only',screen)
        self.assertIn('portal/dispatch_register_print.html',screen)
        paper=(root/'dispatch_register_print.html').read_text(encoding='utf-8')
        self.assertNotIn('class="ui-table',paper)
        self.assertNotIn('ui-query-bar',paper)

    def test_booking_approval_controls_keep_submitter_values_and_confirmation(self):
        from django.template.loader import render_to_string
        from types import SimpleNamespace
        html=render_to_string('portal/_office_booking_approvals.html',{'page_title':'Duyệt phòng','approve_url_name':'portal:room_booking_approve','resource_kind':'room','bookings':[SimpleNamespace(pk=1,employee='Người giả',room='Phòng giả',start_time=timezone.now(),end_time=timezone.now(),purpose='Họp giả')]})
        form=Forms(html).forms[0]
        self.assertEqual(form['attrs']['method'],'post')
        self.assertIn('data-ui-confirm',form['attrs'])
        self.assertEqual({b.get('value') for b in form['buttons']},{'Approved','Rejected'})
        self.assertTrue(all(b.get('name')=='decision' for b in form['buttons']))
