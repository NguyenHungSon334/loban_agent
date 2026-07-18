"""Map hạng mục -> thước, tra cung, chấm tốt/chưa phù hợp.

Rule category->thước cấu hình được (E, 2026-07-15) trong data/category_rules.json,
sửa qua UI trang Thước. Logic (D2c), theo thứ tự ưu tiên:
  1. (category, kind) có trong category_kind_ruler -> thước đó
     (vd lăng thờ tổng thể "lang_tho.tong_the" -> 42.9)
  2. category có trong category_ruler -> thước đó (vd lối đi -> 52.2 thông thủy)
  3. kind == thong_thuy -> thong_thuy_ruler (khe thông thủy 2 cột cổng -> 52.2)
  4. còn lại -> default_ruler (rào/cổng/mộ/lăng/cuốn thư/hộp thờ... -> 38.8)
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from .models import CrossCheck, Dimension, LobanResult, RulerKey
from .ruler import lookup

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "category_rules.json"
_DEFAULT_CATEGORIES: list[dict] = [
    {"key": "mo", "label": "Mộ"},
    {"key": "cong", "label": "Cổng đá / cột cổng"},
    {"key": "hang_rao", "label": "Hàng rào / lan can"},
    {"key": "tran_phong", "label": "Trấn phong / cuốn thư"},
    {"key": "long_dinh", "label": "Long đình / lăng thờ chung"},
    {"key": "loi_di", "label": "Lối đi / bậc tam cấp"},
    {"key": "khoang_cach", "label": "Khoảng cách bố trí"},
    {"key": "lang_tho", "label": "Lăng thờ"},
    {"key": "mat_bang", "label": "Mặt bằng khu"},
]
_DEFAULT_RULES: dict = {
    "default_ruler": "38.8",
    "thong_thuy_ruler": "52.2",
    "category_ruler": {"loi_di": "52.2"},                     # lối đi = thông thủy (QT3)
    "category_kind_ruler": {                                  # tổng thể lăng/long đình (QT2)
        "lang_tho.tong_the": "42.9",
        "long_dinh.tong_the": "42.9",
    },
    # đối chiếu THÊM thước phụ: cổng thông thủy tính cả 38.8 (khối) lẫn 52.2 (chính)
    "cross_ruler": {"cong.thong_thuy": "38.8"},
    "categories": _DEFAULT_CATEGORIES,                        # danh sách hạng mục (sửa được ở UI)
    "checklist": {},                                          # kích thước kỳ vọng/hạng mục (data file)
}
_VALID_RULERS = ("38.8", "42.9", "52.2")


def _rules_path() -> Path:
    return Path(os.environ.get("LOBAN_RULES_PATH") or _DEFAULT_PATH)


@lru_cache(maxsize=8)
def _load_file(path_str: str) -> dict:
    p = Path(path_str)
    if p.exists():
        cfg = json.loads(p.read_text(encoding="utf-8"))
        return {**_DEFAULT_RULES, **cfg}
    return dict(_DEFAULT_RULES)


def load_rules() -> dict:
    return _load_file(str(_rules_path()))


def save_rules(cfg: dict) -> dict:
    merged = {**_DEFAULT_RULES, **cfg}
    if merged["default_ruler"] not in _VALID_RULERS:
        raise ValueError("default_ruler không hợp lệ")
    for c, r in merged.get("category_ruler", {}).items():
        if r not in _VALID_RULERS:
            raise ValueError(f"thước không hợp lệ cho {c}: {r}")
    for c, r in merged.get("category_kind_ruler", {}).items():
        if r not in _VALID_RULERS:
            raise ValueError(f"thước không hợp lệ cho {c}: {r}")
    for c, r in merged.get("cross_ruler", {}).items():
        if r not in _VALID_RULERS:
            raise ValueError(f"thước phụ không hợp lệ cho {c}: {r}")
    p = _rules_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    _load_file.cache_clear()
    return merged


def ruler_for(category: str, kind: str) -> RulerKey:
    # D2c bị override: mọi hạng mục tính bằng thước 38.8, không dùng thước khác.
    return "38.8"


def _cross_for(category: str, kind: str, primary: RulerKey) -> RulerKey | None:
    """Thước phụ đối chiếu thêm — tắt: chỉ dùng thước 38.8."""
    return None


def classify(dim: Dimension) -> LobanResult:
    ruler = ruler_for(dim.category, dim.kind)
    if ruler is None or dim.value_mm is None:
        return LobanResult(ruler=ruler, status="khong_ap_dung")

    hit = lookup(dim.value_mm, ruler)
    cross = None
    alt = _cross_for(dim.category, dim.kind, ruler)
    if alt is not None:
        ch = lookup(dim.value_mm, alt)
        cross = CrossCheck(
            ruler=alt, cung=ch.name, cung_nho=ch.sub_name or None,
            cung_good=ch.good, status="tot" if ch.good else "chua_phu_hop",
        )
    return LobanResult(
        ruler=ruler,
        cung=hit.name,
        cung_nho=hit.sub_name or None,
        cung_good=hit.good,
        near_border=hit.near_border,
        border_note=hit.border_note,
        status="tot" if hit.good else "chua_phu_hop",
        cross=cross,
    )
