"""Render PNG/PDF thuần Python (fpdf2 + fitz) — không browser/native.

Assert nội dung bằng cách trích text từ PDF sinh ra (fitz).
"""
import base64

import fitz

from loban.models import Dimension, ExtractionResult, Profile
from loban.pipeline import build_report
from loban.render.build import build_report_pdf, build_png_pdf

# PNG 1x1 hợp lệ cho test nhúng ảnh bản vẽ
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _report(n=1):
    dims = [
        Dimension(label=f"KT {i}", category="mo", kind="phu_bi", value_mm=870, confidence="cao")
        for i in range(n)
    ]
    dims.append(Dimension(label="Lối đi", category="loi_di", kind="thong_thuy", value_mm=160, confidence="cao"))  # tra bằng 38.8, xấu
    dims.append(Dimension(label="Cổng mờ", category="cong", kind="thong_thuy", value_mm=2060,
                          confidence="thap", need_confirm=True))
    dims.append(Dimension(label="Cột hàng rào", category="lang_tho", kind="tong_the", value_mm=2500, confidence="cao"))  # tra bằng 38.8
    return build_report(ExtractionResult(dimensions=dims),
                        Profile(ho_so="HS01", khach_hang="Ông A", dia_diem="Thanh Hóa"))


def _pages_text(pdf_bytes):
    # gộp khoảng trắng: text trong ô bảng có thể xuống dòng giữa cụm từ
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return [" ".join(p.get_text().split()) for p in doc]


def test_png_groups_single_ruler_388():
    # override: mọi kích thước tính thước 38.8 -> chỉ còn nhóm Âm phần
    text = " ".join(_pages_text(build_png_pdf(_report(n=2))))
    assert "38,8 cm" in text and "Âm phần" in text
    assert "52,2 cm" not in text and "42,9 cm" not in text


def test_png_content_present():
    text = " ".join(_pages_text(build_png_pdf(_report())))
    assert "HS01" in text and "Ông A" in text
    assert "Tốt" in text and "Chưa hợp" in text     # nhãn đánh giá tô nền mềm
    assert "Cổng mờ" in text
    assert "Cần xác nhận" in text          # hộp ghi chú liệt kê mục cần xác nhận


def test_png_has_contact_header():
    # liên hệ (SĐT) hiển thị gọn góc trên phải
    text = " ".join(_pages_text(build_png_pdf(_report())))
    assert "0854 783 333" in text


def test_report_pdf_has_full_sections():
    r = _report()
    text = "".join(_pages_text(build_report_pdf(r)))
    assert "cần xác nhận" in text.lower()
    assert "Sai số thi công" in text        # cảnh báo bắt buộc
    assert "GHI CHÚ CHUNG" in text
    assert r.data_version in text


def test_drawing_embeds_without_error():
    # ảnh hợp lệ -> PDF vẫn dựng, không vỡ
    pdf = build_png_pdf(_report(), drawing=_PNG_1X1)
    assert pdf[:4] == b"%PDF"
    assert _pages_text(pdf)  # có ít nhất 1 trang text


def test_bad_drawing_does_not_break():
    # ảnh hỏng -> bỏ qua, báo cáo vẫn ra
    pdf = build_report_pdf(_report(), drawing=b"not-an-image")
    assert pdf[:4] == b"%PDF"
