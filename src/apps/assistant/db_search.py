"""Tìm kiếm tài liệu trong DB IHRMS theo `ParsedQuery`, tôn trọng RBAC hiện hữu.

Mỗi nhánh sao chép đúng quy tắc visibility của view tương ứng thay vì tự đặt ra
quy tắc mới: dispatch dùng `visible_dispatches_for`, document chỉ
`status="Approved"` (như `portal:document_list`), personnel decision theo
`manage_hr`/`approve_personnel_decision` (như
`apps/document/hcns/views.py:personnel_decision_list`).

Việc so khớp văn bản chạy trong Python trên dữ liệu đã bỏ dấu, theo đúng khuôn
`people_matches()` ở `apps/portal/views/search.py`: lấy về các dòng mà scope
cho phép (có chặn), rồi so khớp. Chỉ dùng `icontains` với từ khóa đã bỏ dấu thì
không ổn định giữa hai backend: nó khớp trên SQL Server collation tiếng Việt
nhưng không khớp trên SQLite, tức là toàn bộ test chạy khác production.
"""
from __future__ import annotations

import re

from django.db.models import F, Q
from django.urls import reverse

from apps.document.hcns.catalog import FORMS
from apps.document.models import Document, OfficialDispatch, PersonnelDecision
from apps.security.data_access import visible_dispatches_for, visible_personnel_decisions_for, visible_leave_requests_for
from apps.security.permissions import has_permission

from .nlp import ParsedQuery, normalize

RECENT_LIMIT = 10
MAX_PER_TYPE = 15
# Cùng mức chặn mà global search áp dụng cho nhân sự: bao quát một năm công văn
# và giữ chi phí của mỗi câu hỏi có biên trên.
SCAN_LIMIT = 5000

DISPATCH_SUBTYPES = ("Incoming", "Outgoing", "InternalDirective")

DISPATCH_FIELDS = (
    "pk", "dispatch_no", "original_doc_no", "title",
    "issuing_organization", "dispatch_type", "issue_date",
)
DOCUMENT_FIELDS = (
    "pk", "document_no", "document_name", "category__category_name", "effective_date",
)
DECISION_FIELDS = (
    "pk", "decision_no", "template_slug", "employee__full_name",
    "employee__employee_code", "decision_date",
)


def _needles(parsed: ParsedQuery) -> list[str]:
    return [normalize(phrase) for phrase in parsed.phrases] + list(parsed.keywords)


def _number_digits(parsed: ParsedQuery) -> str:
    """Dãy số mở đầu số hiệu - phần ASCII duy nhất an toàn cho `icontains`.

    SQL Server collation tiếng Việt khớp "CV-ĐN", SQLite thì không, nên chỉ
    phần số được đưa xuống SQL; số hiệu đầy đủ vẫn đối chiếu lại trong Python.
    """
    match = re.match(r"\d+", parsed.doc_number or "")
    return match.group() if match else ""


def _day_key(value) -> int:
    return value.toordinal() if value else 0


def _rank(candidates, parsed: ParsedQuery) -> list[tuple[object, int]]:
    """Lọc và xếp hạng các ứng viên đã bỏ dấu.

    Mỗi ứng viên là `(payload, number_blob, primary_text, extra_texts, sort_date)`
    với các text đã qua `normalize()`. `number_blob` là nơi so số hiệu văn bản,
    `primary_text` là tiêu đề (điểm cao hơn khi khớp ở đây).

    Câu hỏi chỉ có mốc thời gian hoặc loại văn bản (không từ khóa, không số
    hiệu) thì mọi ứng viên trong scope đều hợp lệ - đó là kiểu "công văn tháng
    9 năm 2026".
    """
    needles = _needles(parsed)
    number_needle = normalize(parsed.doc_number) if parsed.doc_number else ""
    scored = []
    for payload, number_blob, primary, extras, sort_date in candidates:
        if number_needle:
            if number_needle not in number_blob:
                continue
        elif needles:
            if not any(needle in value for needle in needles
                       for value in (number_blob, primary, *extras)):
                continue
        score = 100 if number_needle else 0
        for needle in needles:
            if needle in primary:
                score += 10
            elif any(needle in value for value in (number_blob, *extras)):
                score += 5
        scored.append((score, _day_key(sort_date), payload))
    scored.sort(key=lambda item: (-item[0], -item[1]))
    return [(payload, score) for score, _, payload in scored[:MAX_PER_TYPE]]


