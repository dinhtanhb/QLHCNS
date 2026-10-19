# Chatbot trợ lý tài liệu IHRMS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm chatbot tìm kiếm tài liệu (công văn/tài liệu/quyết định + SharePoint) vào portal IHRMS, bằng parser tiếng Việt thuần quy tắc (không LLM), kèm rà soát độ phủ thông báo/email hiện có.

**Architecture:** App Django mới `apps.assistant` theo modular monolith: `nlp.parse()` → `db_search.search_database()` (ORM + `visible_dispatches_for`/`has_permission`) song song với `m365_search.search_sharepoint()` (Graph `/search/query`, fallback duyệt thư mục) → `services.ask()` gộp/xếp hạng + ghi `SearchQueryLog` → JSON API `/assistant/api/search/` → panel chat vanilla JS trên `base.html`.

**Tech Stack:** Django 5.2, Python 3.12, SQL Server (ODBC 17) + SQLite test, Microsoft Graph (msal/requests), vanilla JS/CSS theo design tokens hiện hữu.

**Spec:** `docs/superpowers/specs/2026-10-19-assistant-chatbot-design.md`

## Global Constraints

- Chỉ làm việc trên nhánh `main`; đầu mỗi Task kiểm tra `git status --short` sạch trước khi commit.
- Không đưa `.env`, dữ liệu thật, tệp đính kèm nhân sự, secret vào Git; không dùng tài khoản/danh tính ngưởi dùng thật để kiểm thử (chỉ tài khoản QA/fixtures giả).
- Server không gửi email; không bật gửi thư tự động. Không gọi API AI/LLM bên ngoài.
- Mọi query DB qua ORM; mọi endpoint mới yêu cầu đăng nhập; kết quả tài liệu lọc theo quyền server-side.
- Trường `db_table` tiếp tục prefix `tbl`; model kế thừa `BaseAuditModel` (`apps.common.models`).
- Không sửa `print_forms.css` (nếu lỡ động phải tăng `?v=` trong `base.html` và chạy print UAT).
- Commit message kiểu gitmoji-lite đang dùng: `feat(scope): …`, `test(scope): …`, `chore(scope): …`.
- Migration app mới nằm trong commit riêng có `sqlmigrate` đối chiếu 2 backend trước khi giao.

---

## File Structure

**Tạo mới:**
- `src/apps/assistant/__init__.py` — rỗng.
- `src/apps/assistant/apps.py` — AppConfig `AssistantConfig`, label `assistant`.
- `src/apps/assistant/models.py` — `SearchQueryLog(BaseAuditModel)`.
- `src/apps/assistant/nlp.py` — `ParsedQuery`, `parse(question, today=None)`.
- `src/apps/assistant/db_search.py` — `search_database(parsed, user)` + helpers nội bộ `_search_dispatches/_search_documents/_search_decisions/_score`.
- `src/apps/assistant/m365_search.py` — `search_sharepoint(parsed)` + `_fallback_listing`.
- `src/apps/assistant/services.py` — `ask(question, user)`.
- `src/apps/assistant/views.py` — `assistant_page(request)`, `api_search(request)`, `_throttle_ok(user)`.
- `src/apps/assistant/urls.py` — `app_name = "assistant"`, 2 route.
- `src/apps/assistant/admin.py` — `SearchQueryLogAdmin` read-only.
- `src/apps/assistant/tests_nlp.py`, `tests_db_search.py`, `tests_m365_search.py`, `tests_services.py`, `tests_api.py`, `tests_ui.py`.
- `src/apps/assistant/templates/assistant/chat.html`.
- `src/static/js/assistant.js`, `src/static/css/assistant.css`.

**Sửa:**
- `src/config/settings.py` — thêm `'apps.assistant'` vào `INSTALLED_APPS` (sau `'apps.lifecycle'`, dòng 141).
- `src/config/urls.py` — thêm `path("assistant/", include("apps.assistant.urls"))` sau route `reports/`.
- `src/apps/m365/graph_client.py` — thêm `search_files()`, `list_folder_files()` (cuối class `GraphClient`, trước `get_web_url`).
- `src/apps/m365/tests.py` — bổ sung 2 test class cho 2 hàm mới (mock `GraphClient._request`).
- `templates/base.html` — thêm CSS link, nút nổi `#assistantFab`, `<div id="assistantDock" hidden>`, block `extra_js`, script `assistant.js`.
- `apps/notification/tests.py` — bổ sung test độ phủ thông báo công văn (Task 9).
- `docs/PROJECT_WORK_LOG.md` — mục nhật ký đợt này (Task 10).

---

## Task 1: Scaffold app assistant + model SearchQueryLog + migration

**Files:**
- Create: `src/apps/assistant/__init__.py`, `apps.py`, `models.py`, `admin.py`, `urls.py` (placeholder views sẽ thay ở Task 7 — file chỉ định nghĩa route trỏ tới views chưa có sẽ ImportError; do đó Task 1 chỉ tạo `urls.py` ở bước cuối sau khi views tồn tại? Không — Task 1 chỉ tạo model + apps + admin, chưa gắn URL. URLs gắn ở Task 7.)
- Create: `src/apps/assistant/tests_ui.py` (chứa test model ở đây tạm? Không — tạo `tests_models.py`.)

**Interfaces:**
- Produces: `SearchQueryLog` với fields: `user` (FK security.User, related_name `assistant_search_logs`), `question` (CharField 500), `parsed_filters` (JSONField default dict), `result_count` (PositiveIntegerField), `sources` (CharField 30), `took_ms` (PositiveIntegerField), `error_note` (CharField 100, null/blank), bảng `tblAssistantSearchLog`, kế thừa `BaseAuditModel`.

- [ ] **Step 1: Viết test model**

```python
# src/apps/assistant/tests_models.py
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
        self.assertEqual(str(log.pk), str(SearchQueryLog.objects.get().pk))
```

- [ ] **Step 2: Chạy test, xác nhận fail**

```powershell
cd D:\QLHCNS\src
python manage.py test apps.assistant.tests_models -v 2
```
Kỳ vọng: FAIL — `ModuleNotFoundError: apps.assistant`.

- [ ] **Step 3: Tạo app scaffold + model**

```python
# src/apps/assistant/__init__.py  (rỗng)

# src/apps/assistant/apps.py
from django.apps import AppConfig


class AssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.assistant"
    label = "assistant"
    verbose_name = "Trợ lý tài liệu"
```

```python
# src/apps/assistant/models.py
from django.db import models
from apps.common.models import BaseAuditModel


class SearchQueryLog(BaseAuditModel):
    """Nhật ký truy vấn chatbot: không lưu nội dung/kết quả tài liệu."""

    user = models.ForeignKey(
        "security.User", on_delete=models.CASCADE,
        related_name="assistant_search_logs", db_column="UserID",
    )
    question = models.CharField("Câu hỏi", max_length=500, db_column="Question")
    parsed_filters = models.JSONField("Bộ lọc đã parse", default=dict, db_column="ParsedFilters")
    result_count = models.PositiveIntegerField("Số kết quả", default=0, db_column="ResultCount")
    sources = models.CharField("Nguồn", max_length=30, db_column="Sources")
    took_ms = models.PositiveIntegerField("Thờ gian (ms)", default=0, db_column="TookMs")
    error_note = models.CharField("Ghi chú lỗi", max_length=100, null=True, blank=True, db_column="ErrorNote")

    class Meta:
        db_table = "tblAssistantSearchLog"
        ordering = ["-created_date"]
        verbose_name = "Nhật ký truy vấn trợ lý"
        verbose_name_plural = "Nhật ký truy vấn trợ lý"
```

```python
# src/apps/assistant/admin.py
from django.contrib import admin
from .models import SearchQueryLog


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "result_count", "sources", "took_ms", "created_date")
    search_fields = ("question",)
    list_filter = ("sources",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
```

- [ ] **Step 4: Đăng ký app, tạo migration**

Sửa `src/config/settings.py` — thêm `'apps.assistant',` sau dòng 141 (`'apps.lifecycle',`):

```python
    'apps.lifecycle',
    'apps.assistant',
```

```powershell
cd D:\QLHCNS\src
python manage.py makemigrations assistant
```

- [ ] **Step 5: Chạy test pass + đối chiếu migration 2 backend**

```powershell
python manage.py test apps.assistant.tests_models -v 2
python manage.py sqlmigrate assistant 0001
```
Kỳ vọng: PASS; SQL chỉ tạo `tblAssistantSearchLog`. Để đối chiếu SQL Server: bật môi trường có `.env` trỏ SQL Server test (theo `docs/Server_Trial_Readiness_2026-09-27.md`), chạy lại `sqlmigrate assistant 0001` và lưu 2 đầu ra để chép vào work log ở Task 10. Nếu máy hiện tại không có SQL Server test, ghi nhận trong work log theo đúng mục "Khi bị giới hạn công cụ" của AGENTS.md.

- [ ] **Step 6: Commit (migration commit riêng theo AGENTS.md)**

```powershell
cd D:\QLHCNS
git add src/apps/assistant/__init__.py src/apps/assistant/apps.py src/apps/assistant/models.py src/apps/assistant/admin.py src/apps/assistant/tests_models.py src/apps/assistant/migrations src/config/settings.py
git commit -m "feat(assistant): search query log model with migration"
```

---

## Task 2: Parser câu hỏi tiếng Việt (nlp.py)

**Files:**
- Create: `src/apps/assistant/nlp.py`
- Test: `src/apps/assistant/tests_nlp.py`

