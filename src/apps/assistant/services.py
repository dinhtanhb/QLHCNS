"""Ghép hai nguồn tài liệu, xếp hạng và ghi nhật ký cho một câu hỏi chatbot.

`ask` là chỗ duy nhất biết cả `db_search` lẫn `m365_search`, nên view (T7) chỉ
việc gọi nó. Quy tắc chết người ở đây là gì chết được cái gì:

- DB là nguồn chính và là nguồn có RBAC. Lỗi ORM ở đây là lỗi server thật, phải
  leo lên view để thành 500 + log, tuyệt đối không được hóa thành "0 kết quả" -
  người dùng sẽ tưởng mình không có quyền trong khi hệ thống đang hỏng.
- SharePoint là nguồn phụ, chạy qua mạng. MọiExceptions từ nó (kể cả lỗi dựng
  dict từ một DriveItem kỳ dị) bị nuốt và báo bằng `error_note`, để câu hỏi vẫn
  còn câu trả lời DB.
- Nhật ký chỉ chứa câu hỏi, bộ lọc và số lượng; không chứa tiêu đề/URL kết quả.
"""
from __future__ import annotations

import time
from dataclasses import asdict
from django.core import signing
from django.urls import reverse

from . import db_search, m365_search, nlp
from .models import SearchQueryLog

MAX_RESULTS = 20
# Hai trạng thái này nghĩa là "câu trả lời chưa đầy đủ" và UI phải nói rõ.
# `not_configured` (nguồn chưa bật) và `restricted` (người hỏi không thuộc phạm vi
# nguồn SharePoint) thì không: đó là trạng thái bình thường, không phải sự cố.
PARTIAL_NOTES = ("unavailable", "search_fallback")


def _iso_date(value):
    return value.isoformat() if hasattr(value, "isoformat") else None


def _day_key(value) -> int:
    return value.toordinal() if hasattr(value, "toordinal") else 0


def _parsed_dict(parsed: nlp.ParsedQuery) -> dict:
    data = asdict(parsed)
    data["date_from"] = _iso_date(parsed.date_from)
    data["date_to"] = _iso_date(parsed.date_to)
    return data


def _search_sharepoint(parsed: nlp.ParsedQuery, user) -> m365_search.SharePointSearchResult:
    try:
        res = m365_search.search_sharepoint(parsed, user)
    except Exception:
        # GraphAPIError đã được m365_search xử lý; nhánh này chặn lỗi dữ liệu
        # lạ từ SharePoint để nó không kéo theo cả câu trả lời.
        return m365_search.SharePointSearchResult([], "unavailable")
    if isinstance(res, m365_search.SharePointSearchResult):
        return res
    results, note = res
    return m365_search.SharePointSearchResult(results, note, undated_count=getattr(res, "undated_count", 0))


def _public_result(row: dict) -> dict:
    result = {key: value for key, value in row.items() if key != "score"}
    result["date"] = _iso_date(row.get("date"))
    if row.get("source") == "sharepoint" and row.get("url"):
        token = signing.dumps(row["url"], salt="assistant-file", compress=True)
        result["url"] = reverse("assistant:sharepoint_file", args=[token])
        result["download_url"] = result["url"] + "?download=1"
    return result


def ask(question: str, user) -> dict:
    """Trả `{"query","parsed","took_ms","partial","results"}` cho `user`."""
    parsed = nlp.parse(question)
    started = time.perf_counter()
    db_results = db_search.search_database(parsed, user)
    sp_res = _search_sharepoint(parsed, user)
    sp_results, sp_note = sp_res[0], sp_res[1]
    sp_undated = getattr(sp_res, "undated_count", 0)
    took_ms = int((time.perf_counter() - started) * 1000)

    merged = sorted(
        db_results + sp_results,
        # Điểm giảm dần, cùng điểm thì bản mới hơn lên trước. `reverse` trên cả
        # hai khóa sẽ đảo luôn cả thứ tự chèn, nên sort key tường minh.
        key=lambda row: (-row["score"], -_day_key(row.get("date"))),
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
        error_note=sp_note if sp_note in PARTIAL_NOTES else None,
        created_by=user,
    )

    response = {
        "query": question,
        "parsed": _parsed_dict(parsed),
        "took_ms": took_ms,
        "partial": sp_note in PARTIAL_NOTES,
        "sharepoint_status": sp_note or "ok",
        "results": [_public_result(row) for row in merged],
    }
    if sp_undated > 0:
        response["undated_count"] = sp_undated
        response["undated_notice"] = f"còn {sp_undated} tệp trong thư mục chưa xác định được ngày"
    return response
