"""Regression cases from the 2026-10-31 document-assistant review."""
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from . import nlp, services, views, tests_db_search as db_tests
from .db_search import search_database
from .models import SearchQueryLog
from .m365_search import search_sharepoint
from .tests_m365_search import _FakeClient, _hit, SITE, HR, ASSISTANT_SETTINGS


class ParserReviewTests(SimpleTestCase):
    def test_current_period_boundaries_and_consumed_keywords(self):
        for today in (date(2026, 1, 1), date(2026, 12, 31), date(2026, 5, 1),
                      date(2026, 5, 31), date(2024, 2, 29), date(2026, 9, 1)):
            for phrase in ('tháng này', 'tuần này', 'hôm nay'):
                with self.subTest(today=today, phrase=phrase):
                    p = nlp.parse('Quyết định '+phrase, today=today)
                    if phrase == 'tháng này':
                        start = today.replace(day=1)
                        end = nlp._last_day_of_month(today.year, today.month)
                    elif phrase == 'tuần này':
                        start = today-timedelta(days=today.weekday())
                        end = start+timedelta(days=6)
                    else:
                        start = end = today
                    self.assertEqual((p.date_from, p.date_to), (start, end))
                    self.assertEqual(p.keywords, [])

    def test_previous_periods_and_numeric_month_stay_compatible(self):
        today = date(2026, 1, 1)
        self.assertEqual(nlp.parse('tuần trước', today).date_from, today-timedelta(days=7))
        self.assertEqual(nlp.parse('tuần trước', today).date_to, today)
        self.assertEqual(nlp.parse('tháng trước', today).date_to, date(2025, 12, 31))
        self.assertEqual(nlp.parse('tháng 9', today).date_from, date(2026, 9, 1))

    def test_all_types_nonoverlap_legacy_first_and_recruitment_qualifier(self):
        p = nlp.parse('công văn về tài sản mua sắm')
        self.assertEqual(p.doc_types, ['asset', 'dispatch'])
        self.assertEqual(p.doc_type, p.doc_types[0])
        self.assertEqual(p.keywords, ['mua', 'sam'])
        self.assertEqual(nlp.parse('công văn đến').doc_types, ['Incoming'])
        self.assertEqual(nlp.parse('văn bản chỉ đạo nội bộ').doc_types, ['InternalDirective'])
        self.assertEqual(nlp.parse('công văn công văn').doc_types, ['dispatch'])
        p = nlp.parse('quyết định tuyển dụng')
        self.assertEqual(p.doc_types, ['personnel_decision'])
        self.assertEqual(p.keywords, ['tuyen', 'dung'])


class SearchReviewTests(TestCase):
    user = db_tests.DbSearchTests.user

    @classmethod
    def setUpTestData(cls):
        db_tests.DbSearchTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.graph_guard = patch('apps.assistant.m365_search.get_graph_client', side_effect=AssertionError('No real Graph in tests'))
        self.graph_guard.start()
        self.addCleanup(self.graph_guard.stop)

    def test_this_month_service_filters_dates_not_word_thang(self):
        from apps.document.models import PersonnelDecision
        self.decision.decision_date = date(2024, 2, 29)
        self.decision.save(update_fields=['decision_date'])
        other = PersonnelDecision.objects.create(employee=self.emp.employee, template_slug='bo-nhiem',
                    decision_no='QA-tháng-ngoài-kỳ', decision_date=date(2024, 1, 31), status='Issued')
        real_parse = nlp.parse
        with patch('apps.assistant.services.nlp.parse', side_effect=lambda q: real_parse(q, date(2024, 2, 29))):
            response = services.ask('Quyết định tháng này', self.hr)
        self.assertEqual([r['url'] for r in response['results']], [reverse('portal:personnel_decision_detail', args=[self.decision.pk])])
        self.assertNotIn(reverse('portal:personnel_decision_detail', args=[other.pk]), [r['url'] for r in response['results']])

    def test_multi_type_search_keeps_dispatch_when_asset_permission_denied(self):
        from apps.asset.models import Asset, AssetType
        kind = AssetType.objects.create(asset_type_code='QA', asset_type_name='QA')
        Asset.objects.create(asset_code='QA-asset', asset_name='Máy tính mua sắm', asset_type=kind)
        self.dispatch.title = 'Công văn mua sắm'
        self.dispatch.save(update_fields=['title'])
        for permitted in (False, True):
            with self.subTest(permitted=permitted), patch('apps.assistant.db_search.has_permission', return_value=permitted):
                result = search_database(nlp.parse('công văn về tài sản mua sắm'), self.emp)
            types = {r['type'] for r in result}
            self.assertIn('official_dispatch', types)
            self.assertEqual('asset' in types, permitted)
        response = services.ask('công văn tài sản mua sắm', self.emp)
        self.assertEqual(response['parsed']['doc_types'], ['asset', 'dispatch'])
        self.assertEqual(SearchQueryLog.objects.get().parsed_filters['doc_types'], ['asset', 'dispatch'])

    def test_single_type_legacy_constructed_query_matches_parser(self):
        from dataclasses import replace
        p = nlp.parse('công văn nghỉ phép')
        self.assertEqual(search_database(p, self.emp), search_database(replace(p, doc_types=[]), self.emp))

    def test_overlapping_dispatch_types_deduplicate_but_same_named_leaves_do_not(self):
        from apps.leave.models import LeaveRequest, LeaveType
        kind = LeaveType.objects.create(leave_type_code='QA-duplicate', leave_type_name='QA')
        for day in (1, 2):
            LeaveRequest.objects.create(employee=self.emp.employee, leave_type=kind,
                from_date=date(2026, 9, day), to_date=date(2026, 9, day), total_days=1)
        rows = search_database(nlp.parse('công văn công văn đến đơn nghỉ phép'), self.emp)
        dispatches = [row['url'] for row in rows if row['type'] == 'official_dispatch']
        self.assertEqual(len(dispatches), len(set(dispatches)))
        self.assertEqual(len([row for row in rows if row['type'] == 'leave']), 2)

    def test_sharepoint_only_unavailable_has_accurate_empty_notice(self):
        for status in ('not_configured', 'unavailable', None):
            with self.subTest(status=status), patch('apps.assistant.services.m365_search.search_sharepoint', return_value=([], status)):
                response = services.ask('báo cáo hoạt động', self.emp)
            self.assertEqual(bool(response.get('empty_notice')), status is not None)
            if status:
                self.assertIn('SharePoint', response['empty_notice'])
        with patch('apps.assistant.services.m365_search.search_sharepoint', return_value=([], 'not_configured')):
            self.assertNotIn('empty_notice', services.ask('công văn báo cáo hoạt động không-khớp', self.emp))

    def test_list_links_explicit_when_portal_has_no_get_filter(self):
        from apps.asset.models import Asset, AssetType
        from apps.leave.models import LeaveRequest, LeaveType
        asset_type = AssetType.objects.create(asset_type_code='QA-list', asset_type_name='QA')
        Asset.objects.create(asset_code='QA/A&B', asset_name='QA <Máy>', asset_type=asset_type)
        leave_type = LeaveType.objects.create(leave_type_code='QA-list', leave_type_name='QA')
        LeaveRequest.objects.create(employee=self.emp.employee, leave_type=leave_type, from_date=date(2026, 9, 1), to_date=date(2026, 9, 1), total_days=1, reason='QA')
        for query, route in [('tài liệu', 'portal:document_list'), ('đơn nghỉ phép', 'portal:leave_list'), ('tài sản', 'portal:asset_admin_list')]:
            with self.subTest(query=query), patch('apps.assistant.db_search.has_permission', return_value=True):
                rows = search_database(nlp.parse(query), self.emp)
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(row['url'], reverse(route))
                self.assertIn('mở danh sách', row['meta'])
                self.assertNotIn('&', row['url'])


