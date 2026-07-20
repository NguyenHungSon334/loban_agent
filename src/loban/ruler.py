"""Tra cung Lỗ Ban từ kích thước mm.

Toàn bộ toán cung nằm ở đây — deterministic, không phụ thuộc LLM.
Công thức (plan mục 5.1 / 6.1):
    pos = value_mm mod cycle_mm
    cung = khoảng [start_mm, end_mm) chứa pos
    near_border = pos cách biên của một cung XẤU kề bên <= border_mm
                  (chỉ có nghĩa khi cung hiện tại là Tốt — rủi ro lệch cung
                   khi sai số thi công ±10mm, quyết định D7)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

RulerKey = str  # chỉ dùng "38.8" (bảng thước khác còn trong data nhưng không dùng)

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "loban_data.json"


@dataclass(frozen=True)
class CungHit:
    ruler: RulerKey
    value_mm: float
    pos_mm: float      # value_mm mod cycle_mm
    index: int         # chỉ số cung LỚN 0-based
    name: str          # tên cung lớn
    good: bool
    near_border: bool
    border_note: str | None = None
    sub_index: int = 0        # chỉ số cung NHỎ trong cung lớn (0-based)
    sub_name: str = ""        # tên cung nhỏ


@lru_cache(maxsize=1)
def load_data(path: str | None = None) -> dict:
    p = Path(path) if path else _DATA_PATH
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def rulers() -> dict:
    return load_data()["rulers"]


def lookup(value_mm: float, ruler: RulerKey, data: dict | None = None) -> CungHit:
    """Tra cung cho một kích thước. Raise KeyError/ValueError nếu input sai."""
    d = data or load_data()
    if value_mm < 0:
        raise ValueError(f"value_mm phải >= 0, nhận {value_mm}")
    if ruler not in d["rulers"]:
        raise KeyError(f"Thước không hợp lệ: {ruler!r}. Hợp lệ: {list(d['rulers'])}")

    border_mm = float(d.get("border_mm", 10.0))
    r = d["rulers"][ruler]
    cycle = float(r["cycle_mm"])
    cungs = r["cung"]
    pos = value_mm % cycle

    idx = _find_index(pos, cungs, cycle)
    hit = cungs[idx]
    near, note = _near_border(pos, idx, cungs, hit, border_mm)
    sub_idx, sub_name = _sub_cung(pos, hit, r)

    return CungHit(
        ruler=ruler,
        value_mm=float(value_mm),
        pos_mm=round(pos, 4),
        index=idx,
        name=hit["name"],
        good=bool(hit["good"]),
        near_border=near,
        border_note=note,
        sub_index=sub_idx,
        sub_name=sub_name,
    )


def _sub_cung(pos: float, hit: dict, ruler_data: dict) -> tuple[int, str]:
    """Cung nhỏ = chia đều cung lớn; kế thừa tốt/xấu từ cung lớn."""
    subs = hit.get("sub") or []
    if not subs:
        return 0, ""
    step = float(ruler_data.get("sub_step_mm") or (hit["end_mm"] - hit["start_mm"]) / len(subs))
    offset = pos - hit["start_mm"]
    i = int(offset // step)
    i = max(0, min(i, len(subs) - 1))   # kẹp trong biên (sai số float)
    return i, subs[i]


def _find_index(pos: float, cungs: list[dict], cycle: float) -> int:
    for i, c in enumerate(cungs):
        if c["start_mm"] <= pos < c["end_mm"]:
            return i
    # pos == cycle chỉ xảy ra do lỗi float; gán về cung cuối cho an toàn.
    if pos >= cycle - 1e-9:
        return len(cungs) - 1
    raise ValueError(f"Không tìm thấy cung cho pos={pos} (cycle={cycle}) — dữ liệu thước hở khoảng.")


def _near_border(
    pos: float, idx: int, cungs: list[dict], hit: dict, border_mm: float
) -> tuple[bool, str | None]:
    # Chỉ cảnh báo khi cung hiện tại Tốt (D7): số tốt nhưng sát cung xấu.
    if not hit["good"]:
        return False, None

    n = len(cungs)
    prev = cungs[(idx - 1) % n]
    nxt = cungs[(idx + 1) % n]
    dist_low = pos - hit["start_mm"]
    dist_high = hit["end_mm"] - pos

    notes: list[str] = []
    if not prev["good"] and dist_low <= border_mm:
        notes.append(f"cách cung {prev['name']} (xấu) {dist_low:.2f} mm phía dưới")
    if not nxt["good"] and dist_high <= border_mm:
        notes.append(f"cách cung {nxt['name']} (xấu) {dist_high:.2f} mm phía trên")

    if notes:
        return True, "; ".join(notes)
    return False, None
