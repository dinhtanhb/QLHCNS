"""Closeout regression tests: ignored dates and the conditional suffix finding."""
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import nlp, services, tests_db_search as fixtures
from .models import SearchQueryLog

REGRESSION_QUESTIONS = [
    'công văn tháng 9 năm 2025','tháng 9/2025','quý 3 năm 2025',
    'từ 01/09/2025 đến 30/09/2025','ngày 05/10/2026','quyết định năm 2025',
    'công văn năm ngoái','quyết định tuyển dụng tháng 10 năm 2026',
    'công văn tháng này','quyết định 12/2026','công văn số 123/2025',
    'tuần trước','tháng trước','hôm nay','tuần này','quý 2',
    'công văn đến 45/CV','năm 2025 quý 2','quý 2 về năm 2025','tài liệu quy trình',
]


class IgnoredDateParserTests(SimpleTestCase):
    def test_only_unapplied_outer_phrases_are_reported(self):
        parsed=nlp.parse('công văn tuần trước năm 2025 quý 2',date(2026,10,31))
        self.assertEqual((parsed.date_from,parsed.date_to),(date(2026,10,24),date(2026,10,31)))
        self.assertEqual(parsed.ignored_date_phrases,['năm 2025','quý 2'])
        self.assertEqual(parsed.keywords,[])

    def test_single_nested_and_combined_periods_do_not_warn(self):
        for question in REGRESSION_QUESTIONS:
            with self.subTest(question=question):
                self.assertEqual(nlp.parse(question,date(2026,10,31)).ignored_date_phrases,[])

    def test_merged_pair_is_applied_but_later_other_period_is_ignored(self):
        parsed=nlp.parse('năm 2025 quý 2 hôm nay',date(2026,10,31))
        self.assertEqual((parsed.date_from,parsed.date_to),(date(2025,4,1),date(2025,6,30)))
        self.assertEqual(parsed.ignored_date_phrases,['hôm nay'])


class CloseoutServiceTests(TestCase):
    user=fixtures.DbSearchTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.DbSearchTests.setUpTestData.__func__(cls)

    def setUp(self):
        guard=patch('apps.assistant.m365_search.get_graph_client',side_effect=AssertionError('No real Graph'))
        guard.start()
        self.addCleanup(guard.stop)

    def test_time_notice_is_optional_and_not_added_to_parsed_or_query_log(self):
        original=nlp.parse
        with patch('apps.assistant.services.nlp.parse',side_effect=lambda q: original(q,date(2026,10,31))):
            response=services.ask('công văn tuần trước năm 2025 quý 2',self.hr)
        self.assertIn('năm 2025',response['time_notice'])
        self.assertIn('quý 2',response['time_notice'])
        self.assertEqual(set(response['parsed']),{'doc_number','phrases','keywords','date_from','date_to','doc_type','doc_types'})
        self.assertEqual(SearchQueryLog.objects.get().parsed_filters,response['parsed'])
        self.assertNotIn('time_notice',SearchQueryLog.objects.get().parsed_filters)
        self.assertNotIn('ignored_date_phrases',response['parsed'])

    def test_twenty_regression_questions_do_not_add_time_notice(self):
        original=nlp.parse
        for question in REGRESSION_QUESTIONS:
            with self.subTest(question=question), patch('apps.assistant.services.nlp.parse',side_effect=lambda q: original(q,date(2026,10,31))):
                self.assertNotIn('time_notice',services.ask(question,self.hr))

    def test_document_number_suffix_returns_both_records_with_full_match_first(self):
        from apps.document.models import PersonnelDecision
        records=[]
        for number in ('12/2025/QĐ-VH','12/2025'):
            records.append(PersonnelDecision.objects.create(employee=self.emp.employee,template_slug='bo-nhiem',
                decision_no=number,decision_date=date(2025,9,1),status='Issued'))
        response=services.ask('quyết định 12/2025/QĐ-VH',self.hr)
        self.assertEqual([row['url'] for row in response['results']],
            [reverse('portal:personnel_decision_detail',args=[record.pk]) for record in records])
        print('D2_SUFFIX_RESULT=both_found_full_suffix_first')

    def test_time_notice_js_uses_existing_safe_warning(self):
        js=(Path(__file__).resolve().parents[2]/'static/js/assistant.js').read_text(encoding='utf-8')
        self.assertIn('payload.time_notice',js)
        self.assertNotIn('innerHTML',js)
