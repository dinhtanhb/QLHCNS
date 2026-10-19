"""Dọn nhật ký truy vấn của trợ lý tài liệu (spec mục 4: "có cơ chế dọn log cũ,
chạy thủ công").

Bảng này chứa câu hỏi tự do của người dùng, tức là dữ liệu cá nhân, nên mặc định
lệnh CHỈ đếm. Phải thêm `--apply` mới xóa, và xóa là xóa cứng
(`all_objects.hard_delete`) vì để lại dòng `is_deleted` thì nội dung vẫn nằm
trong database và trong mọi bản sao lưu.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.assistant.models import SearchQueryLog

DEFAULT_DAYS = 180


class Command(BaseCommand):
    help = ("Xóa nhật ký truy vấn trợ lý cũ hơn N ngày (mặc định 180). "
            "Không có --apply thì chỉ thống kê.")

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                            help="Số ngày giữ lại, tính từ hiện tại.")
        parser.add_argument("--apply", action="store_true",
                            help="Thực sự xóa. Thiếu cờ này lệnh chỉ đếm.")

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError("--days phải lớn hơn 0")
        cutoff = timezone.now() - timedelta(days=days)
        queryset = SearchQueryLog.all_objects.filter(created_date__lt=cutoff)
        count = queryset.count()
        if not count:
            self.stdout.write(f"Không có nhật ký nào trước {cutoff:%Y-%m-%d %H:%M}.")
            return
        if not options["apply"]:
            self.stdout.write(self.style.WARNING(
                f"{count} dòng nhật ký cũ hơn {days} ngày (trước "
                f"{cutoff:%Y-%m-%d %H:%M}). Thêm --apply để xóa hẳn."
            ))
            return
        deleted, _ = queryset.hard_delete()
        self.stdout.write(self.style.SUCCESS(
            f"Đã xóa {deleted} dòng nhật ký truy vấn trước {cutoff:%Y-%m-%d %H:%M}."
        ))
