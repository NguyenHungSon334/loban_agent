"""Gọi Gemini có retry khi 503/429 'quá tải' — dùng chung cho extract + chat.

Gemini flash hay trả 503 'high demand' lúc cao điểm; SDK có retry sẵn nhưng bỏ
cuộc nhanh -> retry thêm với backoff, rồi báo lỗi tiếng Việt rõ ràng.
"""
from __future__ import annotations

import time

_RETRY_SLEEPS = (3, 8, 20)  # giây, tổng ~31s trước khi bỏ cuộc


def _is_overloaded(e: Exception) -> bool:
    code = getattr(e, "code", None) or getattr(e, "status_code", None)
    return code in (429, 503) or "UNAVAILABLE" in str(e) or "overloaded" in str(e).lower()


def generate_with_retry(client, **kwargs):
    """client.models.generate_content(**kwargs) + backoff khi quá tải."""
    from google.genai import errors  # lazy

    last: Exception | None = None
    for sleep_s in (*_RETRY_SLEEPS, None):
        try:
            return client.models.generate_content(**kwargs)
        except errors.APIError as e:
            last = e
            if not _is_overloaded(e) or sleep_s is None:
                break
            time.sleep(sleep_s)
    if last is not None and _is_overloaded(last):
        raise RuntimeError(
            "Model Gemini đang quá tải (503). Đã thử lại vài lần chưa được — "
            "vui lòng thử lại sau vài phút."
        ) from last
    raise last  # type: ignore[misc]
