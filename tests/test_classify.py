from loban.classify import classify, ruler_for
from loban.models import Dimension


def _dim(category, kind, value=None):
    return Dimension(label="x", category=category, kind=kind, value_mm=value)


def test_mapping_ruler():
    # D2c: lăng thờ tổng thể -> 42.9 · thông thủy/lối đi -> 52.2 · còn lại -> 38.8
    assert ruler_for("mo", "phu_bi") == "38.8"            # mộ
    assert ruler_for("mo", "lot_long") == "38.8"          # lọt lòng quan tài
    assert ruler_for("lang_tho", "khoi") == "38.8"        # lăng khối đặc
    assert ruler_for("lang_tho", "hop_tho") == "38.8"     # hộp thờ/bài vị
    assert ruler_for("cong", "phu_bi") == "38.8"          # khối cổng (rào/cuốn thư tương tự)
    assert ruler_for("mat_bang", "tong_the") == "38.8"
    assert ruler_for("khoang_cach", "phu_bi") == "38.8"
    # khe thông thủy giữa 2 cột cổng -> 52.2
    assert ruler_for("cong", "thong_thuy") == "52.2"
    assert ruler_for("khoang_cach", "thong_thuy") == "52.2"
    # lăng thờ tổng thể (dài/rộng khối) -> 42.9 (ưu tiên trước mọi rule)
    assert ruler_for("lang_tho", "tong_the") == "42.9"
    # lối đi -> 52.2 thông thủy (2 biên giới hạn), mọi kind
    assert ruler_for("loi_di", "thong_thuy") == "52.2"
    assert ruler_for("loi_di", "phu_bi") == "52.2"


def test_classify_tot():
    r = classify(_dim("mo", "phu_bi", 870))     # 38.8 -> Vượng tốt
    assert r.ruler == "38.8"
    assert r.cung == "Vượng"
    assert r.status == "tot"


def test_classify_chua_phu_hop():
    r = classify(_dim("cong", "thong_thuy", 610))  # 52.2 -> Hiểm Họa xấu
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


def test_cong_thong_thuy_dual_ruler():
    # cổng thông thủy: chính 52.2 + đối chiếu THÊM 38.8 (cross_ruler mặc định)
    r = classify(_dim("cong", "thong_thuy", 810))
    assert r.ruler == "52.2"
    assert r.cross is not None
    assert r.cross.ruler == "38.8"
    assert r.cross.cung is not None
    assert r.cross.status in ("tot", "chua_phu_hop")


def test_no_cross_for_normal_dim():
    r = classify(_dim("mo", "phu_bi", 870))
    assert r.cross is None