**Interfaces:**
- Consumes: không gì (thuần Python).
- Produces:
  - `ParsedQuery` dataclass: `doc_number: str | None`, `phrases: list[str]`, `keywords: list[str]`, `date_from: date | None`, `date_to: date | None`, `doc_type: str | None`.
  - `parse(question: str, today: date | None = None) -> ParsedQuery`.
  - `doc_type` ∈ {`None`, `"dispatch"`, `"Incoming"`, `"Outgoing"`, `"InternalDirective"`, `"document"`, `"personnel_decision"`}.

- [ ] **Step 1: Viết test**

```python
# src/apps/assistant/tests_nlp.py
from datetime import date
from django.test import SimpleTestCase
from apps.assistant.nlp import parse, ParsedQuery


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

    def test_from_to_range(self):
        p = parse("từ 01/06/2026 đến 30/06/2026", today=date(2026, 10, 19))
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
        self.assertIn("ngân sách", p.keywords)
        for w in ("tìm", "giúp", "tôi", "về", "công", "văn", "quý"):
            self.assertNotIn(w, p.keywords)

    def test_no_diacritics_keywords_normalized(self):
        p = parse("Cong van nghi phep")
        self.assertIn("cong van nghi phep", p.keywords)  # full fallback keeps raw text
        self.assertEqual(p.doc_type, "dispatch")

    def test_fallback_whole_question_as_keywords(self):
        p = parse("abcdefgh")
        self.assertEqual(p.doc_number, None)
        self.assertEqual(p.keywords, ["abcdefgh"])

    def test_empty_and_short(self):
        self.assertEqual(parse("").keywords, [])
        self.assertEqual(parse("  a  ").keywords, [])

    def test_parse_result_is_dataclass(self):
        p = parse("công văn tháng 6", today=date(2026, 10, 19))
        self.assertIsInstance(p, ParsedQuery)
```

- [ ] **Step 2: Chạy test, xác nhận fail**

```powershell
python manage.py test apps.assistant.tests_nlp -v 2
```
Kỳ vọng: FAIL — `ModuleNotFoundError: apps.assistant.nlp`.

- [ ] **Step 3: Viết implementation**

```python
# src/apps/assistant/nlp.py
"""Parser câu hỏi tiếng Việt cho trợ lý tài liệu.

Thuần quy tắc, deterministic, không LLM. Pipeline: số hiệu → cụm ngoặc kép →
mốc thờ gian → loại văn bản → từ khóa còn lại (đã bỏ stopword).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

DOC_NUMBER_RE = re.compile(
    r"(?:số\s*)?(\d{1,5}\s*/\s*[A-Za-zÀ-ỹ0-9]+(?:\s*-\s*[A-Za-zÀ-ỹ0-9]+)*)",
    re.IGNORECASE,
)
QUOTED_RE = re.compile(r'"([^"]+)"')
MONTH_RE = re.compile(r"tháng\s+(\d{1,2})(?:\s*(?:năm|\/)\s*(\d{4}))?", re.IGNORECASE)
QUARTER_RE = re.compile(r"quý\s+([1-4])(?:\s*năm\s*(\d{4}))?", re.IGNORECASE)
YEAR_RE = re.compile(r"\bnăm\s+(\d{4})\b", re.IGNORECASE)
FROM_TO_RE = re.compile(
    r"từ\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})\s*(?:đến|tới)\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    re.IGNORECASE,
)

DOC_TYPE_KEYWORDS = [
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
    "xin", "hãy", "về", "của", "va", "và", "các", "những", "một", "là",
    "ở", "theo", "giúp", "với", "được", "bị", "trong", "ngoài", "từ", "đến",
    "ngày", "nào", "này", "đó", "mới", "gần", "nhất", "gần đây", "liên quan",
}

_TYPE_TOKENS = set()
for _label, _code in DOC_TYPE_KEYWORDS:
    _TYPE_TOKENS.update(_label.split())


@dataclass
class ParsedQuery:
    doc_number: str | None = None
    phrases: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    date_from: date | None = None
    date_to: date | None = None
    doc_type: str | None = None

    def has_constraints(self) -> bool:
        return bool(self.doc_number or self.phrases or self.keywords or self.date_from or self.date_to)


def normalize(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
        if not unicodedata.combining(c)
    )


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _parse_iso(value: str) -> date:
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return date.fromisoformat(value) if "%Y" == fmt[:2] else datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(value)


def _extract_dates(text: str, today: date) -> tuple[str, date | None, date | None]:
    match = FROM_TO_RE.search(text)
    if match:
        start = _parse_iso(match.group(1).replace("-", "/") if "-" in match.group(1) and match.group(1).count("-") == 2 else match.group(1))
        end = _parse_iso(match.group(2).replace("-", "/") if "-" in match.group(2) and match.group(2).count("-") == 2 else match.group(2))
        return (text[:match.start()] + " " + text[match.end():], start, end)

    lowered = text.casefold()
    if "tuần trước" in lowered:
        return (text.replace("tuần trước", "", 1), today - timedelta(days=7), today)
    if "tháng trước" in lowered:
        first = today.replace(day=1)
        prev_end = first - timedelta(days=1)
        return (text.replace("tháng trước", "", 1), prev_end.replace(day=1), prev_end)
    if "năm ngoái" in lowered:
        return (text.replace("năm ngoái", "", 1), date(today.year - 1, 1, 1), date(today.year - 1, 12, 31))

    match = QUARTER_RE.search(text)
    if match:
        quarter = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else today.year
        start = date(year, quarter * 3 - 2, 1)
        return (text[:match.start()] + " " + text[match.end():], start, _last_day_of_month(year, quarter * 3))

    match = MONTH_RE.search(text)
    if match:
        month = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else today.year
        if 1 <= month <= 12:
            start = date(year, month, 1)
            return (text[:match.start()] + " " + text[match.end():], start, _last_day_of_month(year, month))

    match = YEAR_RE.search(text)
    if match:
        year = int(match.group(1))
        return (text[:match.start()] + " " + text[match.end():], date(year, 1, 1), date(year, 12, 31))

    return (text, None, None)


def parse(question: str, today: date | None = None) -> ParsedQuery:
    today = today or date.today()
    text = " ".join(question.split())[:500]
    parsed = ParsedQuery()

    match = QUOTED_RE.search(text)
    if match:
        parsed.phrases = [p.strip() for p in QUOTED_RE.findall(text) if p.strip()][:5]
        text = QUOTED_RE.sub(" ", text)

    match = DOC_NUMBER_RE.search(text)
    if match:
        parsed.doc_number = re.sub(r"\s+", "", match.group(1))
        text = DOC_NUMBER_RE.sub(" ", text, count=1)

    text, parsed.date_from, parsed.date_to = _extract_dates(text, today)

    lowered = " " + normalize(text) + " "
    for label, code in DOC_TYPE_KEYWORDS:
        if f" {normalize(label)} " in lowered:
            parsed.doc_type = code
            text = re.sub(re.escape(label), " ", text, count=1, flags=re.IGNORECASE)
            break

    if parsed.doc_type in ("Incoming", "Outgoing", "InternalDirective"):
        pass  # giữ nguyên, đây là dispatch subtype
    elif parsed.doc_type == "dispatch" and any(
        normalize(k) in lowered for k in ("cong van den", "cong van di")
    ):
        # đã xử lý ở trên theo thứ tự ưu tiên; an toàn khi không trùng
        pass

    raw_tokens = text.split()
    keywords: list[str] = []
    for token in raw_tokens:
        norm = normalize(token)
        if len(norm) < 2 or norm in {normalize(w) for w in STOPWORDS} or norm in {normalize(t) for t in _TYPE_TOKENS}:
            continue
        keywords.append(norm)
    parsed.keywords = keywords[:10]

    if not parsed.has_constraints() and len(normalize(text).strip()) >= 2:
        # fallback: toàn bộ câu (đã normalize) làm từ khóa tự do
        parsed.keywords = [normalize(text).strip()[:200]]

    return parsed
```

- [ ] **Step 4: Chạy test, fix đến khi pass**

```powershell
python manage.py test apps.assistant.tests_nlp -v 2
```
Kỳ vọng: PASS toàn bộ. Chú ý test `test_no_diacritics_keywords_normalized`: normalize làm "Cong van nghi phep" → "cong van nghi phep" (đã lowercase) — fallback gán cả chuỗi.

- [ ] **Step 5: Commit**

```powershell
cd D:\QLHCNS
git add src/apps/assistant/nlp.py src/apps/assistant/tests_nlp.py
git commit -m "feat(assistant): Vietnamese query parser without LLM"
```

---

## Task 3: Tìm kiếm database (db_search.py)

**Files:**
- Create: `src/apps/assistant/db_search.py`
- Test: `src/apps/assistant/tests_db_search.py`

**Interfaces:**
- Consumes: `ParsedQuery`, `has_permission` (`apps.security.permissions`), `visible_dispatches_for` (`apps.security.data_access`), models `OfficialDispatch/Document/PersonnelDecision` (`apps.document.models`), `FORMS` (`apps.document.hcns.catalog`).
- Produces: `search_database(parsed, user) -> list[dict]`; mỗi dict: `source="ihrms"`, `type` ∈ `{"official_dispatch","document","personnel_decision"}`, `title: str`, `meta: str`, `url: str`, `date: date | None`, `score: int`.
- Quy tắc phân quyền (khớp view hiện hữu):
  - Dispatch: `visible_dispatches_for(user, qs)` — dùng y nguyên hàm này.
  - Document: `Document.objects.filter(status="Approved")` (như `document_list`).
  - PersonnelDecision: cần `manage_hr` hoặc `approve_personnel_decision`; nếu không `manage_hr` thì chỉ `PendingApproval` hoặc `history__created_by=user` (như `personnel_decision_list`).
