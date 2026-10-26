"""Một nguồn màu Python duy nhất cho báo cáo xuất tệp (pptx/openpyxl).

Thư viện pptx/openpyxl cần mã hex, không đọc được biến CSS, nên bảng này sao
chép khối light của ui_tokens.css cho từng palette. UI_PALETTE là cấu hình máy
chủ (xem config/settings.py); test_report_palette.py giữ bảng này khớp token CSS
của từng pack — đổi CSS mà quên đây sẽ đỏ ngay.

Báo cáo PPT/Excel luôn in nền sáng nên chỉ dùng tông light của mỗi palette.
"""
from django.conf import settings

# Tên hằng ← token CSS khối light tương ứng trong ui_tokens.css:
#   NAVY  ← --ui-text           MUTED ← --ui-text-muted
#   TEAL  ← --ui-brand          LINE  ← --ui-card-border
#   MINT  ← --ui-brand-soft     RED   ← --ui-danger-text
#   PAPER ← --ui-bg             AMBER ← --ui-warning-text
#                                BLUE  ← --ui-info-text
PALETTES = {
    "viethealth": {
        "NAVY": "101828",
        "TEAL": "1F7A3D",
        "MINT": "E9F5EE",
        "PAPER": "EDF2EE",
        "MUTED": "475467",
        "LINE": "DCE4DE",
        "RED": "CE181F",
        "AMBER": "B54708",
        "BLUE": "175CD3",
    },
    "chamdong": {
        "NAVY": "101828",
        "TEAL": "3A4FD0",
        "MINT": "EEF1FD",
        "PAPER": "E7ECF4",
        "MUTED": "475467",
        "LINE": "DFE4EE",
        "RED": "B42318",
        "AMBER": "B54708",
        "BLUE": "175CD3",
    },
    "thanam": {
        "NAVY": "1C1917",
        "TEAL": "9A4A1A",
        "MINT": "FAF1E8",
        "PAPER": "EFEBE3",
        "MUTED": "57534E",
        "LINE": "E5DFD6",
        "RED": "B42318",
        "AMBER": "A16207",
        "BLUE": "1E5A8A",
    },
}

# Màu trung tính dùng chung mọi palette (không có token CSS tương ứng).
WHITE = "FFFFFF"
GRID = "CBD5E1"


def active():
    """Bảng màu theo UI_PALETTE đang cấu hình.

    settings.py đã quy giá trị lạ về mặc định kèm cảnh báo log, nên nhánh
    fallback dưới đây chỉ là lớp phòng hộ khi module này được import trong
    bối cảnh thiếu cài đặt đó (ví dụ test cô lập).
    """
    return PALETTES.get(getattr(settings, "UI_PALETTE", "viethealth"), PALETTES["viethealth"])
