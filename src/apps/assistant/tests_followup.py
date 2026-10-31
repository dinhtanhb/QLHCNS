"""Regressions and measurements for the second assistant review."""
import ast
from dataclasses import asdict, replace
from datetime import date
import json
from pathlib import Path
import unicodedata
from unittest.mock import patch

from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from . import m365_search, nlp
from . import tests_db_search as db_tests
from .tests_m365_search import ASSISTANT_SETTINGS, SITE, _FakeClient, _hit, _user


class DateFollowupTests(SimpleTestCase):
    def test_first_period_wins_and_all_recognized_periods_are_consumed(self):
        for question, start, end in [
            ('công văn tháng này hôm nay', date(2026,10,1), date(2026,10,31)),
            ('tháng này tháng 9', date(2026,10,1), date(2026,10,31)),
            ('hôm nay tháng này', date(2026,10,31), date(2026,10,31)),
            ('tháng 9 tháng này', date(2026,9,1), date(2026,9,30)),
            ('năm 2025 hôm nay', date(2025,1,1), date(2025,12,31)),
            ('ngày 29 tháng 2 năm 2024 tháng này', date(2024,2,29), date(2024,2,29)),
            ('quý 2 năm 2025 từ 01/01/2026 đến 31/01/2026', date(2025,4,1), date(2025,6,30)),
        ]:
            with self.subTest(question=question):
                parsed = nlp.parse(question, today=date(2026,10,31))
                self.assertEqual((parsed.date_from, parsed.date_to), (start,end))
                self.assertEqual(parsed.keywords, [])

    def test_nfc_nfd_periods_have_identical_parse(self):
        for phrase in ('tháng này','tuần này','hôm nay','tuần trước','tháng trước',
                       'năm ngoái','tháng 9 năm 2025','quý 2 năm 2025',
                       'ngày 29 tháng 2 năm 2024','từ 01/01/2026 đến 31/01/2026'):
            with self.subTest(phrase=phrase):
                question = 'Quyết định '+phrase
                expected = nlp.parse(question, date(2026,10,31))
                actual = nlp.parse(unicodedata.normalize('NFD',question), date(2026,10,31))
                self.assertEqual(asdict(actual), asdict(expected))

    def test_one_period_and_document_number_compatibility(self):
        for question in ('tháng này','tuần này','hôm nay','tuần trước','tháng trước',
                         'tháng 9 năm 2025','quý 2 năm 2025','ngày 29 tháng 2 năm 2024',
                         'từ 31/02/2026 đến 01/03/2026','tháng 13 năm 2025'):
            with self.subTest(question=question):
                parsed = nlp.parse(question, date(2026,10,31))
                legacy = getattr(nlp, '_extract_one_date', nlp._extract_dates)
                _, start, end = legacy(question, date(2026,10,31))
                self.assertEqual((parsed.date_from,parsed.date_to), (start,end))
        self.assertEqual(nlp.parse('công văn 12/2026').doc_number, '12/2026')


@override_settings(**ASSISTANT_SETTINGS)
class SharePointFollowupTests(SimpleTestCase):
    def setUp(self):
        # This factory patch is the network boundary in every scenario.
        self.factory = patch('apps.assistant.m365_search.get_graph_client')
        self.get_client = self.factory.start()
        self.addCleanup(self.factory.stop)
        self.user = _user('SUPER_ADMIN', superuser=True)

    def run_query(self, parsed, **kwargs):
        client = _FakeClient(**kwargs)
        self.get_client.return_value = client
        result = m365_search.search_sharepoint(parsed,self.user)
        return result, client

    def test_same_allowed_roots_are_searched_once(self):
        # Both aliases point to the same configured root; no permission added.
        with override_settings(M365_FOLDER_MAP={'incoming_docs':'Shared','outgoing_docs':'Shared'}):
            hit = _hit('QA.pdf',SITE+'/Shared/QA.pdf')
            one, single_client = self.run_query(nlp.parse('công văn đến QA'),search=[hit])
            two, client = self.run_query(nlp.parse('công văn đến công văn đi QA'),search=[hit])
        self.assertEqual(two,one)
        self.assertEqual(len(client.search_calls),len(single_client.search_calls))
        self.assertEqual(len(client.root_calls),len(single_client.root_calls))

    def test_four_distinct_root_groups_are_capped_at_three_passes(self):
        folders = {'incoming_docs':'In','outgoing_docs':'Out','activity_reports':'Reports','recruitment_cv':'CV'}
        hits = [_hit('QA.pdf',SITE+'/'+folder+'/QA.pdf') for folder in folders.values()]
        with override_settings(M365_FOLDER_MAP=folders), self.assertLogs('apps.assistant.m365_search',level='WARNING') as log:
            parsed = nlp.ParsedQuery(doc_type='Incoming',doc_types=['Incoming','Outgoing','activity_report','candidate'],keywords=['qa'])
            _, client = self.run_query(parsed,search=hits)
        self.assertLessEqual(len(client.search_calls),3)
        self.assertEqual(len(client.search_calls),3)
        self.assertIn('candidate',log.output[0])

    def test_restricted_type_does_not_use_a_pass_or_hide_partial_status(self):
        from apps.m365.graph_client import GraphAPIError
        parsed = nlp.parse('tài sản công văn QA')
        result, client = self.run_query(parsed,search=GraphAPIError('QA timeout',status_code=503))
        self.assertEqual(result.error_note,'unavailable')
        self.assertEqual(len(client.search_calls),1)
        result, client = self.run_query(parsed,search=GraphAPIError('QA denied',status_code=403))
        self.assertEqual(result.error_note,'search_fallback')
        self.assertEqual(len(client.search_calls),1)

    def test_one_and_two_type_results_and_status_match_previous_behavior(self):
        hit = _hit('QA.pdf',SITE+'/CongVanDen/QA.pdf')
        parsed = nlp.parse('tài sản công văn QA')
        client = _FakeClient(search=[hit])
        self.get_client.return_value = client
        expected = [m365_search._search_sharepoint_single(replace(parsed,doc_type=kind,doc_types=[]),self.user)
                    for kind in parsed.doc_types]
        actual, _ = self.run_query(parsed,search=[hit])
        self.assertEqual(actual.results,[row for result in expected for row in result.results])
        self.assertIsNone(actual.error_note)