- URL: dispatch → `reverse("portal:dispatch_detail", args=[pk])`; document → `reverse("portal:document_list")`; decision → `reverse("portal:personnel_decision_detail", args=[pk])`.

- [ ] **Step 1: Viết test**

```python
# src/apps/assistant/tests_db_search.py
from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.assistant.nlp import parse
from apps.assistant.db_search import search_database
from apps.document.models import DispatchBook, OfficialDispatch
from apps.organization.models import Department
from apps.portal import test_home_dashboard as fixtures


class DbSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user("HR_MANAGER", True)
        cls.emp = cls.user("EMPLOYEE", True)
        cls.department = Department.objects.create(
            organization=cls.department.organization if hasattr(cls, "department") else None,
            department_code="HR", department_name="Nhân sự",
        )
        cls.book = DispatchBook.objects.create(
            book_code="IN-2026", book_name="Sổ đến 2026", book_type="Incoming", year=2026,
        )
        cls.dispatch = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=cls.book, dispatch_no="128/CV-ĐN",
            title="Công văn về nghỉ phép", issuing_organization="Sở Y tế",
            issue_date=date(2026, 9, 15), received_or_sent_date=date(2026, 9, 16),
            security_level="Normal", created_by=cls.hr,
        )
        cls.confidential = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=cls.book, dispatch_no="99/TM",
            title="Tài liệu mật nội bộ", issuing_organization="Ban giám đốc",
            issue_date=date(2026, 9, 1), received_or_sent_date=date(2026, 9, 2),
            security_level="Confidential", created_by=cls.hr,
        )

    def test_hr_finds_dispatch_by_keyword(self):
        results = search_database(parse("nghỉ phép"), self.hr)
        urls = [r["url"] for r in results]
        self.assertIn(reverse("portal:dispatch_detail", args=[self.dispatch.pk]), urls)

    def test_employee_without_scope_finds_nothing(self):
        results = search_database(parse("nghỉ phép"), self.emp)
        dispatch_urls = [r for r in results if r["type"] == "official_dispatch"]
        self.assertEqual(dispatch_urls, [])

    def test_confidential_hidden_from_employee_assigned_to_other(self):
        # Nhân viên bình thường không thấy công văn mật dù biết số hiệu
        results = search_database(parse("99/TM"), self.emp)
        self.assertEqual([r for r in results if r["type"] == "official_dispatch"], [])

    def test_hr_sees_confidential(self):
        results = search_database(parse("99/TM"), self.hr)
        self.assertTrue(any(r["title"].startswith("[Công văn đến]") for r in results))

    def test_doc_number_ranks_first(self):
        results = search_database(parse("128/CV-ĐN nghỉ phép"), self.hr)
        dispatch = [r for r in results if r["type"] == "official_dispatch"]
        self.assertEqual(dispatch[0]["url"], reverse("portal:dispatch_detail", args=[self.dispatch.pk]))
        self.assertGreaterEqual(dispatch[0]["score"], 100)

    def test_date_range_filters(self):
        inside = search_database(parse("công văn tháng 9 năm 2026"), self.hr)
        self.assertIn(self.dispatch.pk, [self._pk(r) for r in inside if r["type"] == "official_dispatch"])
        outside = search_database(parse("công văn tháng 7 năm 2026"), self.hr)
        self.assertNotIn(self.dispatch.pk, [self._pk(r) for r in outside if r["type"] == "official_dispatch"])

    def test_dispatch_type_filter(self):
        results = search_database(parse("công văn đi nghỉ phép"), self.hr)
        self.assertEqual([r for r in results if r["type"] == "official_dispatch"], [])

    def test_no_constraints_returns_recent(self):
        results = search_database(parse("gần đây"), self.hr)
        # không rơ constraints → vẫn có kết quả mới nhất (cho chip gợi ý)
        self.assertTrue(results)

    def _pk(self, result):
        return int(result["url"].rstrip("/").split("/")[-1])
```

- [ ] **Step 2: Chạy test, xác nhận fail** — `ModuleNotFoundError: apps.assistant.db_search`.

- [ ] **Step 3: Viết implementation**

```python
# src/apps/assistant/db_search.py
"""Tìm kiếm tài liệu trong DB IHRMS theo ParsedQuery, tôn trọng RBAC hiện có.

Mỗi nhánh dùng đúng quy tắc visibility của view tương ứng: dispatch dùng
visible_dispatches_for; document chỉ status Approved; personnel decision theo
manage_hr / approve_personnel_decision.
"""
from __future__ import annotations

from django.db.models import Q
from django.urls import reverse

from apps.document.models import Document, OfficialDispatch, PersonnelDecision
from apps.document.hcns.catalog import FORMS
from apps.security.data_access import visible_dispatches_for
from apps.security.permissions import has_permission

from .nlp import ParsedQuery

RECENT_LIMIT = 10
SCAN_LIMIT = 50
MAX_PER_TYPE = 15


def _score(parsed: ParsedQuery, *, title: str, number: str = "", extra: tuple[str, ...] = ()) -> int:
    score = 0
    if parsed.doc_number and parsed.doc_number.casefold() in (number or "").replace(" ", "").casefold():
        score += 100
    title_fold = (title or "").casefold()
    for phrase in parsed.phrases:
        if phrase.casefold() in title_fold:
            score += 40
    for kw in parsed.keywords:
        if kw.casefold() in title_fold:
            score += 10
            continue
        for value in extra:
            if kw.casefold() in (value or "").casefold():
                score += 5
                break
    return score


def _has_constraints(parsed: ParsedQuery) -> bool:
    return parsed.has_constraints()


def _search_dispatches(parsed: ParsedQuery, user) -> list[dict]:
    if parsed.doc_type == "document" or parsed.doc_type == "personnel_decision":
        return []
    qs = visible_dispatches_for(user, OfficialDispatch.objects.select_related("dispatch_book"))
    if parsed.doc_type in ("Incoming", "Outgoing", "InternalDirective"):
        qs = qs.filter(dispatch_type=parsed.doc_type)
    if parsed.doc_number:
        qs = qs.filter(
            Q(dispatch_no__icontains=parsed.doc_number) | Q(original_doc_no__icontains=parsed.doc_number)
        )
    elif _has_constraints(parsed):
        text_q = Q()
        for phrase in parsed.phrases:
            text_q |= Q(title__icontains=phrase) | Q(issuing_organization__icontains=phrase)
        for kw in parsed.keywords:
            text_q |= Q(title__icontains=kw) | Q(issuing_organization__icontains=kw) | Q(dispatch_no__icontains=kw)
        qs = qs.filter(text_q) if text_q else qs.none()
    if parsed.date_from:
        qs = qs.filter(issue_date__gte=parsed.date_from)
    if parsed.date_to:
        qs = qs.filter(issue_date__lte=parsed.date_to)
    if not _has_constraints(parsed):
        qs = qs.order_by("-received_or_sent_date")[:RECENT_LIMIT]
    rows = []
    for d in qs.order_by("-received_or_sent_date")[:SCAN_LIMIT]:
        title = f"[{d.get_dispatch_type_display()}] {d.dispatch_no} - {d.title}"
        meta = f"{d.get_dispatch_type_display()} · {d.dispatch_no} · {d.issuing_organization}"
        score = _score(parsed, title=d.title, number=f"{d.dispatch_no} {d.original_doc_no or ''}",
                       extra=(d.issuing_organization, d.dispatch_no))
        if _has_constraints(parsed) and score == 0 and not parsed.doc_number:
            continue
        rows.append({
            "source": "ihrms", "type": "official_dispatch", "title": title, "meta": meta,
            "url": reverse("portal:dispatch_detail", args=[d.pk]),
            "date": d.issue_date, "score": score,
        })
    return rows[:MAX_PER_TYPE]


def _search_documents(parsed: ParsedQuery, user) -> list[dict]:
    if parsed.doc_type not in (None, "document") and parsed.doc_type not in ("Incoming", "Outgoing", "InternalDirective", "dispatch"):
        if parsed.doc_type != "document":
            return []
    if parsed.doc_type == "personnel_decision":
        return []
    qs = Document.objects.filter(status="Approved").select_related("category")
    if parsed.doc_number:
        qs = qs.filter(document_no__icontains=parsed.doc_number)
    elif _has_constraints(parsed):
        text_q = Q()
        for phrase in parsed.phrases:
            text_q |= Q(document_name__icontains=phrase) | Q(category__category_name__icontains=phrase)
        for kw in parsed.keywords:
            text_q |= Q(document_name__icontains=kw) | Q(document_no__icontains=kw)
        qs = qs.filter(text_q) if text_q else qs.none()
    if parsed.date_from:
        qs = qs.filter(effective_date__gte=parsed.date_from)
    if parsed.date_to:
        qs = qs.filter(effective_date__lte=parsed.date_to)
    if not _has_constraints(parsed):
        qs = qs.order_by("-effective_date")[:RECENT_LIMIT]
    rows = []
    for doc in qs.order_by("-effective_date")[:SCAN_LIMIT]:
        score = _score(parsed, title=doc.document_name, number=doc.document_no,
                       extra=(doc.category.category_name,))
        if _has_constraints(parsed) and score == 0 and not parsed.doc_number:
            continue
        rows.append({
            "source": "ihrms", "type": "document",
            "title": f"{doc.document_no} - {doc.document_name}",
            "meta": f"Tài liệu · {doc.document_no} · {doc.category.category_name}",
            "url": reverse("portal:document_list"),
            "date": doc.effective_date, "score": score,
        })
    return rows[:MAX_PER_TYPE]


def _search_decisions(parsed: ParsedQuery, user) -> list[dict]:
    if parsed.doc_type not in (None, "personnel_decision", "dispatch"):
        return []
    can_manage = has_permission(user, "manage_hr")
    if not (can_manage or has_permission(user, "approve_personnel_decision")):
        return []
    qs = PersonnelDecision.objects.select_related("employee")
    if not can_manage:
        qs = qs.filter(Q(status="PendingApproval") | Q(history__created_by=user)).distinct()
    if parsed.doc_number:
        qs = qs.filter(decision_no__icontains=parsed.doc_number)
    elif _has_constraints(parsed):
        text_q = Q()
        for phrase in parsed.phrases:
            text_q |= Q(employee__full_name__icontains=phrase) | Q(decision_no__icontains=phrase)
        for kw in parsed.keywords:
            text_q |= Q(employee__full_name__icontains=kw) | Q(employee__employee_code__icontains=kw) | Q(decision_no__icontains=kw)
        qs = qs.filter(text_q) if text_q else qs.none()
    if parsed.date_from:
        qs = qs.filter(decision_date__gte=parsed.date_from)
    if parsed.date_to:
        qs = qs.filter(decision_date__lte=parsed.date_to)
    if not _has_constraints(parsed):
        qs = qs.order_by("-created_date")[:RECENT_LIMIT]
    rows = []
    for dec in qs.order_by("-created_date")[:SCAN_LIMIT]:
        template_title = FORMS.get(dec.template_slug, {}).get("title", dec.template_slug)
        title = f"{dec.decision_no or dec.template_slug} - {template_title} - {dec.employee.full_name}"
        score = _score(parsed, title=title, number=dec.decision_no,
                       extra=(dec.employee.full_name, template_title))
        if _has_constraints(parsed) and score == 0 and not parsed.doc_number:
            continue
        rows.append({
            "source": "ihrms", "type": "personnel_decision", "title": title,
            "meta": f"Quyết định · {dec.decision_no or '—'} · {template_title}",
            "url": reverse("portal:personnel_decision_detail", args=[dec.pk]),
            "date": dec.decision_date, "score": score,
        })
    return rows[:MAX_PER_TYPE]


def search_database(parsed: ParsedQuery, user) -> list[dict]:
    return (
        _search_dispatches(parsed, user)
        + _search_documents(parsed, user)
        + _search_decisions(parsed, user)
    )
```

