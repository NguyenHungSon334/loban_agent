from loban.classify import classify, ruler_for
from loban.models import Dimension


def _dim(category, kind, value=None):
    return Dimension(label="x", category=category, kind=kind, value_mm=value)


def test_mapping_ruler():
    # Override: MỌI hạng mục/kind -> thước 38.8, không dùng thước khác.
    for cat, kind in [
        ("mo", "phu_bi"), ("mo", "lot_long"), ("lang_tho", "khoi"),
        ("lang_tho", "hop_tho"), ("cong", "phu_bi"), ("mat_bang", "tong_the"),
        ("khoang_cach", "phu_bi"), ("cong", "thong_thuy"),
        ("khoang_cach", "thong_thuy"), ("lang_tho", "tong_the"),
        ("loi_di", "thong_thuy"), ("loi_di", "phu_bi"),
    ]:
        assert ruler_for(cat, kind) == "38.8"


def test_classify_tot():
    r = classify(_dim("mo", "phu_bi", 870))     # 38.8 -> Vượng tốt
    assert r.ruler == "38.8"
    assert r.cung == "Vượng"
    assert r.status == "tot"


def test_classify_chua_phu_hop():
    r = classify(_dim("cong", "thong_thuy", 150))  # 38.8 pos150 -> Khổ (xấu)
    assert r.ruler == "38.8"
    assert r.status == "chua_phu_hop"
    assert r.cung_good is False


def test_classify_all_categories_get_ruler():
    # mặt bằng khu + khoảng cách nay cũng tính Lỗ Ban (không còn "không áp dụng")
    r = classify(_dim("mat_bang", "tong_the", 21000))
    assert r.ruler == "38.8"
    assert r.status in ("tot", "chua_phu_hop")
    r2 = classify(_dim("khoang_cach", "phu_bi", 500))
    assert r2.ruler == "38.8"
    assert r2.status in ("tot", "chua_phu_hop")


def test_classify_khong_ap_dung_no_value():
    r = classify(_dim("mo", "phu_bi", None))
    assert r.status == "khong_ap_dung"
    assert r.ruler == "38.8"


def test_classify_near_border_propagates():
    r = classify(_dim("mo", "phu_bi", 35))  # 38.8 -> Đinh (0-38.8), sát biên Hại
    assert r.status == "tot"
    assert r.near_border is True
    assert "Hại" in r.border_note


def test_cong_thong_thuy_single_ruler():
    # Override: cổng thông thủy nay cũng chỉ tính 38.8, không còn thước phụ.
    r = classify(_dim("cong", "thong_thuy", 810))
    assert r.ruler == "38.8"
    assert r.cross is None


def test_no_cross_for_normal_dim():
    r = classify(_dim("mo", "phu_bi", 870))
    assert r.cross is None
