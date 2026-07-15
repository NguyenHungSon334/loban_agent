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

from .models import Dimension, LobanResult, RulerKey
from .ruler import lookup

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "category_rules.json"
_DEFAULT_RULES: dict = {
    "default_ruler": "38.8",
    "thong_thuy_ruler": "52.2",
    "category_ruler": {"loi_di": "52.2"},                     # lối đi = thông thủy (QT3)
    "category_kind_ruler": {"lang_tho.tong_the": "42.9"},     # lăng thờ tổng thể (QT2)
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
    p = _rules_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    _load_file.cache_clear()
    return merged


def ruler_for(category: str, kind: str) -> RulerKey:
    cfg = load_rules()
    ck_map = cfg.get("category_kind_ruler", {})
    if f"{category}.{kind}" in ck_map:
        return ck_map[f"{category}.{kind}"]
    cat_map = cfg.get("category_ruler", {})
    if category in cat_map:
        return cat_map[category]
    if kind == "thong_thuy" and cfg.get("thong_thuy_ruler"):
        return cfg["thong_thuy_ruler"]
    return cfg["default_ruler"]


def classify(dim: Dimension) -> LobanResult:
    ruler = ruler_for(dim.category, dim.kind)
    if ruler is None or dim.value_mm is None:
        return LobanResult(ruler=ruler, status="khong_ap_dung")

    hit = lookup(dim.value_mm, ruler)
    return LobanResult(
        ruler=ruler,
        cung=hit.name,
        cung_nho=hit.sub_name or None,
        cung_good=hit.good,
        near_border=hit.near_border,
        border_note=hit.border_note,
        status="tot" if hit.good else "chua_phu_hop",
    )