- [ ] **Step 4: Chạy test, fix đến khi pass** (`python manage.py test apps.assistant.tests_db_search -v 2`). Lưu ý: fixture `cls.department` cần tồn tại — nếu `HomeDashboardTests.setUpTestData` chưa tạo `cls.department`, bỏ trường organization (nullable) hoặc tạo Organization tương tự cách test_global_search dùng `self.department.organization` (test_global_search dùng fixtures có sẵn `cls.department`) — dùng y nguyên pattern từ `apps/portal/test_global_search.py` dòng 22-31.

- [ ] **Step 5: Commit**

```powershell
git add src/apps/assistant/db_search.py src/apps/assistant/tests_db_search.py
git commit -m "feat(assistant): RBAC-scoped database document search"
```

---

## Task 4: GraphClient.search_files + list_folder_files (m365)

**Files:**
- Modify: `src/apps/m365/graph_client.py` (thêm 2 method sau `get_metadata`, trước `get_web_url`)
- Test: modify `src/apps/m365/tests.py` (thêm class mới, không đổi test cũ)

**Interfaces:**
- Consumes: `GraphClient._request`, `GraphClient._drive_id`, `GraphClient.site_hostname`, `GraphClient.site_path`, `GraphAPIError`.
- Produces:
  - `GraphClient.search_files(query: str, top: int = 20) -> list[dict]` — POST `{GRAPH_BASE}/search/query`; mỗi dict `{"name": str, "web_url": str, "last_modified": str}`; chỉ giữ hit có `webUrl` bắt đầu bằng `https://{site_hostname}{site_path}`.
  - `GraphClient.list_folder_files(library_name: str, folder: str = "") -> list[dict]` — GET children của drive/folder; chỉ entry không phải folder; mỗi dict cùng schema trên.

- [ ] **Step 1: Viết test (mock `_request`)**

```python
# thêm vào src/apps/m365/tests.py
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.m365.graph_client import GraphClient


class GraphSearchTests(SimpleTestCase):
    def _client(self):
        client = GraphClient()
        client.site_hostname = "congty.sharepoint.com"
        client.site_path = "/sites/IHRMS"
        return client

    def test_search_files_filters_other_sites(self):
        client = self._client()
        payload_response = {
            "value": [{
                "hitsContainers": [{
                    "hits": [
                        {"resource": {"name": "CV-1.pdf",
                                      "webUrl": "https://congty.sharepoint.com/sites/IHRMS/CongVan/CV-1.pdf",
                                      "lastModifiedDateTime": "2026-09-01T08:00:00Z"}},
                        {"resource": {"name": "Other.docx",
                                      "webUrl": "https://congty.sharepoint.com/sites/Khac/Other.docx",
                                      "lastModifiedDateTime": "2026-09-01T08:00:00Z"}},
                    ]
                }]
            }]
        }
        with patch.object(GraphClient, "_request", return_value=_Resp(payload_response)) as mocked:
            results = client.search_files("nghỉ phép")
        self.assertEqual([r["name"] for r in results], ["CV-1.pdf"])
        args, kwargs = mocked.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/search/query"))
        self.assertEqual(kwargs["json"]["requests"][0]["entityTypes"], ["driveItem"])

    def test_list_folder_files_skips_folders(self):
        client = self._client()
        body = {"value": [
            {"name": "CV-1.pdf", "webUrl": "https://x/CV-1.pdf", "lastModifiedDateTime": "2026-09-01T08:00:00Z"},
            {"name": "Sub", "folder": {}},
        ]}
        with patch.object(GraphClient, "_request", return_value=_Resp(body)) as mocked:
            results = client.list_folder_files("Documents", "CongVan")
        self.assertEqual([r["name"] for r in results], ["CV-1.pdf"])
        self.assertIn("/root:/CongVan:/children", mocked.call_args[0][1])


class _Resp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data
```

- [ ] **Step 2: Chạy test, xác nhận fail** — `AttributeError: 'GraphClient' object has no attribute 'search_files'`.

- [ ] **Step 3: Implementation**

```python
    # thêm vào class GraphClient (sau get_metadata, trước get_web_url)
    def search_files(self, query: str, top: int = 20) -> list[dict]:
        """Tìm kiếm driveItem bằng Graph /search/query, giới hạn trong site IHRMS.

        Cần app permission cho phép search (Sites.Read.All / Sites.ReadWrite.All).
        GraphAPIError(403/400) nghĩa là chưa được consent — caller tự fallback.
        """
        self._require_configured()
        payload = {
            "requests": [{
                "entityTypes": ["driveItem"],
                "query": {"queryString": query[:200]},
                "from": 0,
                "size": top,
                "fields": ["name", "webUrl", "lastModifiedDateTime"],
            }]
        }
        data = self._request("POST", f"{GRAPH_BASE}/search/query", json=payload).json()
        prefix = f"https://{self.site_hostname}{self.site_path}"
        results = []
        for block in data.get("value", []):
            for container in block.get("hitsContainers", []):
                for hit in container.get("hits", []):
                    resource = hit.get("resource", {}) or {}
                    web_url = resource.get("webUrl") or ""
                    if web_url.startswith(prefix):
                        results.append({
                            "name": resource.get("name", ""),
                            "web_url": web_url,
                            "last_modified": resource.get("lastModifiedDateTime", ""),
                        })
                    if len(results) >= top:
                        return results
        return results

    def list_folder_files(self, library_name: str, folder: str = "") -> list[dict]:
        """Liệt kê tệp (không đệ quy) trong một thư mục của Document Library."""
        drive_id = self._drive_id(library_name)
        folder = (folder or "").strip("/")
        base = f"{GRAPH_BASE}/drives/{drive_id}/root"
        url = f"{base}:/{folder}:/children" if folder else f"{base}/children"
        data = self._request("GET", url, params={"$top": 200}).json()
        items = []
        for entry in data.get("value", []):
            if "folder" in entry:
                continue
            items.append({
                "name": entry.get("name", ""),
                "web_url": entry.get("webUrl", ""),
                "last_modified": entry.get("lastModifiedDateTime", ""),
            })
        return items
```

- [ ] **Step 4: Chạy test pass** (`python manage.py test apps.m365 -v 2` — cả file, đảm bảo test cũ không vỡ).

- [ ] **Step 5: Commit**

```powershell
git add src/apps/m365/graph_client.py src/apps/m365/tests.py
git commit -m "feat(m365): graph search and folder listing for assistant"
```

---

## Task 5: Module tìm SharePoint (m365_search.py)

**Files:**
- Create: `src/apps/assistant/m365_search.py`
- Test: `src/apps/assistant/tests_m365_search.py`

**Interfaces:**
- Consumes: `get_graph_client` (`apps.m365.graph_client`), `GraphAPIError`, settings `M365_SHAREPOINT_LIBRARY` (default `"Documents"`), `M365_FOLDER_DISPATCHES`/`M365_FOLDER_INCOMING`/`M365_FOLDER_OUTGOING` (default `CongVan`/`CongVanDen`/`CongVanDi`), `ParsedQuery`, `normalize` (`apps.assistant.nlp`).
- Produces: `search_sharepoint(parsed: ParsedQuery) -> tuple[list[dict], str | None]`; dict kết quả: `source="sharepoint"`, `type="file"`, `title=name`, `meta="SharePoint"`, `url=web_url`, `date` (date | None), `score: int`. `error_note` ∈ {`None`, `"search_fallback"`, `"unavailable"`, `"not_configured"`}.