def _result(*, type_name: str, title: str, meta: str, url: str, date, score: int) -> dict:
    return {
        "source": "ihrms",
        "type": type_name,
        "title": title,
        "meta": meta,
        "url": url,
        "date": date,
        "score": score,
    }


def _dispatch_label(dispatch_type: str) -> str:
    return dict(OfficialDispatch.DISPATCH_TYPE_CHOICES).get(dispatch_type, dispatch_type)


def _dispatch_result(row, score: int) -> dict:
    pk, dispatch_no, original_doc_no, title, issuing_org, dispatch_type, issue_date = row
    label = _dispatch_label(dispatch_type)
    return _result(
        type_name="official_dispatch",
        title=f"[{label}] {dispatch_no} - {title}",
        meta=f"{label} · {dispatch_no} · {issuing_org}",
        url=reverse("portal:dispatch_detail", args=[pk]),
        date=issue_date,
        score=score,
    )


def _dispatch_candidate(row):
    number_blob, primary, extras = (
        normalize(f"{row[1]} {row[2] or ''}"),
        normalize(row[3]),
        (normalize(row[2] or ""), normalize(row[4])),
    )
    return row, number_blob, primary, extras, row[6]


def _search_dispatches(parsed: ParsedQuery, user) -> list[dict]:
    if parsed.doc_type not in (None, "dispatch", *DISPATCH_SUBTYPES):
        return []
    qs = visible_dispatches_for(user, OfficialDispatch.objects.all())
    if parsed.doc_type in DISPATCH_SUBTYPES:
        qs = qs.filter(dispatch_type=parsed.doc_type)
    digits = _number_digits(parsed)
    if digits:
        qs = qs.filter(
            Q(dispatch_no__icontains=digits) | Q(original_doc_no__icontains=digits)
        )
    if parsed.date_from:
        qs = qs.filter(issue_date__gte=parsed.date_from)
    if parsed.date_to:
        qs = qs.filter(issue_date__lte=parsed.date_to)
    qs = qs.order_by("-received_or_sent_date", "-id")

    if not parsed.has_constraints():
        rows = list(qs.values_list(*DISPATCH_FIELDS)[:RECENT_LIMIT])
        return [_dispatch_result(row, 0) for row in rows]

    candidates = qs.values_list(*DISPATCH_FIELDS)[:SCAN_LIMIT]
    return [
        _dispatch_result(row, score)
        for row, score in _rank((_dispatch_candidate(row) for row in candidates), parsed)
    ]


def _document_result(row, score: int) -> dict:
    pk, document_no, document_name, category_name, effective_date = row
    return _result(
        type_name="document",
        title=f"{document_no} - {document_name}",
        meta=f"Tài liệu · {document_no} · {category_name}",
        url=reverse("portal:document_list"),
        date=effective_date,
        score=score,
    )


def _document_candidate(row):
    number_blob, primary, extras = (
        normalize(row[1]),
        normalize(row[2]),
        (normalize(row[3]),),
    )
    return row, number_blob, primary, extras, row[4]


def _search_documents(parsed: ParsedQuery, user) -> list[dict]:
    if parsed.doc_type not in (None, "document"):
        return []
    qs = Document.objects.filter(status="Approved")
    digits = _number_digits(parsed)
    if digits:
        qs = qs.filter(document_no__icontains=digits)
    if parsed.date_from:
        qs = qs.filter(effective_date__gte=parsed.date_from)
    if parsed.date_to:
        qs = qs.filter(effective_date__lte=parsed.date_to)
    # `effective_date` có null=True. SQLite coi NULL là nhỏ nhất (DESC đẩy NULL
    # xuống cuối) còn SQL Server để NULL lên ĐẦU khi DESC, và vì `[:SCAN_LIMIT]`
    # cắt sau ORDER BY, hai backend sẽ chọn hai tập ứng viên khác nhau cho cùng
    # một dữ liệu - test chỉ xanh trên SQLite nếu fixture luôn đặt ngày.
    qs = qs.order_by(F("effective_date").desc(nulls_last=True), "-id")

    if not parsed.has_constraints():
        rows = list(qs.values_list(*DOCUMENT_FIELDS)[:RECENT_LIMIT])
        return [_document_result(row, 0) for row in rows]

    candidates = qs.values_list(*DOCUMENT_FIELDS)[:SCAN_LIMIT]
    return [
        _document_result(row, score)
        for row, score in _rank((_document_candidate(row) for row in candidates), parsed)
    ]


