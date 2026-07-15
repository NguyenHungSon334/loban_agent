from loban.classify import classify
from loban.models import Dimension
from loban.suggest import suggest


def _dim(category, kind, value):
    return Dimension(label="x", category=category, kind=kind, value_mm=value)


def _run(category, kind, value):
    d = _dim(category, kind, value)
    return d, classify(d)


def test_loi_di_uses_522_and_increase_note():
    d, lb = _run("loi_di", "thong_thuy", 160)  # lối đi -> 52.2 thông thủy, xấu
    assert lb.ruler == "52.2"
    assert lb.status == "chua_phu_hop"
    s = suggest(d, lb)
    assert s.lower_mm is not None or s.upper_mm is not None
    assert "Ưu tiên tăng" in s.note


def test_tot_still_shows_alternative_and_dang_dat():
    d, lb = _run("cong", "thong_thuy", 2060)   # Tể Tướng tốt
    assert lb.status == "tot"
    s = suggest(d, lb)
    assert s.lower_mm is None                   # xuống 50mm vẫn cùng cung
    assert s.upper_mm == 2088 and s.upper_cung == "Quý Nhân"
    assert "Đang đạt cung Tể Tướng" in s.note


def test_no_option_needs_architect():
    d, lb = _run("cong", "thong_thuy", 32)      # Quý Nhân, không cung tốt khác ±50
    s = suggest(d, lb)
    assert s.lower_mm is None and s.upper_mm is None
    assert "Cần kiến trúc sư" in s.note


def test_mo_two_stage_extends_to_100():
    d, lb = _run("mo", "phu_bi", 90)            # Vượng tốt; cung tốt khác đều >50mm
    s = suggest(d, lb)
    assert s.lower_mm == 38 and s.lower_cung == "Đinh"    # Δ52 -> nhờ mở rộng ±100
    assert s.upper_mm == 156 and s.upper_cung == "Nghĩa"  # Δ66 -> nhờ mở rộng ±100


def test_khoang_cach_now_suggested():
    # mọi hạng mục đều tính Lỗ Ban + có đề xuất (không còn None)
    d, lb = _run("khoang_cach", "phu_bi", 500)   # 38.8 (không phải thông thủy)
    assert lb.ruler == "38.8"
    s = suggest(d, lb)
    assert s is not None
    assert s.lower_mm is not None or s.upper_mm is not None


def test_mat_bang_suggested():
    d, lb = _run("mat_bang", "tong_the", 21000)  # 38.8
    assert lb.ruler == "38.8"
    assert suggest(d, lb) is not None


def test_cong_thong_thuy_is_52():
    d, lb = _run("cong", "thong_thuy", 2000)     # khe đi vào -> 52.2
    assert lb.ruler == "52.2"