- [ ] **Step 1: Viết test**

```python
# src/apps/assistant/tests_m365_search.py
from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.assistant.nlp import parse
from apps.assistant.m365_search import search_sharepoint
from apps.m365.graph_client import GraphAPIError


class _FakeClient:
    def __init__(self, *, configured=True, search=None, listing=None):
        self._configured = configured
        self._search = search
        self._listing = listing

    def is_configured(self):
        return self._configured

    def search_files(self, query, top=20):
        if isinstance(self._search, Exception):
            raise self._search
        return self._search

    def list_folder_files(self, library_name, folder=""):
        return self._listing or []


class SharePointSearchTests(SimpleTestCase):
    def test_not_configured(self):
        with patch("apps.assistant.m365_search.get_graph_client", return_value=_FakeClient(configured=False)):
            results, note = search_sharepoint(parse("công văn"))
        self.assertEqual((results, note), ([], "not_configured"))

    def test_search_success_maps_results(self):
        client = _FakeClient(search=[{"name": "CV nghỉ phép.pdf",
                                      "web_url": "https://x/sites/IHRMS/CongVan/CV.pdf",
                                      "last_modified": "2026-09-10T00:00:00Z"}])
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            results, note = search_sharepoint(parse('"nghỉ phép"'))
        self.assertEqual(note, None)
        self.assertEqual(results[0]["type"], "file")
        self.assertEqual(results[0]["url"], "https://x/sites/IHRMS/CongVan/CV.pdf")
        self.assertGreaterEqual(results[0]["score"], 40)

    def test_403_falls_back_to_listing(self):
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listing=[{"name": "CV nghỉ phép scan.pdf",
                                       "web_url": "https://x/CV.pdf", "last_modified": ""}])
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            results, note = search_sharepoint(parse("nghỉ phép"))
        self.assertEqual(note, "search_fallback")
        self.assertEqual(len(results), 1)

    def test_listing_filters_by_keyword(self):
        client = _FakeClient(search=GraphAPIError("Forbidden", status_code=403),
                             listing=[{"name": "CV nghỉ phép.pdf", "web_url": "u1", "last_modified": ""},
                                      {"name": "Báo cáo tài chính.pdf", "web_url": "u2", "last_modified": ""}])
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            results, note = search_sharepoint(parse("nghỉ phép"))
        self.assertEqual([r["title"] for r in results], ["CV nghỉ phép.pdf"])

    def test_network_error_returns_unavailable(self):
        client = _FakeClient(search=GraphAPIError("timeout", status_code=503))
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            results, note = search_sharepoint(parse("nghỉ phép"))
        self.assertEqual((results, note), ([], "unavailable"))

    def test_empty_query_skips(self):
        client = _FakeClient(search=[])
        with patch("apps.assistant.m365_search.get_graph_client", return_value=client):
            results, note = search_sharepoint(parse(""))
        self.assertEqual((results, note), ([], None))
```

- [ ] **Step 2: Chạy test, xác nhận fail** — `ModuleNotFoundError: apps.assistant.m365_search`.

- [ ] **Step 3: Implementation**

```python
# src/apps/assistant/m365_search.py
"""Tìm kiếm tệp trên SharePoint cho chatbot qua GraphClient.

Ưu tiên Graph /search/query; khi thiếu consent (403/400) fallback duyệt các
thư mục nghiệp vụ đã cấu hình và lọc theo tên tệp.
"""
from __future__ import annotations

from django.conf import settings

from apps.m365.graph_client import GraphAPIError, get_graph_client

from .nlp import ParsedQuery, normalize

MAX_RESULTS = 20
FALLBACK_LIMIT_PER_FOLDER = 50


def _fallback_folders() -> list[tuple[str, str]]:
    library = getattr(settings, "M365_SHAREPOINT_LIBRARY", "Documents") or "Documents"
    folders = [
        getattr(settings, "M365_FOLDER_DISPATCHES", "CongVan"),
        getattr(settings, "M365_FOLDER_INCOMING", "CongVanDen"),
        getattr(settings, "M365_FOLDER_OUTGOING", "CongVanDi"),
    ]
    seen, pairs = set(), []
    for folder in folders:
        folder = (folder or "").strip("/")
        if folder and folder not in seen:
            seen.add(folder)
            pairs.append((library, folder))
    pairs.append((library, ""))
    return pairs


def _to_result(hit: dict, parsed: ParsedQuery) -> dict:
    name = hit.get("name", "")
    name_fold = normalize(name)
    score = 0
    if parsed.doc_number and normalize(parsed.doc_number) in name_fold:
        score += 100
    for phrase in parsed.phrases:
        if normalize(phrase) in name_fold:
            score += 40
    for kw in parsed.keywords:
        if kw in name_fold:
            score += 10
    return {
        "source": "sharepoint",
        "type": "file",
        "title": name,
        "meta": "SharePoint",
        "url": hit.get("web_url", ""),
        "date": None,
        "score": score,
    }


def _fallback_listing(client, parsed: ParsedQuery) -> list[dict]:
    terms = [normalize(p) for p in parsed.phrases] + list(parsed.keywords)
    if parsed.doc_number:
        terms.append(normalize(parsed.doc_number))
    terms = [t for t in terms if t]
    if not terms:
        return []
    results: list[dict] = []
    for library, folder in _fallback_folders():
        try:
            hits = client.list_folder_files(library, folder)
        except GraphAPIError:
            continue
        for hit in hits:
            name_fold = normalize(hit.get("name", ""))
            if any(term in name_fold for term in terms):
                results.append(_to_result(hit, parsed))
        if len(results) >= MAX_RESULTS:
            break
    return results[:MAX_RESULTS]


def search_sharepoint(parsed: ParsedQuery) -> tuple[list[dict], str | None]:
    """Trả (results, error_note). error_note=None khi thành công hoặc không cấu hình.

    'search_fallback' = search API thiếu quyền, đã duyệt thư mục thay thế.
    'unavailable'     = lỗi mạng/khác — caller trả kết quả DB kèm cờ partial.
    """
    client = get_graph_client()
    if not client.is_configured():
        return [], "not_configured"
    terms = list(parsed.phrases) + list(parsed.keywords)
    query = " ".join(terms)[:200] if terms else (parsed.doc_number or "")
    if not query.strip():
        return [], None
    try:
        hits = client.search_files(query, top=MAX_RESULTS)
    except GraphAPIError as exc:
        if exc.status_code in (403, 400):
            return _fallback_listing(client, parsed), "search_fallback"
        return [], "unavailable"
    return [_to_result(hit, parsed) for hit in hits], None
```

- [ ] **Step 4: Chạy test pass** (`python manage.py test apps.assistant.tests_m365_search -v 2`).

- [ ] **Step 5: Commit**

```powershell
git add src/apps/assistant/m365_search.py src/apps/assistant/tests_m365_search.py
git commit -m "feat(assistant): sharepoint search with folder-listing fallback"
```

---

## Task 6: Orchestration services.ask + ghi log

**Files:**
- Create: `src/apps/assistant/services.py`
- Test: `src/apps/assistant/tests_services.py`

**Interfaces:**
- Consumes: `nlp.parse`, `db_search.search_database`, `m365_search.search_sharepoint`, `SearchQueryLog`.
- Produces: `ask(question: str, user) -> dict` với khóa: `query` (str), `parsed` (dict tương thích JSON), `took_ms` (int), `partial` (bool — True khi SharePoint lỗi `"unavailable"` hoặc `"search_fallback"`), `results` (list dict không có `score`). Sắp xếp: `score` giảm dần, tiebreak ngày mới nhân.

- [ ] **Step 1: Viết test**

```python
# src/apps/assistant/tests_services.py
from unittest.mock import patch

from django.test import TestCase

from apps.assistant.models import SearchQueryLog
from apps.assistant.services import ask
from apps.portal import test_home_dashboard as fixtures


class AskServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user("HR_MANAGER", True)

    def _ask(self, question, sp=None, note=None):
        with patch("apps.assistant.services.m365_search.search_sharepoint", return_value=(sp or [], note)):
            return ask(question, self.hr)

    def test_response_contract(self):
        response = self._ask("công văn nghỉ phép")
        self.assertIn("query", response)
        self.assertIn("parsed", response)
        self.assertIn("took_ms", response)
        self.assertIn("partial", response)
        self.assertIn("results", response)
        for result in response["results"]:
            self.assertNotIn("score", result)

    def test_results_sorted_by_score(self):
        db = [{"source": "ihrms", "type": "document", "title": "A", "meta": "m",
               "url": "/u1", "date": None, "score": 10},
              {"source": "ihrms", "type": "document", "title": "B", "meta": "m",
               "url": "/u2", "date": None, "score": 100}]
        with patch("apps.assistant.services.db_search.search_database", return_value=db):
            response = self._ask("công văn")
        self.assertEqual([r["title"] for r in response["results"]], ["B", "A"])

    def test_partial_flag_on_sharepoint_error(self):
        response = self._ask("công văn", note="unavailable")
        self.assertTrue(response["partial"])
        response = self._ask("công văn", note="search_fallback")
        self.assertTrue(response["partial"])
        response = self._ask("công văn", note=None)
        self.assertFalse(response["partial"])

    def test_log_written_without_scores(self):
        self._ask("công văn nghỉ phép", sp=[{"source": "sharepoint", "type": "file",
                                             "title": "f.pdf", "meta": "SharePoint",
                                             "url": "https://x", "date": None, "score": 10}])
        log = SearchQueryLog.objects.get()
        self.assertEqual(log.user, self.hr)
        self.assertEqual(log.sources, "db+sharepoint")
        self.assertIn("keywords", log.parsed_filters)
        self.assertGreaterEqual(log.took_ms, 0)

    def test_empty_results_sources_none(self):
        with patch("apps.assistant.services.db_search.search_database", return_value=[]):
            response = self._ask("zzzzz")
        log = SearchQueryLog.objects.get(question__contains="zzzzz")
        self.assertEqual(log.sources, "none")
```

