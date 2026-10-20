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

    def test_impossible_date_range_does_not_crash_the_parse(self):
        # Một ngày sai lịch là lỗi gõ phím rất thường gặp (31/02, ngày 30/2 năm
        # không nhuận, năm 0000). `datetime.strptime` raise ValueError, và vì
        # `services.ask` gọi parse ngoài mọi try nên người hỏi nhận HTTP 500 -
        # kèm theo việc câu hỏi không bao giờ tới được log, tức là chính cơ chế
        # "dùng log để rà soát parser" (spec mục 7) bị mù đúng chỗ đó.
        for question in (
            "từ 31/02/2026 đến 01/03/2026",
            "từ 29/02/2025 đến 05/03/2025",
            "từ 2026-02-30 đến 2026-03-01",
            "từ 01/01/0000 đến 02/01/0000",
            "quý 1 năm 0000",
            "năm 0000",
        ):
            with self.subTest(question=question):
                p = parse(question, today=date(2026, 10, 19))
                self.assertIsNone(p.date_from)
                self.assertIsNone(p.date_to)

    def test_impossible_range_still_loses_the_date_phrase_from_keywords(self):
        # Bỏ qua bộ lọc thời gian không có nghĩa là để nguyên "từ ... đến ..."
        # làm từ khóa: các token đó phủ chủ đề thật và bảo đảm không ra kết quả.
        p = parse("từ 31/02/2026 đến 01/03/2026 nghỉ phép", today=date(2026, 10, 19))
        self.assertTrue({"nghi", "phep"} <= set(p.keywords))
        self.assertNotIn("31/02/2026", " ".join(p.keywords))

    def test_reversed_range_is_swapped_not_silently_empty(self):
        # "từ 31/12/2026 đến 01/01/2026" là đảo ngược, không phải vô nghĩa. Để
        # nguyên thì SQL AND hai điều kiện loại nhau và người dùng bị báo "không
        # có tài liệu trong phạm vi quyền" - tức là đổ lỗi cho họ.
        p = parse("từ 31/12/2026 đến 01/01/2026", today=date(2026, 10, 19))
        self.assertEqual((p.date_from, p.date_to), (date(2026, 1, 1), date(2026, 12, 31)))

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

    def test_single_date_extraction(self):
        p = parse("tìm file QD ngày 29.04.2020")
        self.assertEqual(p.date_from, date(2020, 4, 29))
        self.assertEqual(p.date_to, date(2020, 4, 29))
        self.assertEqual(p.doc_type, "personnel_decision")
        self.assertEqual(p.keywords, [])

        p2 = parse("quyết định ngày 29/04/2020")
        self.assertEqual((p2.date_from, p2.date_to), (date(2020, 4, 29), date(2020, 4, 29)))

        p3 = parse("ngày 29 tháng 4 năm 2020")
        self.assertEqual((p3.date_from, p3.date_to), (date(2020, 4, 29), date(2020, 4, 29)))

        p4 = parse("công văn 2026-10-20")
        self.assertEqual((p4.date_from, p4.date_to), (date(2026, 10, 20), date(2026, 10, 20)))
        self.assertEqual(p4.doc_type, "dispatch")

    def test_qd_abbreviation_and_file_stopwords(self):
        p1 = parse("tìm file QD")
        self.assertEqual(p1.doc_type, "personnel_decision")
        self.assertEqual(p1.keywords, [])

        p2 = parse("tìm tệp QĐ")
        self.assertEqual(p2.doc_type, "personnel_decision")
        self.assertEqual(p2.keywords, [])
