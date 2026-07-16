"""Chat tư vấn Lỗ Ban — hỏi nhanh ("mộ 87x127 cung nào") hoặc hỏi/sửa trong hồ sơ.

Gemini tự gọi hàm `tra_cung` (function calling) nên số học tra cung là deterministic
(dùng chung ruler.lookup), LLM chỉ lo hiểu ngôn ngữ + chọn thước + diễn giải.
Import google-genai muộn để repo test được khi chưa cài SDK/chưa có key.
"""
from __future__ import annotations

from .config import get_settings
from .ingest import ImagePart
from .ruler import RulerKey, lookup

_RULERS: tuple[RulerKey, ...] = ("38.8", "42.9", "52.2")


def tra_cung(value_mm: float, ruler: str) -> dict:
    """Tra cung Lỗ Ban cho một kích thước.

    Args:
        value_mm: kích thước tính bằng mm (vd 870 cho 87cm, 1270 cho 1m27).
        ruler: loại thước — "38.8" (âm phần: mộ/lăng thờ/đồ thờ),
               "52.2" (thông thủy: lối đi/cửa/cổng lọt lòng),
               "42.9" (dương trạch: khối đặc/cột/hàng rào).
    """
    if ruler not in _RULERS:
        return {"loi": f"thước phải là một trong {_RULERS}"}
    h = lookup(value_mm, ruler)
    return {
        "value_mm": value_mm,
        "thuoc": ruler,
        "cung": h.name,
        "cung_nho": h.sub_name or None,
        "tot": h.good,
        "sat_bien_xau": h.near_border,
    }


_SYSTEM = """Bạn là trợ lý phong thủy Lỗ Ban của Công ty Mỹ Nghệ Hồn Đá.

# QUY TẮC TỐI QUAN TRỌNG
Bạn KHÔNG có bảng cung trong đầu và KHÔNG được tự suy tên cung. MỌI kết luận về
cung (tốt/xấu, tên cung lớn › cung nhỏ) BẮT BUỘC phải lấy từ kết quả hàm tra_cung.
Nếu chưa gọi tra_cung, TUYỆT ĐỐI không nêu bất kỳ tên cung nào. Có số là phải gọi.

Chọn thước theo hạng mục rồi GỌI tra_cung:
- 38,8cm — âm phần: mộ, lăng thờ, hộp thờ, đồ thờ cúng.
- 52,2cm — thông thủy: lối đi, cửa, cổng (khoảng lọt lòng), ô thoáng.
- 42,9cm — dương trạch: khối đặc, cột, hàng rào, bậc.
Không rõ hạng mục -> mặc định 38,8cm (âm phần).

Đổi kích thước ra mm trước khi gọi: "87" hay "87cm" -> 870mm; "1m27"/"1.27m" -> 1270mm;
số đã là mm (vd "480mm", "480") thì giữ nguyên.
Nếu khách cho nhiều số (rộng × dài), tra TỪNG số. Trả lời tiếng Việt ngắn gọn theo
đúng dữ liệu tra_cung trả về; nếu xấu hoặc sát biên thì gợi ý số đẹp gần nhất.
Khi có [Ngữ cảnh hồ sơ], ưu tiên dữ liệu hồ sơ đó.
Nếu có hàm sua_kich_thuoc và khách yêu cầu ĐỔI/SỬA số đo hạng mục, đổi số ra mm rồi
GỌI sua_kich_thuoc; sau đó báo lại cung mới. Đừng tự sửa nếu khách chỉ hỏi thông tin."""


def chat(message: str, images: list[ImagePart] | None = None,
         context: str | None = None, *, client=None, tools_extra: list | None = None) -> str:
    """Trả lời 1 lượt chat. `context` = JSON hồ sơ (nếu hỏi trong hồ sơ)."""
    from google import genai  # lazy
    from google.genai import types

    s = get_settings()
    if client is None:
        if not s.gemini_api_key:
            raise RuntimeError("Thiếu GEMINI API key (LOBAN_GEMINI_API_KEY).")
        client = genai.Client(api_key=s.gemini_api_key)

    text = message.strip()
    if not text and not images:
        raise ValueError("Không có câu hỏi và không có ảnh.")
    contents: list = [types.Part.from_bytes(data=d, mime_type=m) for d, m in (images or [])]
    if context:
        text = f"[Ngữ cảnh hồ sơ]\n{context}\n\n[Câu hỏi]\n{text}".rstrip()
    if text:
        contents.append(text)

    from .genai_retry import generate_with_retry

    resp = generate_with_retry(
        client,
        model=s.model_chat,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            tools=[tra_cung, *(tools_extra or [])],  # google-genai tự chạy hàm + lặp
            temperature=0.0,                         # số học -> quyết đoán, bớt bịa
        ),
    )
    return (resp.text or "").strip()
