"""Tra cung Lỗ Ban cho từng kích thước, chấm tốt/chưa phù hợp.

MỌI hạng mục dùng DUY NHẤT thước 38.8 (âm phần) — không map thước theo
category/kind, không đối chiếu thước phụ. data/category_rules.json chỉ còn
danh sách hạng mục (categories) + checklist kích thước kỳ vọng, sửa qua UI
trang Thước.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from .models import Dimension, LobanResult, RulerKey
from .ruler import lookup

RULER: RulerKey = "38.8"  # thước duy nhất dùng cho mọi hạng mục

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
    "categories": _DEFAULT_CATEGORIES,   # danh sách hạng mục (sửa được ở UI)
    "checklist": {},                     # kích thước kỳ vọng/hạng mục (data file)
}
# key cấu hình thước cũ — bỏ khi đọc/ghi để file cũ không hồi sinh thước khác 38.8
_DROP_KEYS = ("default_ruler", "thong_thuy_ruler", "category_ruler",
              "category_kind_ruler", "cross_ruler")


def _rules_path() -> Path:
    return Path(os.environ.get("LOBAN_RULES_PATH") or _DEFAULT_PATH)


def _strip(cfg: dict) -> dict:
    return {k: v for k, v in cfg.items() if k not in _DROP_KEYS}


@lru_cache(maxsize=8)
def _load_file(path_str: str) -> dict:
    p = Path(path_str)
    if p.exists():
        cfg = json.loads(p.read_text(encoding="utf-8"))
        return {**_DEFAULT_RULES, **_strip(cfg)}
    return dict(_DEFAULT_RULES)


def load_rules() -> dict:
    return _load_file(str(_rules_path()))


def save_rules(cfg: dict) -> dict:
    merged = {**_DEFAULT_RULES, **_strip(cfg)}
    if not isinstance(merged.get("categories"), list):
        raise ValueError("categories phải là danh sách")
    p = _rules_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    _load_file.cache_clear()
    return merged


def ruler_for(category: str, kind: str) -> RulerKey:
    """Mọi hạng mục tính bằng thước 38.8 — không có ngoại lệ."""
    return RULER


def classify(dim: Dimension) -> LobanResult:
    if dim.value_mm is None:
        return LobanResult(ruler=RULER, status="khong_ap_dung")

    hit = lookup(dim.value_mm, RULER)
    return LobanResult(
        ruler=RULER,
        cung=hit.name,
        cung_nho=hit.sub_name or None,
        cung_good=hit.good,
        near_border=hit.near_border,
        border_note=hit.border_note,
        status="tot" if hit.good else "chua_phu_hop",
    )
