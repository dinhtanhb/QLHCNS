"""`purge_search_logs` là deliverable của spec mục 4, không phải tùy chọn: bảng
nhật ký chứa câu hỏi tự do của người dùng và lớn mãi nếu không có đường xóa."""
from datetime import timedelta
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from apps.assistant.models import SearchQueryLog
from apps.portal import test_home_dashboard as fixtures


class PurgeSearchLogsTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user(cls, "HR_MANAGER", True)

    def _log(self, days_ago, **extra):
        log = SearchQueryLog.objects.create(
            user=self.hr, question="công văn nghỉ phép", parsed_filters={},
            result_count=0, sources="db", took_ms=1, **extra,
        )
        # `created_date` là auto_now_add nên chỉ đổi được sau khi ghi.
        SearchQueryLog.all_objects.filter(pk=log.pk).update(
            created_date=timezone.now() - timedelta(days=days_ago)
        )
        return log

    def _run(self, *args):
        out = StringIO()
        call_command("purge_search_logs", *args, stdout=out, stderr=out)
        return out.getvalue()

    def test_without_apply_nothing_is_deleted(self):
        self._log(400)
        self._log(10)
        report = self._run("--days", "180")
        self.assertIn("1 dòng", report)
        self.assertEqual(SearchQueryLog.all_objects.count(), 2)

    def test_apply_removes_only_rows_past_the_cutoff(self):
        old = self._log(400)
        recent = self._log(10)
        self._run("--days", "180", "--apply")
        remaining = set(SearchQueryLog.all_objects.values_list("pk", flat=True))
        self.assertEqual(remaining, {recent.pk})
        self.assertNotIn(old.pk, remaining)

    def test_soft_deleted_old_rows_are_purged_too(self):
        # Log mềm vẫn giữ nguyên câu hỏi trong DB và trong backup, nên dọn phải
        # quét cả `all_objects`, không chỉ tập chưa xóa.
        old = self._log(400)
        old.delete(user=self.hr)
        self._run("--days", "180", "--apply")
        self.assertFalse(SearchQueryLog.all_objects.filter(pk=old.pk).exists())

    def test_zero_days_is_rejected(self):
        with self.assertRaises(CommandError):
            self._run("--days", "0", "--apply")

    def test_empty_table_reports_without_error(self):
        self.assertIn("Không có nhật ký", self._run("--apply"))
