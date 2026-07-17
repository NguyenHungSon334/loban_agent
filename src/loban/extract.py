"""Bước vision: gọi Gemini bóc tách kích thước -> ExtractionResult (plan mục 3 bước 2, P3).

- LLM CHỈ đọc số/nhãn; không tính cung (classify.py lo).
- Ép JSON bằng response_schema. Nếu SDK không parse được (union/None phức tạp),
  fallback json.loads thủ công.
- Import google-genai muộn để repo vẫn import/test được khi chưa cài SDK/chưa có key.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import get_settings
from .ingest import ImagePart
from .models import ExtractionResult

_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "extract_system.md"
_GENAI_TIMEOUT_MS = 120_000  # 2 phút/call; call treo -> fail để consumer worker chạy tiếp job sau


def _system_prompt() -> str:
    base = _PROMPT_PATH.read_text(encoding="utf-8")
    from .classify import load_rules
    from .models import KNOWN_CATEGORIES

    cfg = load_rules()
    # danh sách hạng mục cấu hình được (kèm nhãn) -> để Gemini chọn đúng key.
    cats = cfg.get("categories") or [{"key": k} for k in KNOWN_CATEGORIES]
    lines = [f"- {c['key']}: {c.get('label', c['key'])}" for c in cats if c.get("key")]
    if lines:
        base += "\n\n# Hạng mục khả dụng (dùng ĐÚNG key bên trái)\n" + "\n".join(lines)
    return base


def _build_client(api_key: str | None):
    from google import genai  # lazy

    key = api_key or get_settings().gemini_api_key
    if not key:
        raise RuntimeError("Thiếu GEMINI API key. Đặt LOBAN_GEMINI_API_KEY trong .env.")
    # timeout để 1 call treo (network stall) không wedge consumer worker mãi mãi.
    return genai.Client(api_key=key, http_options={"timeout": _GENAI_TIMEOUT_MS})


def extract(
    images: list[ImagePart],
    employee_note: str = "",
    *,
    light: bool = False,
    client=None,
    api_key: str | None = None,
) -> ExtractionResult:
    """Bóc tách kích thước từ ảnh. `light=True` dùng model flash (rẻ hơn)."""
    if not images and not employee_note.strip():
        raise ValueError("Không có ảnh và không có số đo đầu vào.")

    from google.genai import types  # lazy

    settings = get_settings()
    client = client or _build_client(api_key)
    model = settings.model_extract_light if light else settings.model_extract

    contents: list = [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in images]
    if images:
        user_text = "Bóc tách toàn bộ kích thước nhìn thấy rõ theo schema."
        if employee_note.strip():
            user_text += f"\n\nGhi chú nhân viên nhập (nguồn ưu tiên 3):\n{employee_note.strip()}"
    else:
        # Không có ảnh -> bóc tách từ mô tả số đo người dùng nhập.
        user_text = (
            "Không có ảnh bản vẽ. Bóc tách kích thước từ mô tả số đo dưới đây "
            f"theo schema:\n{employee_note.strip()}"
        )
    contents.append(user_text)

    from .genai_retry import generate_with_retry

    resp = generate_with_retry(
        client,
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=_system_prompt(),
            response_mime_type="application/json",
            response_schema=ExtractionResult,
            temperature=settings.extract_temperature,
        ),
    )
    return _parse(resp)


def _parse(resp) -> ExtractionResult:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, ExtractionResult):
        return parsed
    # Fallback: parse text thủ công.
    text = getattr(resp, "text", None)
    if not text:
        raise RuntimeError("Gemini không trả nội dung parse được.")
    return ExtractionResult.model_validate(json.loads(text))
