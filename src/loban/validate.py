"""Lọc độ tin cậy, gom 'Cần xác nhận', cảnh báo bắt buộc (plan mục 3 bước 5, mục 6, mục 9)."""
from __future__ import annotations

from .models import AnalyzedItem, Dimension

# Độ tin cậy Thấp/chưa xác định không được dùng cho kết luận cuối.
_LOW_CONF = {"thap", "chua_xac_dinh"}

MANDATORY_WARNING = (
    "Kết quả đối chiếu Lỗ Ban xây dựng trên thông số hiện có. Các kích thước "
    "'Cần xác nhận' phải kiểm tra lại trên bản vẽ kỹ thuật hoặc tại hiện trường "
    "trước khi sản xuất và thi công. Sai số thi công ±10 mm."
)


def is_usable(dim: Dimension) -> bool:
    return dim.value_mm is not None and dim.confidence not in _LOW_CONF


def needs_confirm(dim: Dimension) -> bool:
    return dim.need_confirm or dim.value_mm is None or dim.confidence in _LOW_CONF


def mark_usability(item: AnalyzedItem) -> AnalyzedItem:
    item.usable = is_usable(item.dimension)
    return item
