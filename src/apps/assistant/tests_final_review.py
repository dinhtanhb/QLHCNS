"""Regression tests for remaining assistant review C1-C3."""
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from . import m365_search, nlp, services, tests_db_search as db_tests
from .models import SearchQueryLog
from .tests_m365_search import SITE, _FakeClient, _hit, _user


class PeriodYearReviewTests(SimpleTestCase):
    def test_existing_format_regression_cases(self):
        for question, start, end, number in [
            ('công văn tháng 9 năm 2025',date(2025,9,1),date(2025,9,30),None),
            ('tháng 9/2025',date(2025,9,1),date(2025,9,30),None),
            ('quý 3 năm 2025',date(2025,7,1),date(2025,9,30),None),
            ('từ 01/09/2025 đến 30/09/2025',date(2025,9,1),date(2025,9,30),None),
            ('ngày 05/10/2026',date(2026,10,5),date(2026,10,5),None),
            ('quyết định năm 2025',date(2025,1,1),date(2025,12,31),None),
            ('công văn năm ngoái',date(2025,1,1),date(2025,12,31),None),
            ('quyết định tuyển dụng tháng 10 năm 2026',date(2026,10,1),date(2026,10,31),None),
            ('công văn tháng này',date(2026,10,1),date(2026,10,31),None),
            ('quyết định 12/2026',None,None,'12/2026'),
            ('công văn số 123/2025',None,None,'123/2025'),
        ]:
            with self.subTest(question=question):
                parsed=nlp.parse(question,date(2026,10,31))
                self.assertEqual((parsed.date_from,parsed.date_to,parsed.doc_number),(start,end,number))
    def test_new_month_and_quarter_year_formats_consume_entire_phrase(self):
        for question, start, end in [
            ('quý 3/2025',date(2025,7,1),date(2025,9,30)),
            ('quý 3 2025',date(2025,7,1),date(2025,9,30)),
            ('quý 3, 2025',date(2025,7,1),date(2025,9,30)),
            ('tháng 9 2025',date(2025,9,1),date(2025,9,30)),
            ('tháng 9, 2025',date(2025,9,1),date(2025,9,30)),
        ]:
            with self.subTest(question=question):
                parsed=nlp.parse(question,date(2026,10,31))
                self.assertEqual((parsed.date_from,parsed.date_to),(start,end))
                self.assertEqual(parsed.keywords,[])

    def test_plain_year_is_bounded_and_invalid_month_has_no_dates(self):
        for number in ('1234','20255','1899','2100','2025a'):
            with self.subTest(number=number):
                parsed=nlp.parse('tháng 9 '+number,date(2026,10,31))
                self.assertEqual(parsed.date_from,date(2026,9,1))
                self.assertIn(number,parsed.keywords)
        parsed=nlp.parse('tháng 13 2025',date(2026,10,31))
        self.assertIsNone(parsed.date_from)
        self.assertIsNone(parsed.date_to)
        for year in (1999,2099):
            self.assertEqual(nlp.parse('tháng 9 '+str(year),date(2026,10,31)).date_from,date(year,9,1))

    def test_standalone_year_combines_with_bare_period_in_both_orders(self):
        for period, start, end in [('quý 2',date(2025,4,1),date(2025,6,30)),
                                   ('tháng 9',date(2025,9,1),date(2025,9,30))]:
            for question in ('năm 2025 '+period,period+' về năm 2025',period+' năm 2025'):
                with self.subTest(question=question):
                    parsed=nlp.parse(question,date(2026,10,31))
                    self.assertEqual((parsed.date_from,parsed.date_to),(start,end))
                    self.assertEqual(parsed.keywords,[])

    def test_fully_dated_period_with_other_year_keeps_first_filter(self):
        for question, start, end in [
            ('năm 2024 tháng 9 năm 2025',date(2024,1,1),date(2024,12,31)),
            ('tháng 9 năm 2025 năm 2024',date(2025,9,1),date(2025,9,30)),
            ('năm 2024 quý 2 năm 2025',date(2024,1,1),date(2024,12,31)),
            ('quý 2 năm 2025 năm 2024',date(2025,4,1),date(2025,6,30)),
        ]:
            with self.subTest(question=question):
                parsed=nlp.parse(question,date(2026,10,31))
                self.assertEqual((parsed.date_from,parsed.date_to),(start,end))
                self.assertEqual(parsed.keywords,[])


FOLDERS={'incoming_docs':'In','outgoing_docs':'Out','activity_reports':'Reports','recruitment_cv':'CV','personnel_decisions':'Decisions'}