def _decision_result(row, score: int, template_title: str) -> dict:
    pk, decision_no, template_slug, full_name, employee_code, decision_date = row
    return _result(
        type_name="personnel_decision",
        title=f"{decision_no or template_slug} - {template_title} - {full_name}",
        meta=f"Quyết định · {decision_no or '—'} · {template_title}",
        url=reverse("portal:personnel_decision_detail", args=[pk]),
        date=decision_date,
        score=score,
    )


def _decision_candidate(row):
    template_title = FORMS.get(row[2], {}).get("title", row[2])
    payload = (row, template_title)
    number_blob, primary, extras = (
        normalize(row[1]),
        normalize(row[3]),
        (normalize(row[4]), normalize(template_title), normalize(row[2])),
    )
    return payload, number_blob, primary, extras, row[5]


def _search_decisions(parsed: ParsedQuery, user) -> list[dict]:
    if parsed.doc_type not in (None, "personnel_decision"):
        return []
    qs = visible_personnel_decisions_for(user)
    digits = _number_digits(parsed)
    if digits:
        qs = qs.filter(decision_no__icontains=digits)
    if parsed.date_from:
        qs = qs.filter(decision_date__gte=parsed.date_from)
    if parsed.date_to:
        qs = qs.filter(decision_date__lte=parsed.date_to)
    qs = qs.order_by("-created_date", "-id")

    if not parsed.has_constraints():
        rows = list(qs.values_list(*DECISION_FIELDS)[:RECENT_LIMIT])
        return [
            _decision_result(row, 0, FORMS.get(row[2], {}).get("title", row[2]))
            for row in rows
        ]

    candidates = qs.values_list(*DECISION_FIELDS)[:SCAN_LIMIT]
    ranked = []
    for (row, template_title), score in _rank(
        (_decision_candidate(row) for row in candidates), parsed
    ):
        ranked.append(_decision_result(row, score, template_title))
    return ranked


def search_database(parsed: ParsedQuery, user) -> list[dict]:
    """Trả về kết quả DB mà `user` được phép nhìn thấy, kèm điểm xếp hạng."""
    return (
        _search_dispatches(parsed, user)
        + _search_documents(parsed, user)
        + _search_decisions(parsed, user)
        + _search_business_records(parsed, user)
    )


def _search_business_records(parsed, user):
    """Object-scoped records stay DB-backed; never list raw private folders."""
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return []
    kind = parsed.doc_type
    if kind == "leave":
        qs = visible_leave_requests_for(user).select_related("employee", "leave_type")
        date_field = "from_date"
        def record(obj):
            return (f"{obj.employee.full_name} — {obj.leave_type}", obj.from_date,
                    reverse("portal:leave_list"), obj.reason or "")
    elif kind == "candidate" and has_permission(user, "view_candidate"):
        from apps.recruitment.models import Candidate
        qs = Candidate.objects.all()
        date_field = "created_date__date"
        def record(obj):
            return (f"{obj.candidate_code} — {obj.full_name}", obj.created_date.date(),
                    reverse("portal:hr_candidate_detail", args=[obj.pk]), obj.source or "")
    elif kind == "asset" and has_permission(user, "view_asset"):
        from apps.asset.models import Asset
        qs = Asset.objects.all()
        date_field = "purchase_date"
        def record(obj):
            return (f"{obj.asset_code} — {obj.asset_name}", obj.purchase_date,
                    reverse("portal:asset_admin_list"), obj.location or "")
    else:
        return []
    if parsed.date_from:
        qs = qs.filter(**{date_field + "__gte": parsed.date_from})
    if parsed.date_to:
        qs = qs.filter(**{date_field + "__lte": parsed.date_to})
    candidates = []
    for obj in qs.order_by("-pk")[:SCAN_LIMIT]:
        title, day, url, extra = record(obj)
        row = _result(type_name=kind, title=title, meta=kind, url=url, date=day, score=0)
        candidates.append((row, normalize(title), normalize(title), (normalize(extra),), day))
    return [{**row, "score": score} for row, score in _rank(candidates, parsed)]