- [ ] **Step 2: Chạy test, xác nhận fail** — `ModuleNotFoundError: apps.assistant.services`.

- [ ] **Step 3: Implementation**

```python
# src/apps/assistant/services.py
"""Ghép nguồn, xếp hạng và ghi nhật ký truy vấn chatbot."""
from __future__ import annotations

import time
from dataclasses import asdict

from . import db_search, m365_search, nlp
from .models import SearchQueryLog

MAX_RESULTS = 20
PARTIAL_NOTES = ("unavailable", "search_fallback")


def _iso_date(value):
    return value.isoformat() if hasattr(value, "isoformat") else None


def _parsed_dict(parsed: nlp.ParsedQuery) -> dict:
    data = asdict(parsed)
    data["date_from"] = _iso_date(parsed.date_from)
    data["date_to"] = _iso_date(parsed.date_to)
    return data


def ask(question: str, user) -> dict:
    parsed = nlp.parse(question)
    started = time.perf_counter()
    db_results = db_search.search_database(parsed, user)
    sp_results, sp_note = m365_search.search_sharepoint(parsed)
    took_ms = int((time.perf_counter() - started) * 1000)

    merged = sorted(
        db_results + sp_results,
        key=lambda r: (
            -r["score"],
            -(r["date"].toordinal() if r.get("date") else 0),
        ),
    )[:MAX_RESULTS]

    if db_results and sp_results:
        sources = "db+sharepoint"
    elif db_results:
        sources = "db"
    elif sp_results:
        sources = "sharepoint"
    else:
        sources = "none"

    SearchQueryLog.objects.create(
        user=user,
        question=question[:500],
        parsed_filters=_parsed_dict(parsed),
        result_count=len(merged),
        sources=sources,
        took_ms=took_ms,
        error_note=sp_note if sp_note in ("unavailable", "search_fallback") else None,
        created_by=user,
    )

    results = [
        {**{k: v for k, v in r.items() if k != "score"}, "date": _iso_date(r.get("date"))}
        for r in merged
    ]
    return {
        "query": question,
        "parsed": _parsed_dict(parsed),
        "took_ms": took_ms,
        "partial": sp_note in PARTIAL_NOTES,
        "results": results,
    }
```

- [ ] **Step 4: Chạy test pass** (`python manage.py test apps.assistant.tests_services -v 2`).

- [ ] **Step 5: Commit**

```powershell
git add src/apps/assistant/services.py src/apps/assistant/tests_services.py
git commit -m "feat(assistant): ask orchestration with query logging"
```

---

## Task 7: API endpoint + trang chat + rate limit

**Files:**
- Create: `src/apps/assistant/views.py`, `src/apps/assistant/urls.py`, `src/apps/assistant/templates/assistant/chat.html`, `tests_api.py`, `tests_ui.py`
- Modify: `src/config/urls.py` (thêm include), `templates/base.html` (bản edit nhẹ: block `extra_js` + 2 dòng markup — full UI ở Task 8, ở đây chỉ cần page render được; **tách bài toán**: Task 7 chỉ gắn route + trang chat.html độc lập, chưa đụng base.html để test UI không bị layout audit sớm).

**Interfaces:**
- Consumes: `services.ask`.
- Produces:
  - `GET /assistant/` → `assistant_page` render `assistant/chat.html` (extends base.html).
  - `POST /assistant/api/search/` → JSON `{"question": "..."}`; 400 `invalid_json`/`question_too_short` (len < 2), 429 `rate_limited`, 200 `services.ask(...)`.
  - `_throttle_ok(user) -> bool` — tối đa 30 request/phút/user qua `caches["default"]`.

- [ ] **Step 1: Viết test**

```python
# src/apps/assistant/tests_api.py
import json

from django.test import TestCase
from django.urls import reverse

from apps.portal import test_home_dashboard as fixtures


class AssistantApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user("HR_MANAGER", True)

    def setUp(self):
        from django.core.cache import caches
        caches["default"].clear()

    def test_anonymous_redirected(self):
        response = self.client.post(reverse("assistant:api_search"),
                                    data=json.dumps({"question": "cong van"}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 302)

    def test_get_page_renders(self):
        self.client.force_login(self.hr)
        response = self.client.get(reverse("assistant:assistant_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trợ lý tài liệu")

    def test_post_valid_question(self):
        self.client.force_login(self.hr)
        response = self.client.post(reverse("assistant:api_search"),
                                    data=json.dumps({"question": "công văn nghỉ phép"}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        self.assertIn("took_ms", payload)

    def test_short_question_400(self):
        self.client.force_login(self.hr)
        response = self.client.post(reverse("assistant:api_search"),
                                    data=json.dumps({"question": "a"}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "question_too_short")

    def test_invalid_json_400(self):
        self.client.force_login(self.hr)
        response = self.client.post(reverse("assistant:api_search"),
                                    data="{bad", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_json")

    def test_get_not_allowed_405(self):
        self.client.force_login(self.hr)
        self.assertEqual(self.client.get(reverse("assistant:api_search")).status_code, 405)

    def test_rate_limit_429(self):
        self.client.force_login(self.hr)
        url = reverse("assistant:api_search")
        last = None
        for _ in range(31):
            last = self.client.post(url, data=json.dumps({"question": "công văn"}),
                                    content_type="application/json")
        self.assertEqual(last.status_code, 429)
        self.assertEqual(last.json()["error"], "rate_limited")
```

- [ ] **Step 2: Chạy test, xác nhận fail** — `No module named 'apps.assistant.views'` hoặc `NoReverseMatch`.

- [ ] **Step 3: Implementation**

```python
# src/apps/assistant/views.py
import json

from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from . import services

RATE_LIMIT = 30
RATE_WINDOW_SECONDS = 60


def _throttle_ok(user) -> bool:
    key = f"assistant:rl:{user.pk}"
    try:
        if caches["default"].add(key, 1, RATE_WINDOW_SECONDS):
            return True
        return caches["default"].incr(key) <= RATE_LIMIT
    except ValueError:
        return True


@login_required
def assistant_page(request):
    return render(request, "assistant/chat.html")


@login_required
@require_POST
@never_cache
def api_search(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    question = str(data.get("question", "")).strip()[:500]
    if len(question) < 2:
        return JsonResponse({"error": "question_too_short"}, status=400)
    if not _throttle_ok(request.user):
        return JsonResponse({"error": "rate_limited"}, status=429)
    return JsonResponse(services.ask(question, request.user))
```

```python
# src/apps/assistant/urls.py
from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("", views.assistant_page, name="assistant_page"),
    path("api/search/", views.api_search, name="api_search"),
]
```

Sửa `src/config/urls.py`:

```python
    path("reports/", include("apps.reporting.urls")),
    path("assistant/", include("apps.assistant.urls")),
```

```html
{# src/apps/assistant/templates/assistant/chat.html #}
{% extends "base.html" %}
{% block title %}Trợ lý tài liệu{% endblock %}
{% block content %}
<div class="assistant-root assistant-page" data-api="{% url 'assistant:api_search' %}">
  <h1 class="ui-component-heading">Trợ lý tài liệu</h1>
  <p class="assistant-hint">Hỏi bằng tiếng Việt, ví dụ: <em>công văn nghỉ phép tháng 9</em>
     hoặc <em>quyết định 12/2026</em>. Kết quả giới hạn trong phạm vi quyền của anh/chị.</p>
  <div class="assistant-panel" data-role="panel" aria-live="polite"></div>
  <div class="assistant-chips" data-role="chips">
    <button type="button" class="assistant-chip" data-question="Công văn gần đây">Công văn gần đây</button>
    <button type="button" class="assistant-chip" data-question="Tài liệu gần đây">Tài liệu gần đây</button>
    <button type="button" class="assistant-chip" data-question="Quyết định tháng này">Quyết định tháng này</button>
  </div>
  <form class="assistant-form" data-role="form">
    <label class="sr-only" for="assistantInput">Câu hỏi</label>
    <input id="assistantInput" name="question" type="text" maxlength="500"
           placeholder="Nhập câu hỏi tìm tài liệu…" autocomplete="off">
    <button type="submit" class="btn btn-primary">Gửi</button>
  </form>
</div>
{% endblock %}
```

- [ ] **Step 4: Chạy test pass** (`python manage.py test apps.assistant.tests_api -v 2`).

- [ ] **Step 5: Commit**

```powershell
git add src/apps/assistant/views.py src/apps/assistant/urls.py src/apps/assistant/templates/assistant/chat.html src/apps/assistant/tests_api.py src/config/urls.py
git commit -m "feat(assistant): chat page and JSON search API with rate limit"
```

---

## Task 8: Giao diện chat — CSS, JS, tích hợp base.html

**Files:**
- Create: `src/static/css/assistant.css`, `src/static/js/assistant.js`, `src/apps/assistant/tests_ui.py`
- Modify: `templates/base.html`

