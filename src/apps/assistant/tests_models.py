from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.assistant.models import SearchQueryLog


class SearchQueryLogModelTests(TestCase):
    def test_create_minimal(self):
        User = get_user_model()
        user = User.objects.create_user(username="log-tester", password="x")
        log = SearchQueryLog.objects.create(
            user=user, question="tim cong van", parsed_filters={"keywords": ["cong", "van"]},
            result_count=3, sources="db", took_ms=12, created_by=user,
        )
        self.assertEqual(log._meta.db_table, "tblAssistantSearchLog")
        self.assertEqual(log.error_note, None)
        reloaded = SearchQueryLog.objects.get()
        self.assertEqual(str(log.pk), str(reloaded.pk))
        # parsed_filters là field duy nhất có DDL khác nhau theo backend
        # (sqlite: JSON_VALID, mssql: ISJSON) nên phải đọc ngược từ DB,
        # không chỉ so pk.
        self.assertEqual(reloaded.parsed_filters, {"keywords": ["cong", "van"]})
        # related_name là interface công bố cho các task sau.
        self.assertEqual(user.assistant_search_logs.count(), 1)

    def test_took_ms_verbose_name_is_correct_vietnamese(self):
        # Khóa nhãn đã sửa chính tả; hồi quy về "Thờ gian (ms)" sẽ fail.
        self.assertEqual(
            SearchQueryLog._meta.get_field("took_ms").verbose_name, "Thời gian (ms)"
        )