class ImportOrderFollowupTests(SimpleTestCase):
    def test_standard_imports_are_alphabetical(self):
        path = Path(__file__).with_name('views.py')
        names = [alias.name for node in ast.parse(path.read_text(encoding='utf-8')).body
                 if isinstance(node,ast.Import) for alias in node.names]
        self.assertEqual(names,sorted(names))


@override_settings(M365_STORAGE_ENABLED=False)
class HistoryQueryMeasurementTests(TestCase):
    """Measure existing behavior only; do not cache or impose a query budget."""
    user = db_tests.DbSearchTests.user

    @classmethod
    def setUpTestData(cls):
        from apps.hrm.models import Employee
        db_tests.DbSearchTests.setUpTestData.__func__(cls)
        cls.manager = cls.user(cls,'DEPT_MANAGER',True)
        root = cls.manager.employee
        def employee(index, manager):
            return Employee(employee_code=f'QA-TREE-{index}',first_name='QA',last_name=str(index),
                full_name=f'QA synthetic {index}',date_of_birth=date(1990,1,1),gender='Other',
                national_id=f'QA-TREE-{index}',company_email=f'qa-tree-{index}@example.test',
                mobile_phone='0000000000',join_date=date(2020,1,1),department_id=root.department_id,
                position_id=root.position_id,manager_id=manager)
        Employee.objects.bulk_create([employee(index,root.pk) for index in range(10)],batch_size=100)
        leaders = list(Employee.objects.filter(employee_code__startswith='QA-TREE-').order_by('pk').values_list('pk',flat=True))
        Employee.objects.bulk_create([employee(index,leaders[index%10]) for index in range(10,300)],batch_size=100)

    def test_measure_authenticated_search_and_history_with_300_subordinates(self):
        from apps.security.data_access import employee_and_subordinate_ids
        self.assertEqual(len(employee_and_subordinate_ids(self.manager)),301)
        self.client.force_login(self.manager)
        measurements = {'backend':connection.vendor,'subordinates':300,'levels':2,'samples':[]}
        with patch('apps.assistant.m365_search.get_graph_client',side_effect=AssertionError('No real Graph')):
            for method, route in [('get','assistant:api_history'),('post','assistant:api_search')]:
                for iteration in range(3):
                    with CaptureQueriesContext(connection) as captured:
                        if method == 'get':
                            response = self.client.get(reverse(route))
                        else:
                            response = self.client.post(reverse(route),data=json.dumps({'question':'công văn'}),content_type='application/json')
                    self.assertEqual(response.status_code,200)
                    tree_queries = 0
                    for query in captured:
                        projection = query['sql'].lower().split(' from ',1)[0]
                        if 'tblemployee' in query['sql'].lower() and 'managerid' in projection and 'fullname' not in projection:
                            tree_queries += 1
                    self.assertGreaterEqual(tree_queries,1)
                    measurements['samples'].append({'method':method.upper(),'iteration':iteration+1,
                        'queries':len(captured),'full_tree_selects':tree_queries})
        print('ASSISTANT_HISTORY_QUERIES='+json.dumps(measurements,sort_keys=True))
