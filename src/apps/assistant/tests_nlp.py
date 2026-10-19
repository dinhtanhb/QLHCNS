from datetime import date

from django.test import SimpleTestCase

from apps.assistant.nlp import ParsedQuery, parse


class QueryParserTests(SimpleTestCase):
    def test_doc_number(self):
        p = parse("tìm công văn số 1234/QĐ-VH")
        self.assertEqual(p.doc_number, "1234/QĐ-VH")
        self.assertEqual(p.doc_type, "dispatch")

    def test_doc_number_without_prefix(self):
        self.assertEqual(parse("công văn 12/2026 về ngân sách").doc_number, "12/2026")

    def test_quoted_phrase(self):
        p = parse('tìm "nghỉ phép không lương" tháng 6')
        self.assertEqual(p.phrases, ["nghỉ phép không lương"])
        self.assertNotIn("không", p.keywords)

    def test_month_current_year(self):
        p = parse("công văn tháng 6", today=date(2026, 10, 19))
        self.assertEqual(p.date_from, date(2026, 6, 1))
        self.assertEqual(p.date_to, date(2026, 6, 30))

    def test_month_with_year(self):
        p = parse("hồ sơ tháng 3 năm 2025", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2025, 3, 1), date(2025, 3, 31)))

    def test_quarter(self):
        p = parse("quý 2 năm 2026", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2026, 4, 1), date(2026, 6, 30)))

    def test_year_only(self):
        p = parse("công văn năm 2025", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2025, 1, 1), date(2025, 12, 31)))

    def test_relative_last_month(self):
        p = parse("công văn tháng trước", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2026, 9, 1), date(2026, 9, 30)))

    def test_relative_last_week(self):
        p = parse("tuần trước", today=date(2026, 10, 19))
        self.assertEqual(p.date_from, date(2026, 10, 12))
        self.assertEqual(p.date_to, date(2026, 10, 19))

    def test_relative_last_year(self):
        p = parse("công văn năm ngoái", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2025, 1, 1), date(2025, 12, 31)))

    def test_from_to_range(self):
        p = parse("từ 01/06/2026 đến 30/06/2026", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2026, 6, 1), date(2026, 6, 30)))

    def test_from_to_range_accepts_other_date_separators(self):
        # Chuỗi ngày dán từ hệ thống khác sang có thể dùng dấu gạch nối hoặc
        # thuận ngược nhau; mọi nhánh định dạng phải phân giải được.
        for question in (
            "từ 01-06-2026 đến 30-06-2026",
            "từ 2026-06-01 đến 2026-06-30",
            "từ 2026/06/01 đến 2026/06/30",
        ):
            with self.subTest(question=question):
                p = parse(question, today=date(2026, 10, 19))
                self.assertEqual((p.date_from, p.date_to), (date(2026, 6, 1), date(2026, 6, 30)))

    def test_doc_type_variants(self):
        self.assertEqual(parse("công văn đến").doc_type, "Incoming")
        self.assertEqual(parse("công văn đi").doc_type, "Outgoing")
        self.assertEqual(parse("văn bản chỉ đạo nội bộ").doc_type, "InternalDirective")
        self.assertEqual(parse("quyết định bổ nhiệm").doc_type, "personnel_decision")
        self.assertEqual(parse("tài liệu quy trình").doc_type, "document")

    def test_keywords_strip_stopwords_and_type_words(self):
        p = parse("tìm giúp tôi công văn về ngân sách quý 4", today=date(2026, 10, 19))
        self.assertEqual(p.doc_type, "dispatch")
        # Từ khóa là token đã bỏ dấu (chúng chạy icontrans trên DB), không phải cụm.
        self.assertIn("ngan", p.keywords)
        self.assertIn("sach", p.keywords)
        for w in ("tim", "giup", "toi", "ve", "cong", "van", "quy"):
            self.assertNotIn(w, p.keywords)

    def test_stopword_cua_is_latin_and_stripped(self):
        # "của" phải mang a Latin; bản mang a Cyrillic thì không loại được từ này.
        p = parse("công văn của phòng tổ chức", today=date(2026, 10, 19))
        self.assertNotIn("cua", p.keywords)
        self.assertIn("phong", p.keywords)

    def test_no_diacritics_input_is_detected(self):
        p = parse("Cong van nghi phep")
        self.assertEqual(p.doc_type, "dispatch")
        self.assertIn("nghi", p.keywords)
        self.assertIn("phep", p.keywords)

    def test_fallback_whole_question_as_keywords(self):
        p = parse("abcdefgh")
        self.assertEqual(p.doc_number, None)
        self.assertEqual(p.keywords, ["abcdefgh"])

    def test_empty_and_short(self):
        self.assertEqual(parse("").keywords, [])
        self.assertEqual(parse("  a  ").keywords, [])

    def test_no_constraint_question_yields_no_keywords(self):
        # Toàn stopword -> has_constraints() False, không được rơi vào fallback.
        p = parse("tìm giúp tôi", today=date(2026, 10, 19))
        self.assertEqual(p.keywords, [])
        self.assertFalse(p.has_constraints())

    def test_keywords_are_capped(self):
        p = parse("alpha bravo charlie delta echo foxtrot golf hotel india "
                  "juliett kilo lima", today=date(2026, 10, 19))
        self.assertEqual(len(p.keywords), 10)

    def test_question_is_truncated_at_log_limit(self):
        # question cat theo SearchQueryLog.question (max_length=500), nen phan
        # vuot qua khong duoc bien thanh tu khoa.
        p = parse("công văn " + ("a" * 490) + " zzz")
        self.assertNotIn("zzz", p.keywords)

    def test_parse_result_is_dataclass(self):
        p = parse("công văn tháng 6", today=date(2026, 10, 19))
        self.assertIsInstance(p, ParsedQuery)
