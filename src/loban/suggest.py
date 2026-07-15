"""Đề xuất kích thước tốt gần nhất (dưới/trên) trong biên độ QT5 (plan mục 6.2, D6, D8).

Nguyên tắc:
- Đề xuất phải rơi cung TỐT và KHÁC cung hiện tại (cùng cung tốt = không phải phương án mới).
- Quét từng mm ra hai phía trong biên độ theo hạng mục.
- Kích thước đã Tốt vẫn hiện đề xuất dưới/trên (D6), kèm ghi chú "đang đạt".
- Lối đi: ưu tiên tăng; giảm chỉ khi đảm bảo công năng (agent không tự quyết -> ghi chú).
- Không có phương án trong biên độ -> "Cần kiến trúc sư điều chỉnh mặt bằng".
"""
from __future__ import annotations

from .models import AnalyzedItem, Dimension, LobanResult, Suggestion
from .ruler import CungHit, lookup

# category -> (biên độ ưu tiên, biên độ mở rộng) mm. D8 (QT5).
_RANGE: dict[str, tuple[int, int]] = {
    "mo": (50, 100),
    "cong": (50, 50),
    "lang_tho": (100, 100),
    "loi_di": (100, 100),
    # khối/khu lớn: biên rộng để chắc chắn tìm được cung tốt hai phía
    "mat_bang": (100, 300),
    "khoang_cach": (100, 300),
}


def _search(value: float, ruler: str, direction: int, max_r: int, exclude_index: int) -> CungHit | None:
    """Quét ±1mm tìm cung tốt gần nhất khác cung hiện tại."""
    for d in range(1, max_r + 1):
        v = value + direction * d
        if v < 0:
            break
        hit = lookup(v, ruler)
        if hit.good and hit.index != exclude_index:
            return hit
    return None


def _search_side(value: float, ruler: str, direction: int, r_pref: int, r_ext: int, exclude_index: int) -> CungHit | None:
    hit = _search(value, ruler, direction, r_pref, exclude_index)
    if hit is None and r_ext > r_pref:
        hit = _search(value, ruler, direction, r_ext, exclude_index)
    return hit


def suggest(dim: Dimension, loban: LobanResult) -> Suggestion | None:
    if loban.ruler is None or dim.value_mm is None:
        return None
    if dim.category not in _RANGE:
        return None

    r_pref, r_ext = _RANGE[dim.category]
    value = dim.value_mm
    cur = lookup(value, loban.ruler)

    lower = _search_side(value, loban.ruler, -1, r_pref, r_ext, cur.index)
    upper = _search_side(value, loban.ruler, +1, r_pref, r_ext, cur.index)

    s = Suggestion()
    if lower:
        s.lower_mm = lower.value_mm
        s.lower_cung = lower.name
        s.delta_lower = round(value - lower.value_mm, 1)
    if upper:
        s.upper_mm = upper.value_mm
        s.upper_cung = upper.name
        s.delta_upper = round(upper.value_mm - value, 1)

    s.note = _note(dim, loban, lower, upper, max(r_pref, r_ext))
    return s


def _note(dim: Dimension, loban: LobanResult, lower, upper, max_r: int) -> str:
    parts: list[str] = []
    if loban.status == "tot":
        parts.append(f"Đang đạt cung {loban.cung}.")
        if loban.near_border:
            parts.append("Sát biên cung xấu — cân nhắc chỉnh xa biên.")
    if lower is None and upper is None:
        parts.append(f"Không có cung tốt khác trong biên độ ±{max_r} mm. Cần kiến trúc sư điều chỉnh mặt bằng.")
        return " ".join(parts)
    if dim.category == "loi_di":
        parts.append("Ưu tiên tăng kích thước; chỉ giảm nếu vẫn đảm bảo công năng.")
    return " ".join(parts).strip()


def analyze(dim: Dimension, loban: LobanResult) -> AnalyzedItem:
    return AnalyzedItem(dimension=dim, loban=loban, suggestion=suggest(dim, loban))