**Interfaces:**
- Consumes: endpoint `assistant:api_search` (POST JSON), URL `assistant:assistant_page`.
- Produces:
  - CSS scoped `.assistant-*`, dùng token `--ui-*`; ẩn khi in (`@media print`).
  - JS: IIFE `window.IHRMSAssistant` — `initFab()` gắn `#assistantFab` (mobile < 640px chuyển trang), `initRoot(root)` gắn `.assistant-root`; render message + result cards; `partial` hiển thị cảnh báo; Enter gửi, Esc đóng panel nổi.
  - base.html: CSS link sau `atoms_ui.css` (dòng 22), nút `#assistantFab` + `<div id="assistantDock" hidden>` trước `</body>`, block `{% block extra_js %}{% endblock %}` sau `shared_components.js` (dòng 220), script `assistant.js` defer.

- [ ] **Step 1: Viết test**

```python
# src/apps/assistant/tests_ui.py
from django.test import TestCase
from django.urls import reverse

from apps.portal import test_home_dashboard as fixtures


class AssistantUiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.hr = cls.user("HR_MANAGER", True)

    def test_page_contains_root_and_api_url(self):
        self.client.force_login(self.hr)
        response = self.client.get(reverse("assistant:assistant_page"))
        self.assertContains(response, 'class="assistant-root')
        self.assertContains(response, reverse("assistant:api_search"))

    def test_base_page_renders_fab_for_logged_in(self):
        self.client.force_login(self.hr)
        response = self.client.get(reverse("portal:dashboard"))
        self.assertContains(response, 'id="assistantFab"')
        self.assertContains(response, "js/assistant.js")

    def test_fab_hidden_from_anonymous(self):
        response = self.client.get(reverse("portal:login"))
        self.assertNotContains(response, 'id="assistantFab"')
```

- [ ] **Step 2: Chạy test, xác nhận fail** — dashboard không chứa `assistantFab`.

- [ ] **Step 3: CSS**

```css
/* src/static/css/assistant.css — scoped, dùng design tokens */
.assistant-fab {
  position: fixed; right: 1.25rem; bottom: 1.25rem; z-index: 60;
  width: 3rem; height: 3rem; border-radius: 999px; border: 1px solid var(--ui-border, #d4d4d8);
  background: var(--ui-brand, #4f46e5); color: #fff; font-size: 1.25rem; cursor: pointer;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .18);
}
.assistant-fab:hover { background: var(--ui-brand-hover, var(--ui-brand, #4f46e5)); }
.assistant-dock { position: fixed; right: 1.25rem; bottom: 4.75rem; z-index: 60; }
.assistant-panel {
  width: 22rem; max-width: calc(100vw - 2rem); max-height: 70vh; overflow: auto;
  display: flex; flex-direction: column; gap: .5rem;
  background: var(--ui-bg, #fff); color: var(--ui-text-primary, #18181b);
  border: 1px solid var(--ui-border, #d4d4d8); border-radius: .75rem; padding: .75rem;
  box-shadow: 0 12px 32px rgba(0, 0, 0, .22);
}
.assistant-panel .assistant-msg { padding: .4rem .6rem; border-radius: .5rem; max-width: 92%; }
.assistant-msg.assistant-msg-user { align-self: flex-end; background: var(--ui-brand-soft, #e0e7ff); }
.assistant-msg.assistant-msg-bot { align-self: flex-start; background: var(--ui-bg, #f4f4f5); border: 1px solid var(--ui-border-subtle, #e4e4e7); }
.assistant-result { display: block; padding: .5rem .6rem; border: 1px solid var(--ui-border-subtle, #e4e4e7); border-radius: .5rem; margin-top: .35rem; text-decoration: none; color: inherit; }
.assistant-result:hover { border-color: var(--ui-brand, #4f46e5); }
.assistant-result .assistant-result-title { font-weight: 600; }
.assistant-result .assistant-result-meta { font-size: .8rem; color: var(--ui-text-muted, #71717a); }
.assistant-warning { padding: .4rem .6rem; border-radius: .5rem; background: #fef3c7; color: #92400e; font-size: .85rem; }
.assistant-error { padding: .4rem .6rem; border-radius: .5rem; background: #fee2e2; color: #991b1b; font-size: .85rem; }
.assistant-chips { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .5rem; }
.assistant-chip { border: 1px solid var(--ui-border, #d4d4d8); background: transparent; color: var(--ui-action, #4f46e5); border-radius: 999px; padding: .25rem .75rem; cursor: pointer; font-size: .85rem; }
.assistant-chip:hover { background: var(--ui-action-hover, #eef2ff); }
.assistant-form { display: flex; gap: .5rem; margin-top: .5rem; }
.assistant-form input { flex: 1; padding: .5rem .75rem; border: 1px solid var(--ui-border-control, #d4d4d8); border-radius: .5rem; background: var(--ui-bg, #fff); color: inherit; }
.assistant-page .assistant-panel { width: 100%; max-height: none; }
.assistant-hint { color: var(--ui-text-muted, #71717a); font-size: .9rem; margin: .25rem 0 .75rem; }
@media print { .assistant-fab, .assistant-dock { display: none !important; } }
@media (prefers-color-scheme: dark) {
  .assistant-msg.assistant-msg-bot { background: var(--ui-bg, #27272a); }
}
```

- [ ] **Step 4: JS**

```javascript
/* src/static/js/assistant.js — chatbot UI, vanilla JS */
(function () {
  "use strict";

  function csrfToken() {
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function renderResults(panel, payload) {
    if (payload.partial) {
      panel.appendChild(el("div", "assistant-warning",
        "SharePoint tạm không khả dụng — chỉ hiển thị kết quả trong IHRMS."));
    }
    if (!payload.results || payload.results.length === 0) {
      panel.appendChild(el("div", "assistant-msg assistant-msg-bot",
        "Không tìm thấy tài liệu phù hợp trong phạm vi quyền của anh/chị."));
      return;
    }
    var wrap = el("div", "assistant-msg assistant-msg-bot");
    payload.results.forEach(function (r) {
      var a = el("a", "assistant-result");
      a.href = r.url || "#";
      if (r.url && r.url.indexOf("http") === 0) { a.target = "_blank"; a.rel = "noopener"; }
      a.appendChild(el("div", "assistant-result-title", r.title || "(không tên)"));
      a.appendChild(el("div", "assistant-result-meta", r.meta || ""));
      wrap.appendChild(a);
    });
    panel.appendChild(wrap);
  }

  function ask(root, panel, question) {
    panel.appendChild(el("div", "assistant-msg assistant-msg-user", question));
    panel.scrollTop = panel.scrollHeight;
    fetch(root.getAttribute("data-api"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken()
      },
      body: JSON.stringify({ question: question })
    }).then(function (resp) {
      if (!resp.ok) {
        return resp.json().then(function (data) {
          throw new Error(data.error || ("HTTP " + resp.status));
        });
      }
      return resp.json();
    }).then(function (payload) {
      renderResults(panel, payload);
    }).catch(function (err) {
      panel.appendChild(el("div", "assistant-error",
        "Không thực hiện được truy vấn (" + err.message + "). Anh/chị thử lại sau."));
    }).finally(function () {
      panel.scrollTop = panel.scrollHeight;
    });
  }

  function initRoot(root) {
    var panel = root.querySelector('[data-role="panel"]');
    var form = root.querySelector('[data-role="form"]');
    var input = form ? form.querySelector("input[name='question']") : null;
    if (!panel || !form || !input) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var question = input.value.trim();
      if (question.length < 2) return;
      input.value = "";
      ask(root, panel, question);
    });
    var chips = root.querySelectorAll(".assistant-chip");
    Array.prototype.forEach.call(chips, function (chip) {
      chip.addEventListener("click", function () {
        ask(root, panel, chip.getAttribute("data-question"));
      });
    });
  }

  function initFab(fab) {
    var dock = document.getElementById("assistantDock");
    if (!dock) return;
    fab.addEventListener("click", function () {
      if (window.innerWidth < 640) {
        window.location.href = fab.getAttribute("data-page-url");
        return;
      }
      if (dock.hidden && !dock.firstChild) {
        var root = el("div", "assistant-root");
        root.setAttribute("data-api", fab.getAttribute("data-api"));
        var panel = el("div", "assistant-panel");
        panel.setAttribute("data-role", "panel");
        panel.setAttribute("aria-live", "polite");
        var form = el("form", "assistant-form");
        form.setAttribute("data-role", "form");
        var input = el("input");
        input.type = "text";
        input.maxLength = 500;
        input.setAttribute("aria-label", "Câu hỏi tìm tài liệu");
        input.placeholder = "Nhập câu hỏi…";
        var btn = el("button", "btn btn-primary", "Gửi");
        btn.type = "submit";
        form.appendChild(input);
        form.appendChild(btn);
        root.appendChild(panel);
        root.appendChild(form);
        dock.appendChild(root);
        initRoot(root);
      }
      dock.hidden = !dock.hidden;
      if (!dock.hidden) {
        var first = dock.querySelector("input");
        if (first) first.focus();
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !dock.hidden) {
        dock.hidden = true;
        fab.focus();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var fab = document.getElementById("assistantFab");
    if (fab) initFab(fab);
    var roots = document.querySelectorAll(".assistant-root");
    Array.prototype.forEach.call(roots, initRoot);
  });

  window.IHRMSAssistant = { initRoot: initRoot, initFab: initFab };
})();
```

- [ ] **Step 5: Sửa base.html**

