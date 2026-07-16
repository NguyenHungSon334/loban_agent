from loban.checklist import check_completeness
from loban.models import Dimension


def _dim(category, label, kind="phu_bi", value=1000.0):
    return Dimension(label=label, category=category, kind=kind, value_mm=value)


_CFG = {
    "categories": [{"key": "mo", "label": "Mộ"}],
    "checklist": {
        "mo": [
            {"label": "Dài phủ bì", "kind": "phu_bi", "match": ["dai"], "required": True},
            {"label": "Rộng phủ bì", "kind": "phu_bi", "match": ["rong"], "required": True},
            {"label": "Lỗ thông thiên", "kind": "thong_thuy", "match": ["thong thien"], "required": True},
            {"label": "Ô kim tinh", "kind": "lot_long", "match": ["kim tinh"], "required": False},
        ],
    },
}


def test_missing_reported_when_component_present_but_incomplete():
    dims = [_dim("mo", "Chiều dài phủ bì mộ")]  # có mộ nhưng thiếu rộng + thông thiên
    missing = check_completeness(dims, _CFG)
    assert "Rộng phủ bì (Mộ)" in missing
    assert "Lỗ thông thiên (Mộ)" in missing
    assert not any("Dài" in m for m in missing)       # đã đo -> không thiếu
    assert not any("kim tinh" in m.lower() for m in missing)  # optional -> bỏ qua


def test_no_missing_when_component_absent():
    # bản vẽ không có mộ -> không báo thiếu (tránh nhiễu)
    dims = [_dim("cong", "Thông thủy cổng", kind="thong_thuy")]
    assert check_completeness(dims, _CFG) == []


def test_accent_insensitive_match():
    # "thông thiên" khớp bất kể dấu
    dims = [
        _dim("mo", "Chiều dài mộ"),
        _dim("mo", "Chiều rộng mộ"),
        _dim("mo", "Lỗ Thông Thiên", kind="thong_thuy"),
    ]
    assert check_completeness(dims, _CFG) == []


def test_empty_checklist_no_missing():
    dims = [_dim("mo", "Chiều dài mộ")]
    assert check_completeness(dims, {"checklist": {}}) == []
