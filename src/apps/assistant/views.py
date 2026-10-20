"""Hai endpoint của trợ lý tài liệu: trang trò chuyện và API tìm kiếm JSON.

Toàn bộ nghiệp vụ nằm trong `services.ask`; view chỉ làm ba việc ở ranh giới:
chặn người chưa đăng nhập, chặn thân request sai dạng trước khi chạm nghiệp vụ,
và giới hạn số câu hỏi mỗi người mỗi phút.

Không có `@csrf_exempt`: `assistant.js` gửi kèm `X-CSRFToken` lấy từ cookie
`csrftoken`, đúng khuôn các trang khác trong portal.
"""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET

from . import services

MIN_QUESTION_LENGTH = 2
# Khớp `SearchQueryLog.question` (max_length=500): câu dài hơn sẽ bị cắt khi ghi
# log, nên cắt luôn ở đây để những gì hiển thị và những gì lưu là một.
MAX_QUESTION_LENGTH = 500
RATE_LIMIT = 30
RATE_WINDOW_SECONDS = 60


def _throttle_key(user) -> str:
    return f"assistant:rl:{user.pk}"


def _throttle_ok(user) -> bool:
    """Cho phép tối đa `RATE_LIMIT` câu hỏi trong `RATE_WINDOW_SECONDS`."""
    cache = caches["default"]
    key = _throttle_key(user)
    try:
        if cache.add(key, 1, RATE_WINDOW_SECONDS):
            return True
        return cache.incr(key) <= RATE_LIMIT
    except ValueError:
        # `incr` trên key vừa hết hạn giữa hai lệnh: coi như cửa sổ mới.
        return True


def _question_from(request) -> str | None:
    """Câu hỏi đã cắt gọn, hoặc `None` nếu thân request không dùng được.

    `UnicodeDecodeError` là nhánh của `ValueError` và `JSONDecodeError` cũng vậy,
    nên một lệnh bắt là đủ cho: body không phải UTF-8, body không phải JSON, và
    JSON đúng cú pháp nhưng không phải object (`"abc"`, `[1,2]`, `null`, `42`).
    """
    try:
        data = json.loads(request.body)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    return str(data.get("question", "")).strip()[:MAX_QUESTION_LENGTH]


@login_required
def assistant_page(request):
    return render(request, "assistant/chat.html")


@login_required
@require_POST
@never_cache
def api_search(request):
    question = _question_from(request)
    if question is None:
        return JsonResponse({"error": "invalid_json"}, status=400)
    # Kiểm tra định dạng trước when kiểm tra hạn mức: script gửi body sai cú pháp
    # hàng loạt không được chiếm hết suất của người dùng thật.
    if len(question) < MIN_QUESTION_LENGTH:
        return JsonResponse({"error": "question_too_short"}, status=400)
    if not _throttle_ok(request.user):
        return JsonResponse({"error": "rate_limited"}, status=429)
    if not request.user.is_active:
        return JsonResponse({"error": "session_expired"}, status=403)
    payload = services.ask(question, request.user)
    turns = _history(request)
    turns.append({"question": question, "answer": payload})
    request.session["assistant_history"] = turns[-HISTORY_LIMIT:]
    return JsonResponse(payload)


HISTORY_LIMIT = 20


def _history(request):
    # History belongs to this login, and is discarded if account privileges change.
    scope = [request.user.pk, request.user.is_active, request.user.is_superuser,
             getattr(request.user, "role_id", None)]
    if request.session.get("assistant_history_scope") != scope:
        request.session["assistant_history_scope"] = scope
        request.session["assistant_history"] = []
    return request.session.get("assistant_history", [])


@login_required
@require_GET
@never_cache
def api_history(request):
    if not request.user.is_active:
        return JsonResponse({"error": "session_expired"}, status=403)
    return JsonResponse({"turns": _history(request)})