@override_settings(**ASSISTANT_SETTINGS)
class MultiSharePointReviewTests(SimpleTestCase):
    def test_multiple_types_search_each_allowed_root(self):
        hit = _hit('mua sam.pdf', SITE+'/CongVanDen/mua-sam.pdf')
        client = _FakeClient(search=[hit])
        with patch('apps.assistant.m365_search.get_graph_client', return_value=client):
            result = search_sharepoint(nlp.parse('công văn về tài sản mua sắm'), HR)
        self.assertEqual([row['url'] for row in result.results], [hit['web_url']])

    def test_multi_type_partial_status_and_urls_are_preserved(self):
        from .m365_search import SharePointSearchResult
        row = {'url': SITE+'/CongVanDen/test.pdf', 'score': 10}
        with patch('apps.assistant.m365_search._search_sharepoint_single', side_effect=[
            SharePointSearchResult([], 'restricted'), SharePointSearchResult([row], None)
        ]):
            result = search_sharepoint(nlp.parse('tài sản công văn'), HR)
        self.assertEqual(result.results, [row])
        self.assertIsNone(result.error_note)
        with patch('apps.assistant.m365_search._search_sharepoint_single', side_effect=[
            SharePointSearchResult([row], None), SharePointSearchResult([], 'unavailable')
        ]):
            result = search_sharepoint(nlp.parse('công văn báo cáo hoạt động'), HR)
        self.assertEqual(result.results, [row])
        self.assertEqual(result.error_note, 'unavailable')


class HistoryReviewTests(SimpleTestCase):
    def test_scope_is_fixed_size_and_invalidates_for_role_tree_and_policy(self):
        user = SimpleNamespace(pk=1, role_id=1, is_active=True, is_superuser=False)
        request = SimpleNamespace(user=user, session={})
        with patch('apps.security.data_access.employee_and_subordinate_ids', return_value={1}):
            views._history(request)
            scope = request.session['assistant_history_scope']
            self.assertIsInstance(scope, str)
            self.assertEqual(len(scope), 64)
            request.session['assistant_history'] = ['QA']
            self.assertEqual(views._history(request), ['QA'])
        with patch('apps.security.data_access.employee_and_subordinate_ids', return_value=set(range(5000))):
            self.assertEqual(views._history(request), [])
            self.assertEqual(len(request.session['assistant_history_scope']), 64)
            request.session['assistant_history'] = ['QA']
            user.role_id = 2
            self.assertEqual(views._history(request), [])
            request.session['assistant_history'] = ['QA']
            with patch.object(views, 'HISTORY_POLICY_VERSION', 'future-policy', create=True):
                self.assertEqual(views._history(request), [])


class WordingReviewTests(SimpleTestCase):
    def test_reviewed_wording_and_session_retention_documented(self):
        root = Path(__file__).resolve().parents[2]
        for relative, bad in [('apps/assistant/views.py', 'trước when kiểm tra'), ('apps/assistant/services.py', 'MọiExceptions')]:
            self.assertNotIn(bad, (root/relative).read_text(encoding='utf-8'))
        spec = (root.parent/'docs/superpowers/specs/2026-10-19-assistant-chatbot-design.md').read_text(encoding='utf-8')
        for bad in ('thừơng', 'Ngưởi', 'ngưởi', 'rồi khỏi'):
            self.assertNotIn(bad, spec)
        self.assertIn('session', spec)
        self.assertIn('20 lượt', spec)
