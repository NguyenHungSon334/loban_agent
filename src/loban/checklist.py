"""Đối chiếu 'đo đủ chưa': so kích thước bóc được với checklist kỳ vọng/hạng mục.

Checklist cấu hình trong data/category_rules.json (sửa ở UI trang Thước):
  "checklist": { "<category>": [ {label, kind?, match?, required} ] }

Khớp 1 item với kích thước đã bóc:
  - có `match` (từ khóa) -> chỉ cần 1 từ khóa xuất hiện trong nhãn (bỏ dấu) là đủ;
    (từ khóa là bộ phân biệt thật: dài/rộng/cao/thông thiên/ô chờ/kim tinh...)
  - không có `match` -> khớp theo `kind`.
Chỉ báo thiếu cho hạng mục ĐÃ xuất hiện ≥1 kích thước (bộ phận có trên bản vẽ),
tránh nhiễu khi bản vẽ vốn không có hạng mục đó. Chỉ báo item required=true.
"""
from __future__ import annotations

import unicodedata

from .models import Dimension


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def _satisfied(item: dict, cat_dims: list[Dimension]) -> bool:
    keys = [_norm(k) for k in (item.get("match") or [])]
    kind = item.get("kind")
    for d in cat_dims:
        if keys:
            label = _norm(d.label)
            if any(k in label for k in keys):
                return True
        elif kind and d.kind == kind:
            return True
    return False


def _cat_label(cfg: dict, cat: str) -> str:
    for c in cfg.get("categories") or []:
        if c.get("key") == cat:
            return c.get("label", cat)
    return cat


def check_completeness(dims: list[Dimension], cfg: dict) -> list[str]:
    """Trả danh sách 'Nhãn thiếu (Hạng mục)' cho item required chưa đo được."""
    checklist = cfg.get("checklist") or {}
    present = {d.category for d in dims}
    missing: list[str] = []
    for cat, items in checklist.items():
        if cat not in present:
            continue
        cat_dims = [d for d in dims if d.category == cat]
        for item in items:
            if not item.get("required"):
                continue
            if not _satisfied(item, cat_dims):
                missing.append(f"{item['label']} ({_cat_label(cfg, cat)})")
    return missing