@override_settings(M365_STORAGE_ENABLED=True,M365_FOLDER_MAP=FOLDERS)
class LimitResultReviewTests(SimpleTestCase):
    def test_skipped_types_preserve_unique_order_and_all_searched_results(self):
        hits=[_hit('QA.pdf',SITE+'/'+folder+'/QA.pdf') for folder in FOLDERS.values()]
        parsed=nlp.ParsedQuery(doc_type='Incoming',doc_types=['Incoming','Outgoing','activity_report','candidate','personnel_decision','candidate'],keywords=['qa'])
        client=_FakeClient(search=hits)
        with patch('apps.assistant.m365_search.get_graph_client',return_value=client):
            result=m365_search.search_sharepoint(parsed,_user('SUPER_ADMIN',superuser=True))
        self.assertEqual(result.skipped_types,['candidate','personnel_decision'])
        self.assertEqual(len(client.search_calls),3)
        self.assertEqual({row['url'] for row in result.results},{hit['web_url'] for hit in hits[:3]})
        self.assertIsNone(result.error_note)

    def test_legacy_tuple_and_optional_list_defaults(self):
        result=m365_search.SharePointSearchResult([],None)
        self.assertEqual(tuple(result),([],None))
        self.assertEqual(result.skipped_types,[])
        result.skipped_types.append('Outgoing')
        self.assertEqual(m365_search.SharePointSearchResult([],None).skipped_types,[])


class LimitNoticeReviewTests(TestCase):
    user=db_tests.DbSearchTests.user

    @classmethod
    def setUpTestData(cls):
        db_tests.DbSearchTests.setUpTestData.__func__(cls)

    @override_settings(M365_STORAGE_ENABLED=True,M365_FOLDER_MAP=FOLDERS)
    def test_four_groups_end_to_end_notice_and_three_groups_without_notice(self):
        self.hr.is_superuser=True
        hits=[_hit(folder+' QA.pdf',SITE+'/'+folder+'/QA.pdf') for folder in FOLDERS.values()]
        for question, expected, limited in [
            ('công văn đến công văn đi báo cáo hoạt động ứng viên QA',{'Reports QA.pdf','CV QA.pdf','In QA.pdf'},True),
            ('công văn đến công văn đi báo cáo hoạt động QA',{'Reports QA.pdf','In QA.pdf','Out QA.pdf'},False),
        ]:
            with self.subTest(question=question), patch('apps.assistant.m365_search.get_graph_client',return_value=_FakeClient(search=hits)):
                response=services.ask(question,self.hr)
                self.assertEqual({row['title'] for row in response['results']},expected)
                self.assertEqual('limit_notice' in response,limited)
                if limited:
                    self.assertIn('công văn đi',response['limit_notice'])
                    self.assertNotIn('Outgoing',response['limit_notice'])

    def test_notice_is_optional_vietnamese_and_never_saved_in_query_log(self):
        result=m365_search.SharePointSearchResult([],None)
        result.skipped_types=['Outgoing','activity_report']
        with patch('apps.assistant.m365_search.get_graph_client',side_effect=AssertionError('No real Graph')), \
             patch('apps.assistant.m365_search.search_sharepoint',return_value=result):
            response=services.ask('công văn',self.hr)
        self.assertIn('công văn đi',response['limit_notice'])
        self.assertIn('báo cáo hoạt động',response['limit_notice'])
        self.assertNotIn('Outgoing',response['limit_notice'])
        self.assertNotIn('activity_report',response['limit_notice'])
        self.assertFalse(response['partial'])
        self.assertEqual(response['sharepoint_status'],'ok')
        log=SearchQueryLog.objects.get()
        self.assertNotIn('limit_notice',log.parsed_filters)
        self.assertIsNone(log.error_note)
        result.skipped_types=[]
        with patch('apps.assistant.m365_search.search_sharepoint',return_value=result):
            self.assertNotIn('limit_notice',services.ask('công văn',self.hr))
        result.skipped_types=['Outgoing']
        with patch('apps.assistant.m365_search.search_sharepoint',return_value=result):
            empty=services.ask('công văn qa-khong-ton-tai',self.hr)
        self.assertEqual(empty['results'],[])
        self.assertIn('công văn đi',empty['limit_notice'])

    def test_js_renders_limit_notice_with_safe_text_for_empty_and_results(self):
        js=(Path(__file__).resolve().parents[2]/'static/js/assistant.js').read_text(encoding='utf-8')
        self.assertIn('payload.limit_notice',js)
        self.assertNotIn('innerHTML',js)