Thêm CSS (sau dòng 22 `<link ... atoms_ui.css">`):
```html
  <link rel="stylesheet" href="{% asset 'css/assistant.css' %}">
```
Thêm trước `</body>` (sau khối script inline dòng 222-233):
```html
  {% if user.is_authenticated %}
  <button type="button" id="assistantFab" class="assistant-fab" aria-label="Mở trợ lý tài liệu"
          data-page-url="{% url 'assistant:assistant_page' %}"
          data-api="{% url 'assistant:api_search' %}">✦</button>
  <div id="assistantDock" class="assistant-dock" hidden></div>
  {% endif %}
  {% block extra_js %}{% endblock %}
  <script src="{% asset 'js/assistant.js' %}" defer></script>
```

- [ ] **Step 6: Chạy test pass** (`python manage.py test apps.assistant -v 2` — toàn app).

- [ ] **Step 7: Commit**

```powershell
git add src/static/css/assistant.css src/static/js/assistant.js src/apps/assistant/tests_ui.py templates/base.html
git commit -m "feat(assistant): floating chat widget and portal integration"
```

---

## Task 9: Rà soát độ phủ thông báo (audit + test)

**Files:**
- Modify: `src/apps/notification/tests.py` (thêm class mới)
- Modify: chỉ khi phát hiện lỗ hổng thật: view tương ứng + test (không thay đổi cơ chế gửi thư).

**Interfaces:**
- Consumes: fixture pattern `apps.portal.test_home_dashboard`; view `apps.portal.views.documents.dispatch_create/dispatch_detail`; model `Notification`.
- Produces: test xác nhận giao công văn tạo `Notification` cho ngườ được giao; cập nhật tiến độ tạo `Notification` cho ngườ tạo/giao.

Bối cảnh audit (call sites đã xác nhận khi lập kế hoạch): leave/timesheet (`apps/portal/views/attendance.py:186,444`), document (`apps/portal/views/documents.py:74,90`), dispatch (`apps/portal/views/documents.py:187,266`), personnel decision (`apps/document/hcns/views.py:527-531`), activity (`apps/activity/*`), lifecycle (`apps/lifecycle/services.py:59`), payroll (`apps/portal/views/finance.py:325,340,369`). Test hiện có `apps/notification/tests.py` đã phủ payroll/document/leave + quyền + mailto. **Khoảng trống xác nhận**: chưa có test báo cáo thông báo của luồng công văn (dispatch).

- [ ] **Step 1: Viết test bổ sung**

```python
# thêm vào src/apps/notification/tests.py
from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.document.models import DispatchBook, OfficialDispatch
from apps.notification.models import Notification
from apps.organization.models import Department
from apps.portal import test_home_dashboard as fixtures


class DispatchNotificationCoverageTests(TestCase):
    """Bổ sung độ phủ: giao công văn và cập nhật tiến độ phải tạo Notification."""

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)
        cls.admin = cls.user("SUPER_ADMIN", True)
        cls.officer = cls.user("EMPLOYEE", True)

    def _book(self):
        return DispatchBook.objects.create(
            book_code="IN-2026", book_name="Sổ đến 2026", book_type="Incoming", year=2026,
        )

    def test_dispatch_create_notifies_assignee(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("portal:dispatch_create"), {
            "dispatch_type": "Incoming",
            "dispatch_no": "500/CV",
            "original_doc_no": "",
            "title": "Công văn kiểm thử thông báo",
            "issuing_organization": "Đơn vị A",
            "issue_date": "2026-09-20",
            "received_or_sent_date": "2026-09-21",
            "urgency_level": "Normal",
            "security_level": "Normal",
            "department": "",
            "assigned_to": str(self.officer.employee_id),
            "signer": "",
            "due_date": "",
        })
        self.assertEqual(response.status_code, 302)
        dispatch = OfficialDispatch.objects.get(dispatch_no="500/CV")
        self.assertTrue(Notification.objects.filter(
            employee_id=self.officer.employee_id,
            notification_type="dispatch",
            link=f"/portal/dispatches/{dispatch.pk}/",
        ).exists())

    def test_dispatch_progress_notifies_creator(self):
        self.client.force_login(self.admin)
        dispatch = OfficialDispatch.objects.create(
            dispatch_type="Incoming", dispatch_book=self._book(), dispatch_no="501/CV",
            title="CV theo dõi", issuing_organization="Đơn vị B",
            issue_date=date(2026, 9, 20), received_or_sent_date=date(2026, 9, 21),
            assigned_to_id=self.officer.employee_id, created_by=self.admin,
        )
        self.client.force_login(self.officer)
        detail = reverse("portal:dispatch_detail", args=[dispatch.pk])
        self.client.post(detail, {
            "action_type": "Đã xử lý",
            "comment": "Hoàn tất",
            "new_status": "Completed",
        })
        self.assertTrue(Notification.objects.filter(
            employee_id=self.admin.employee_id,
            notification_type="dispatch",
        ).exists())
```

- [ ] **Step 2: Chạy test** — `python manage.py test apps.notification -v 2`. Nếu PASS: ghi nhận "coverage đầy đủ, không cần sửa view". Nếu FAIL do thiếu thông báo: vá view trong phạm vi nhỏ theo đúng pattern `notify(...)` hiện có (không đổi cơ chế email), viết lại test cho xanh, ghi rõ vào work log.

- [ ] **Step 3: Commit**

```powershell
git add src/apps/notification/tests.py
git commit -m "test(notification): dispatch notification coverage"
```

---

## Task 10: Kiểm thử tổng + UAT + work log + push

**Files:**
- Modify: `docs/PROJECT_WORK_LOG.md`

- [ ] **Step 1: Kiểm thử tự động toàn cụm**

```powershell
cd D:\QLHCNS\src
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.assistant apps.m365 apps.notification -v 1
python manage.py test apps.portal.test_global_search apps.document -v 1
```
Kỳ vọng: check OK; không migration thiếu; test pass. Chạy lại cụm `apps.assistant` với cấu hình SQL Server test (đổi `.env` theo `docs/Server_Trial_Readiness_2026-09-27.md`, KHÔNG dùng DB production): `python manage.py test apps.assistant -v 1`. Ghi cả 2 kết quả vào work log.

- [ ] **Step 2: Kiểm thử layout + browser UAT (theo AGENTS.md)**

```powershell
cd D:\QLHCNS
python ops/run_layout_alignment_audit.py
python ops/run_browser_uat.py
```
`run_layout_alignment_audit.py` bắt buộc vì đổi `base.html` + CSS dùng chung; ghi số vi phạm trước/sau, độ rộng màn, thư mục bằng chứng. Chạy `python ops/run_print_layout_uat.py` nếu audit động tới template form/bảng/in. Luồng chatbot: mở trình duyệt bằng tài khoản QA (do chủ dự án cấp, trên DB/media cô lập — không dùng danh tính thật), kiểm: mở panel từ nút nổi, hỏi "công văn gần đây", kết quả hiển thị đúng quyền, link mở được, Esc đóng panel; chụp ảnh màn hình bỏ vào thư mục bằng chứng của work log. Nếu không có tài khoản QA/chạy được script, ghi lỗi cụ thể + phần đã kiểm được, KHÔNG báo UAT hoàn tất.

- [ ] **Step 3: Bản sao review nguồn (AGENTS.md bước 6)**

Tạo bản sao nguồn ngoài repo từ các tệp được track, loại `.env`/db/media/log; thêm manifest SHA-256; xác minh lại bản sao mở được.

- [ ] **Step 4: Cập nhật `docs/PROJECT_WORK_LOG.md`** — một mục duy nhất cho đợt: ngày 2026-10-19, mục tiêu/phạm vi, tệp & phân hệ, các bước + lệnh kiểm tra + kết quả (2 backend), việc còn mở (OneDrive giai đoạn 2, Graph search consent cho IT), việc chủ dự án cần tự làm (cấp quyền Graph nếu muốn search đầy đủ; tài khoản QA UAT).

- [ ] **Step 5: Commit work log + push + xác minh**

```powershell
cd D:\QLHCNS
git add docs/PROJECT_WORK_LOG.md
git commit -m "docs: work log for assistant chatbot"
git push origin main
git rev-parse HEAD origin/main
git status --short
```
Kỳ vọng: SHA remote khớp HEAD, working tree sạch.

---

## Self-Review

**Spec coverage:**
- Parser VN không LLM → Task 2 ✓
- Tìm DB 3 model + RBAC → Task 3 ✓ (visible_dispatches_for, document Approved, decision manage/approve rule)
- SharePoint search + fallback → Task 4+5 ✓
- Gộp/xếp hạng + SearchQueryLog → Task 6 ✓
- API + rate limit + trang chat → Task 7 ✓
- UI nút nổi + base.html → Task 8 ✓
- Audit thông báo → Task 9 ✓
- Kiểm thử 2 backend + layout audit + browser UAT + work log + push → Task 10 ✓
- Global constraints (AGENTS.md) → header ✓

**Placeholder scan:** không còn TBD/TODO; mọi step có code hoặc lệnh cụ thể. Điểm duy nhất mang tính quyết định khi chạy: fixture `cls.department` trong Task 3 — đã ghi rõ fallback theo pattern test_global_search.

**Type consistency:** `ParsedQuery` dùng chung ở Task 2/3/5/6 (cùng field names); `search_sharepoint` trả tuple (results, note) dùng ở Task 5/6; result dict keys (source/type/title/meta/url/date/score) nhất quán Task 3/5/6; `ask` response keys nhất quán Task 6/7 (JsonResponse trực tiếp) và Task 8 JS (`payload.results`, `payload.partial`). Rate limit 30/phút khớp spec. URLs `assistant:assistant_page` / `assistant:api_search` khớp ở urls.py, chat.html, base.html, tests.
