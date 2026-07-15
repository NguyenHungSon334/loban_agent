"""Golden cases tra cung — khoá theo công thức plan mục 5.1 (D9).

Không dùng tên cung ảnh mẫu. Số kỳ vọng tính trực tiếp từ công thức
    pos = value % cycle ; cung = floor(pos / step).
"""
import pytest

from loban.ruler import lookup

# (value_mm, ruler, cung kỳ vọng, tốt?, near_border kỳ vọng)
GOLDEN = [
    # Thước 38.8 — âm phần
    (870, "38.8", "Vượng", True, False),
    (1270, "38.8", "Vượng", True, False),
    (2500, "38.8", "Nghĩa", True, False),
    (790, "38.8", "Đinh", True, False),
    (2830, "38.8", "Vượng", True, True),      # sát biên Khổ (xấu) 2.40mm
    # Thước 52.2 — thông thủy
    (610, "52.2", "Hiểm Họa", False, False),   # khác ảnh mẫu (D9)
    (2060, "52.2", "Tể Tướng", True, False),   # khác ảnh mẫu (D9)
    (522, "52.2", "Quý Nhân", True, False),    # bội chu kỳ -> pos 0
    (0, "52.2", "Quý Nhân", True, False),
    # Thước 42.9 — dương trạch
    (250, "42.9", "Quan", True, False),
    (1880, "42.9", "Nghĩa", True, True),       # khác ảnh mẫu (D9); sát biên Ly (xấu) 3.13mm
    (590, "42.9", "Nghĩa", True, True),        # sát biên Ly (xấu) 0.125mm -> near_border
]


@pytest.mark.parametrize("value_mm,ruler,cung,good,near", GOLDEN)
def test_lookup_golden(value_mm, ruler, cung, good, near):
    hit = lookup(value_mm, ruler)
    assert hit.name == cung, f"{value_mm}mm/{ruler}: got {hit.name}"
    assert hit.good is good
    assert hit.near_border is near


def test_near_border_note_names_bad_cung():
    hit = lookup(590, "42.9")
    assert hit.near_border is True
    assert "Ly" in hit.border_note  # cung xấu kề bên


def test_periodicity():
    # cùng pos sau 1 chu kỳ -> cùng cung
    a = lookup(250, "42.9")
    b = lookup(250 + 429, "42.9")
    assert a.name == b.name and a.good == b.good


def test_bad_cung_no_near_border_flag():
    # cung hiện tại đã xấu -> không gắn cờ near_border (D7 chỉ cảnh báo số tốt)
    hit = lookup(610, "52.2")
    assert hit.good is False
    assert hit.near_border is False


def test_invalid_ruler_raises():
    with pytest.raises(KeyError):
        lookup(500, "50.0")


def test_negative_value_raises():
    with pytest.raises(ValueError):
        lookup(-10, "52.2")


def test_sub_cung_52():
    h = lookup(63, "52.2")           # Quý Nhân, offset 63/13.05 -> sub 4
    assert h.name == "Quý Nhân"
    assert h.sub_index == 4
    assert h.sub_name == "Thông minh"


def test_sub_cung_38():
    h = lookup(870, "38.8")          # Vượng (pos 94), offset 16.4/9.7 -> sub 1
    assert h.name == "Vượng"
    assert h.sub_name == "Hỷ sự"


def test_sub_cung_first_of_cung():
    h = lookup(5, "38.8")            # Đinh, sub 0
    assert h.name == "Đinh"
    assert h.sub_index == 0
    assert h.sub_name == "Phúc tinh"
