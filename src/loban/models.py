"""Schema dữ liệu (pydantic v2). Ép kiểu tại boundary — plan mục 5.2."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Hạng mục gốc. Cho phép hạng mục tùy biến (cấu hình ở trang Thước) -> để str,
# danh sách khả dụng được bơm vào prompt extract để Gemini biết chọn.
# long_dinh/lang_tho tách riêng để checklist "đo gì" chính xác theo hạng mục.
KNOWN_CATEGORIES = (
    "mo", "cong", "hang_rao", "tran_phong", "long_dinh",
    "loi_di", "khoang_cach", "lang_tho", "mat_bang",
)
Category = str
# phu_bi=mép ngoài, thong_thuy=lọt sáng, lot_long=trong lòng,
# khoi=khối đặc, tong_the=kích thước tổng, hop_tho=hộp thờ/bài vị
Kind = Literal["phu_bi", "thong_thuy", "lot_long", "khoi", "tong_the", "hop_tho"]
Confidence = Literal["cao", "trung_binh", "thap", "chua_xac_dinh"]
RulerKey = Literal["38.8"]   # chỉ dùng thước 38.8 (âm phần)
Status = Literal["tot", "chua_phu_hop", "khong_ap_dung"]


class Dimension(BaseModel):
    label: str                       # "Chiều rộng mộ", "Lọt lòng cổng"...
    category: Category
    kind: Kind
    value_mm: float | None = None
    location: str = ""               # vị trí trên bản vẽ
    confidence: Confidence = "chua_xac_dinh"
    need_confirm: bool = False
    estimated: bool = False          # True nếu suy theo tỷ lệ bản vẽ


class LobanResult(BaseModel):
    ruler: RulerKey | None = None
    cung: str | None = None            # cung lớn
    cung_nho: str | None = None        # cung nhỏ (trong cung lớn)
    cung_good: bool | None = None
    near_border: bool = False
    border_note: str | None = None
    status: Status = "khong_ap_dung"


class Suggestion(BaseModel):
    lower_mm: float | None = None
    lower_cung: str | None = None
    upper_mm: float | None = None
    upper_cung: str | None = None
    delta_lower: float | None = None
    delta_upper: float | None = None
    note: str = ""


class AnalyzedItem(BaseModel):
    dimension: Dimension
    loban: LobanResult
    suggestion: Suggestion | None = None
    usable: bool = True   # False nếu tin cậy Thấp/thiếu -> không dùng kết luận cuối (mục 6)


class Profile(BaseModel):
    ho_so: str
    khach_hang: str | None = None
    dia_diem: str | None = None
    huong_cong: str | None = None
    vat_lieu: str | None = None
    dien_tich_m2: float | None = None


class ExtractionResult(BaseModel):
    """Đầu ra bước vision (Gemini) — trước khi classify."""
    dimensions: list[Dimension] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """Đầu ra 1 — dữ liệu phân tích nội bộ (plan mục 8)."""
    profile: Profile
    data_version: str
    items: list[AnalyzedItem] = Field(default_factory=list)
    need_confirm: list[str] = Field(default_factory=list)   # nhãn kích thước cần xác nhận
    near_border: list[str] = Field(default_factory=list)     # cảnh báo sát biên cung
    missing: list[str] = Field(default_factory=list)         # kích thước bắt buộc còn thiếu (checklist)
    warnings: list[str] = Field(default_factory=list)
