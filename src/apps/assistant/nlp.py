"""Parser câu hỏi tiếng Việt cho trợ lý tài liệu.

Thuần quy tắc, deterministic, không LLM. Pipeline: cụm ngoặc kép → mốc thời
gian → số hiệu → loại văn bản → từ khóa còn lại (đã bỏ stopword).

Từ khóa trả về dạng token đã bỏ dấu vì đó đúng cách so sánh mà các query
`icontains` ở `db_search` áp dụng.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

DOC_NUMBER_RE = re.compile(
    r"(?:số\s*)?(\d{1,5}\s*/\s*[A-Za-zÀ-ỹ0-9]+(?:\s*-\s*[A-Za-zÀ-ỹ0-9]+)*)",
    re.IGNORECASE,
)
QUOTED_RE = re.compile(r'"([^"]+)"')
MONTH_RE = re.compile(r"tháng\s+(\d{1,2})(?:\s*(?:năm|/)\s*(\d{4}))?", re.IGNORECASE)
QUARTER_RE = re.compile(r"quý\s+([1-4])(?:\s*năm\s*(\d{4}))?", re.IGNORECASE)
YEAR_RE = re.compile(r"\bnăm\s+(\d{4})\b", re.IGNORECASE)
# Ngày ghi thuận (năm trước) cũng hay xuất hiện khi sao chép từ hệ thống khác,
# nên cả hai vế nhận 1-4 số và định dạng được phân giải ở _parse_date.
DATE_VALUE = r"\d{1,4}[/-]\d{1,2}[/-]\d{1,4}"
FROM_TO_RE = re.compile(
    rf"từ\s+({DATE_VALUE})\s*(?:đến|tới)\s+({DATE_VALUE})",
    re.IGNORECASE,
)

DOC_TYPE_KEYWORDS = [
    ("báo cáo hoạt động", "activity_report"),
    ("hồ sơ ứng viên", "candidate"),
    ("ứng viên", "candidate"),
    ("đơn xin nghỉ", "leave"),
    ("đơn nghỉ phép", "leave"),
    ("tài sản", "asset"),
    ("công văn đến", "Incoming"),
    ("công văn đi", "Outgoing"),
    ("văn bản chỉ đạo nội bộ", "InternalDirective"),
    ("chỉ đạo nội bộ", "InternalDirective"),
    ("văn bản nội bộ", "InternalDirective"),
    ("quyết định", "personnel_decision"),
    ("công văn", "dispatch"),
    ("văn bản", "dispatch"),
    ("tài liệu", "document"),
]

STOPWORDS = {
    "tìm", "kiếm", "tìm kiếm", "cho", "tôi", "mình", "em", "anh", "chị", "bạn",
    "xin", "hãy", "về", "của", "va", "và", "các", "những", "một", "là", "ở",
    "theo", "giúp", "với", "được", "bị", "trong", "ngoài", "từ", "đến", "ngày",
    "nào", "này", "đó", "mới", "gần", "nhất", "đây", "liên quan",
}

MAX_KEYWORDS = 10
MAX_PHRASES = 5


@dataclass
class ParsedQuery:
    doc_number: str | None = None
    phrases: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    date_from: date | None = None
    date_to: date | None = None
    doc_type: str | None = None

    def has_constraints(self) -> bool:
        return bool(
            self.doc_number
            or self.phrases
            or self.keywords
            or self.date_from
            or self.date_to
        )


def normalize(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
        if not unicodedata.combining(c)
    )


# normalize() chạy cho từng token của mọi câu hỏi, nên hai tập loại trừ được
# chuẩn hóa một lần tại import thay vì dựng lại trong vòng lặp.
_STOPWORDS_NORMALIZED = frozenset(normalize(word) for word in STOPWORDS)


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _strip_phrase(text: str, phrase: str) -> str:
    return re.sub(re.escape(phrase), " ", text, count=1, flags=re.IGNORECASE)


def _parse_date(value: str) -> date:
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(value)


def _date_span(first: str, second: str) -> tuple[date, date]:
    """Hai mốc "từ ... đến ...", đổi chỗ nếu bị ngược, raise nếu sai lịch."""
    start, end = _parse_date(first), _parse_date(second)
    return (start, end) if start <= end else (end, start)


def _extract_dates(text: str, today: date) -> tuple[str, date | None, date | None]:
    match = FROM_TO_RE.search(text)
    if match:
        rest = text[: match.start()] + " " + text[match.end():]
        try:
            start, end = _date_span(match.group(1), match.group(2))
        except ValueError:
            # "31/02" hay 29/02 của năm không nhuận: bỏ đúng bộ lọc thời gian,
            # giữ nguyên phần còn lại của câu đã cắt cụm ngày. Ném tiếp thì cả
            # request thành 500 và câu hỏi không bao giờ ghi được vào log.
            return rest, None, None
        return rest, start, end

    lowered = text.casefold()
    if "tuần trước" in lowered:
        return (_strip_phrase(text, "tuần trước"), today - timedelta(days=7), today)
    if "tháng trước" in lowered:
        prev_end = today.replace(day=1) - timedelta(days=1)
        return (_strip_phrase(text, "tháng trước"), prev_end.replace(day=1), prev_end)
    if "năm ngoái" in lowered:
        return (
            _strip_phrase(text, "năm ngoái"),
            date(today.year - 1, 1, 1),
            date(today.year - 1, 12, 31),
        )

    match = QUARTER_RE.search(text)
    if match:
        quarter = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else today.year
        start = date(year, quarter * 3 - 2, 1)
        end = _last_day_of_month(year, quarter * 3)
        return (text[: match.start()] + " " + text[match.end():], start, end)

    match = MONTH_RE.search(text)
    if match:
        month = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else today.year
        if 1 <= month <= 12:
            start = date(year, month, 1)
            return (
                text[: match.start()] + " " + text[match.end():],
                start,
                _last_day_of_month(year, month),
            )

    match = YEAR_RE.search(text)
    if match:
        year = int(match.group(1))
        return (
            text[: match.start()] + " " + text[match.end():],
            date(year, 1, 1),
            date(year, 12, 31),
        )

    return (text, None, None)


def parse(question: str, today: date | None = None) -> ParsedQuery:
    today = today or date.today()
    text = " ".join(question.split())[:500]
    parsed = ParsedQuery()

    if QUOTED_RE.search(text):
        parsed.phrases = [
            p.strip() for p in QUOTED_RE.findall(text) if p.strip()
        ][:MAX_PHRASES]
        text = QUOTED_RE.sub(" ", text)

    # Mốc thời gian trích trước số hiệu: DOC_NUMBER_RE cũng khớp dạng
    # "2026/06" và nếu chạy trước sẽ ăn mất nửa đầu của dải ngày.
    try:
        text, parsed.date_from, parsed.date_to = _extract_dates(text, today)
    except ValueError:
        # "quý 1 năm 0000" dựng `date()` trực tiếp từ số trong câu và cũng nổ như
        # dải ngày sai lịch. Mất bộ lọc thời gian vẫn tốt hơn 500: `text` chưa
        # bị gán lại nên các từ khóa phía dưới vẫn trích đúng.
        parsed.date_from = parsed.date_to = None

    match = DOC_NUMBER_RE.search(text)
    if match:
        parsed.doc_number = re.sub(r"\s+", "", match.group(1))
        text = DOC_NUMBER_RE.sub(" ", text, count=1)

    padded = " " + normalize(text) + " "
    for label, code in DOC_TYPE_KEYWORDS:
        if f" {normalize(label)} " in padded:
            parsed.doc_type = code
            tokens = text.split()
            label_tokens = normalize(label).split()
            for index in range(len(tokens) - len(label_tokens) + 1):
                if [normalize(token) for token in tokens[index:index + len(label_tokens)]] == label_tokens:
                    del tokens[index:index + len(label_tokens)]
                    break
            text = " ".join(tokens)
            break

    keywords: list[str] = []
    for token in text.split():
        norm = normalize(token)
        if (
            len(norm) < 2
            or norm in _STOPWORDS_NORMALIZED
        ):
            continue
        keywords.append(norm)
    parsed.keywords = keywords[:MAX_KEYWORDS]

    return parsed
