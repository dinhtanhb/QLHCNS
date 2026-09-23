"""Tiện ích parse tham số an toàn từ query string / POST body.

Mục I14 (báo cáo rà soát 22/09/2026): rất nhiều view dùng thẳng
`int(request.GET.get("year"))` / `int(request.GET.get("days", 60))` trên
input người dùng — `?year=abc` hoặc `?month=13` (hợp lệ với int() nhưng vô
lý với calendar) làm view ném ValueError/OverflowError chưa bắt, Django trả
500 (và lộ traceback nếu DEBUG=True).

Dùng `parse_int()` ở đây thay cho `int()` trực tiếp trên mọi
`request.GET`/`request.POST` — không bao giờ ném exception.
"""


def parse_int(value, default=None, min_value=None, max_value=None):
    """Parse `value` thành int một cách an toàn.

    Trả về `default` nếu `value` là None/rỗng/không phải số, hoặc nằm ngoài
    khoảng [min_value, max_value] (nếu có). Không bao giờ ném exception.
    """
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    if min_value is not None and result < min_value:
        return default
    if max_value is not None and result > max_value:
        return default
    return result