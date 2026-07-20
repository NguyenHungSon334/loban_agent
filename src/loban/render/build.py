"""Dựng PDF/PNG từ AnalysisReport bằng fpdf2 (thuần Python, không browser/native).

Layout (bản 2, 2026-07-15) theo góp ý:
- Palette slate (#2d3748) thay đen tuyền — sang, dịu mắt.
- GỘP 3 nhóm thước thành 1 bảng duy nhất; mỗi nhóm mở đầu bằng 1 hàng tiêu đề
  (colspan) nhạt. Cột "Đề xuất" đưa kích thước sửa thẳng vào từng dòng.
- Ô "Đánh giá" tô nền mềm: xanh lá nhạt = Tốt, vàng cam nhạt = Chưa phù hợp.
- Logo đặt góc trên trái; thêm watermark logo cực mờ (6%) làm vân nền — KHÔNG
  đè lên số. Bản vẽ nằm trong khung giới hạn, không chồng bảng.

Đầu ra:
- report A4 ngang -> pdf_report.write_pdf
- png 4:5 (portrait) -> png.write_png (fitz đổi PNG)

Font DejaVuSans (phủ tiếng Việt) bundle trong render/fonts/. Test không cần
browser: fitz trích text từ PDF sinh ra để assert nội dung.
"""
from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

from ..models import AnalysisReport, AnalyzedItem

_FONTS = Path(__file__).resolve().parent / "fonts"
_ASSETS = Path(__file__).resolve().parents[3] / "assests"
_LOGO = _ASSETS / "logo_black.png"      # logo đen (góc trên trái)
_LOGO_WM = _ASSETS / "logo_wm.png"      # logo mờ 6% (vân nền)
_CONTACT = _ASSETS / "TTLN.txt"
_PNG_MM = (200, 250)  # tỉ lệ 4:5 (portrait); tràn -> tự sang trang

# ── palette slate ───────────────────────────────────────────────────────────
_SLATE = (45, 55, 72)          # #2d3748 — band tiêu đề
_SLATE_SOFT = (74, 85, 104)    # #4a5568
_GROUP_BG = (237, 242, 247)    # #edf2f7 — nền hàng nhóm thước
_INK = (26, 32, 44)            # #1a202c
_MUTED = (113, 128, 150)       # #718096
_WHITE = (255, 255, 255)
_GREEN_BG = (226, 244, 233)
_GREEN_TX = (22, 101, 52)
_AMBER_BG = (253, 240, 221)
_AMBER_TX = (154, 77, 17)
_ORANGE = (194, 65, 12)

_RULER_ORDER = ["38.8"]        # chỉ dùng thước 38.8
_RULER_META = {
    "38.8": ("A", "38,8 cm", "Âm phần", "Toàn bộ hạng mục"),
}

_CUNG_Y_NGHIA = {
    "Đinh": "Thêm đinh, phát triển nhân khẩu.",
    "Vượng": "Vượng khí, tài lộc, phát triển.",
    "Nghĩa": "Quan hệ tốt đẹp, bền vững.",
    "Quan": "Công danh, sự nghiệp thăng tiến.",
    "Hưng": "Hưng vượng, thịnh vượng lâu dài.",
    "Tài": "Tài lộc, tiền bạc, phú quý.",
    "Bản": "Vốn liếng, gốc rễ vững chắc.",
    "Quý Nhân": "Được quý nhân phù trợ, hanh thông.",
    "Thiên Tài": "Tài lộc trời cho, nhiều may mắn.",
    "Phúc Lộc": "Phúc đức, lộc khí đầy đủ.",
    "Tể Tướng": "Quyền uy, địa vị, tiền tài.",
}

_GHICHU_CHUNG = (
    "Đảm bảo yếu tố phong thủy và công năng sử dụng.",
    "Thi công theo kích thước thực tế tại hiện trường.",
    "Có thể sai số ±10 mm trong quá trình chế tác.",
)

MANDATORY_TAIL = "Sai số thi công ±10 mm."

# thứ tự cột bảng gộp
_COL_W = (46, 16, 26, 22, 36)   # Hạng mục · KT · Cung · Đánh giá · Đề xuất
_HEAD = ("Hạng mục / Loại thước", "KT (mm)", "Cung", "Đánh giá", "Đề xuất")


# ── format nhỏ ───────────────────────────────────────────────────────────────
def _fmt_mm(v: float | None) -> str:
    if v is None:
        return "—"
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def _eval_style(it: AnalyzedItem) -> tuple[str, FontFace]:
    if it.loban.status == "tot":
        txt = "✓ Tốt" + (" △" if it.loban.near_border else "")
        return txt, FontFace(color=_GREEN_TX, fill_color=_GREEN_BG, emphasis="BOLD")
    if it.loban.status == "chua_phu_hop":
        return "△ Chưa hợp", FontFace(color=_AMBER_TX, fill_color=_AMBER_BG, emphasis="BOLD")
    return "—", FontFace(color=_MUTED)


def _cung_name(it: AnalyzedItem) -> str:
    if not it.loban.cung:
        return "—"
    return it.loban.cung + (f"\n{it.loban.cung_nho}" if it.loban.cung_nho else "")


def _item_label(it: AnalyzedItem) -> str:
    cm = _RULER_META.get(it.loban.ruler or "", ("", "?", "", ""))[1]
    star = " *" if it.dimension.need_confirm else ""
    return f"{it.dimension.label}{star}\nThước {cm}"


def _suggest_cell(it: AnalyzedItem) -> str:
    s = it.suggestion
    if it.loban.status == "tot":
        return "Đang đạt"
    if not s or (s.lower_mm is None and s.upper_mm is None):
        return "Cần KTS chỉnh" if s and "kiến trúc sư" in (s.note or "").lower() else "—"
    parts = []
    if s.lower_mm is not None:
        parts.append(f"↓{_fmt_mm(s.lower_mm)} ({s.lower_cung})")
    if s.upper_mm is not None:
        parts.append(f"↑{_fmt_mm(s.upper_mm)} ({s.upper_cung})")
    return "\n".join(parts)


# ── PDF cơ bản ───────────────────────────────────────────────────────────────
def _new_pdf(orientation: str, fmt) -> FPDF:
    pdf = FPDF(orientation=orientation, unit="mm", format=fmt)
    pdf.add_font("dejavu", "", str(_FONTS / "DejaVuSans.ttf"))
    pdf.add_font("dejavu", "B", str(_FONTS / "DejaVuSans-Bold.ttf"))
    pdf.set_auto_page_break(True, margin=8)
    pdf.set_text_color(*_INK)
    return pdf


def _watermark(pdf: FPDF, frac: float = 0.75) -> None:
    """Vân logo mờ 15% giữa trang — vẽ trước nội dung, không đè số."""
    if not _LOGO_WM.exists():
        return
    try:
        w = pdf.w * frac
        x = (pdf.w - w) / 2
        y = (pdf.h - w) / 2
        pdf.image(str(_LOGO_WM), x=x, y=y, w=w)
        pdf.set_xy(pdf.l_margin, pdf.t_margin)
    except Exception:  # noqa: BLE001
        pass


def _logo(pdf: FPDF, w: float) -> None:
    if _LOGO.exists():
        try:
            pdf.image(str(_LOGO), w=w)
        except Exception:  # noqa: BLE001
            pass


@lru_cache(maxsize=1)
def _contact_info() -> tuple[str, str, str]:
    """(công ty, điện thoại, văn phòng) trích từ TTLN.txt — hiển thị gọn góc phải."""
    try:
        lines = _CONTACT.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ("", "", "")
    company = phone = office = ""
    for ln in lines:
        s = ln.strip().lstrip("•").strip()
        low = s.lower()
        if not company and low.startswith("công ty"):
            company = s.split("(")[0].strip()
        elif "điện thoại" in low:
            phone = s.split(":", 1)[-1].strip()
        elif not office and "văn phòng" in low:
            office = s.split(":", 1)[-1].strip()
    return (company, phone, office)


def _contact_block(pdf: FPDF, x: float, y: float, w: float) -> float:
    """Khối liên hệ căn phải, icon gọn. Trả về y kết thúc."""
    company, phone, office = _contact_info()
    if not (company or phone or office):
        return y
    pdf.set_xy(x, y)
    if company:
        pdf.set_font("dejavu", "B", 7)
        pdf.set_text_color(*_SLATE)
        pdf.cell(w, 3.6, company, new_x=XPos.LEFT, new_y=YPos.NEXT, align="R")
        pdf.set_x(x)
    pdf.set_font("dejavu", "", 6.4)
    pdf.set_text_color(*_MUTED)
    if phone:
        pdf.cell(w, 3.4, f"SĐT: {phone}", new_x=XPos.LEFT, new_y=YPos.NEXT, align="R")
        pdf.set_x(x)
    if office:
        pdf.multi_cell(w, 3.2, f"Địa chỉ: {office}", align="R")
    pdf.set_text_color(*_INK)
    return pdf.get_y()


def _profile_line(report: AnalysisReport) -> str:
    p = report.profile
    bits = [b for b in (p.khach_hang, p.dia_diem) if b]
    bits.append(f"data {report.data_version}")
    return "  ·  ".join(bits)


# ── khối layout ──────────────────────────────────────────────────────────────
def _header(pdf: FPDF, report: AnalysisReport, width: float, logo_w: float) -> None:
    y0 = pdf.get_y()
    _logo(pdf, w=logo_w)

    # khối liên hệ căn phải (icon gọn) — song song với tiêu đề
    cw = min(66.0, width * 0.32)
    cx = pdf.l_margin + width - cw
    contact_bottom = _contact_block(pdf, cx, y0, cw)

    # tiêu đề + hồ sơ bên trái, không lấn khối liên hệ
    tx = pdf.l_margin + logo_w + 4
    tw = cx - tx - 4
    pdf.set_xy(tx, y0 + 1)
    pdf.set_font("dejavu", "B", 15)
    pdf.cell(tw, 8, f"Báo cáo Lỗ Ban — {report.profile.ho_so}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(tx)
    pdf.set_font("dejavu", "", 8)
    pdf.set_text_color(*_MUTED)
    pdf.cell(tw, 5, _profile_line(report), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_INK)
    pdf.set_y(max(pdf.get_y(), contact_bottom, y0 + logo_w * 0.75))
    pdf.ln(1)


def _band(pdf: FPDF, title: str, width: float) -> None:
    pdf.set_font("dejavu", "B", 9)
    pdf.set_fill_color(*_SLATE)
    pdf.set_text_color(*_WHITE)
    pdf.cell(width, 6, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_text_color(*_INK)


def _totals_band(pdf: FPDF, report: AnalysisReport, width: float) -> None:
    p = report.profile
    fields = []
    if p.dien_tich_m2 is not None:
        fields.append(("Diện tích", f"{_fmt_mm(p.dien_tich_m2)} m²"))
    if p.huong_cong:
        fields.append(("Hướng cổng", p.huong_cong))
    if p.vat_lieu:
        fields.append(("Vật liệu", p.vat_lieu))
    if not fields:
        return
    _band(pdf, "KÍCH THƯỚC TỔNG THỂ", width)
    cw = width / len(fields)
    x0, y = pdf.get_x(), pdf.get_y()
    for i, (k, v) in enumerate(fields):
        pdf.set_xy(x0 + i * cw, y)
        pdf.set_font("dejavu", "", 7)
        pdf.set_text_color(*_MUTED)
        pdf.cell(cw, 4, f" {k}", new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.set_x(x0 + i * cw)
        pdf.set_font("dejavu", "B", 9)
        pdf.set_text_color(*_INK)
        pdf.cell(cw, 5, f" {v}")
    pdf.set_xy(x0, y + 9)
    pdf.ln(1)


def _merged_table(pdf: FPDF, report: AnalysisReport, width: float) -> None:
    """1 bảng gộp: mỗi nhóm thước mở đầu bằng hàng tiêu đề (colspan)."""
    groups = _group_by_ruler(report)
    pdf.set_font("dejavu", "", 6.8)
    pdf.set_fill_color(*_WHITE)
    with pdf.table(
        col_widths=_COL_W,
        text_align=("LEFT", "RIGHT", "LEFT", "CENTER", "LEFT"),
        headings_style=FontFace(emphasis="BOLD", fill_color=_SLATE_SOFT, color=_WHITE),
        line_height=4.4,
        first_row_as_headings=True,
    ) as t:
        t.row(_HEAD)
        for ruler in _RULER_ORDER:
            items = groups.get(ruler) or []
            if not items:
                continue
            tag, cm, am, dungcho = _RULER_META[ruler]
            gr = t.row()
            gr.cell(f"{tag} · THƯỚC {cm} — {am}  ({dungcho})",
                    colspan=5, style=FontFace(emphasis="BOLD", fill_color=_GROUP_BG))
            for it in items:
                etxt, estyle = _eval_style(it)
                row = t.row()
                row.cell(_item_label(it))
                row.cell(_fmt_mm(it.dimension.value_mm))
                row.cell(_cung_name(it))
                row.cell(etxt, style=estyle)
                row.cell(_suggest_cell(it))
    pdf.ln(1)


def _box_title(pdf: FPDF, title: str, width: float) -> None:
    pdf.set_font("dejavu", "B", 8)
    pdf.set_fill_color(*_SLATE)
    pdf.set_text_color(*_WHITE)
    pdf.cell(width, 5, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_text_color(*_INK)


def _cung_meaning_box(pdf: FPDF, report: AnalysisReport, width: float) -> None:
    seen = []
    for it in report.items:
        c = it.loban.cung
        if it.loban.status == "tot" and c in _CUNG_Y_NGHIA and c not in seen:
            seen.append(c)
    if not seen:
        return
    _box_title(pdf, "Ý NGHĨA CÁC CUNG TỐT", width)
    pdf.set_font("dejavu", "", 6.8)
    for c in seen:
        pdf.set_font("dejavu", "B", 6.8)
        pdf.cell(22, 4.2, f" {c}")
        pdf.set_font("dejavu", "", 6.8)
        pdf.multi_cell(width - 22, 4.2, _CUNG_Y_NGHIA[c], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def _ghichu_box(pdf: FPDF, report: AnalysisReport, width: float) -> None:
    _box_title(pdf, "GHI CHÚ CHUNG", width)
    pdf.set_font("dejavu", "", 6.8)
    for line in _GHICHU_CHUNG:
        pdf.set_text_color(*_GREEN_TX)
        pdf.cell(4, 4.2, " ✓")
        pdf.set_text_color(*_INK)
        pdf.multi_cell(width - 4, 4.2, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if report.need_confirm:
        pdf.set_text_color(*_ORANGE)
        pdf.multi_cell(width, 4.2, "Cần xác nhận (*): " + ", ".join(report.need_confirm),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_INK)
    if report.missing:
        pdf.set_text_color(*_ORANGE)
        pdf.multi_cell(width, 4.2, "Thiếu / cần đo bổ sung: " + ", ".join(report.missing),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_INK)
    for n in report.near_border:
        pdf.set_text_color(*_ORANGE)
        pdf.multi_cell(width, 4.2, f"△ {n}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_INK)
    pdf.set_font("dejavu", "", 6.5)
    pdf.set_text_color(*_MUTED)
    for w in report.warnings:
        pdf.multi_cell(width, 4, w, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_INK)


def _group_by_ruler(report: AnalysisReport) -> dict[str, list[AnalyzedItem]]:
    groups: dict[str, list[AnalyzedItem]] = {r: [] for r in _RULER_ORDER}
    for it in report.items:
        groups.setdefault(it.loban.ruler or "38.8", []).append(it)
    return groups


def _as_drawings(drawing: bytes | list[bytes] | None) -> list[bytes]:
    if drawing is None:
        return []
    return list(drawing) if isinstance(drawing, (list, tuple)) else [drawing]


def _drawing_page(pdf: FPDF, data: bytes) -> None:
    """1 trang chứa ảnh bản vẽ input, vừa khung nội dung, giữ tỉ lệ."""
    pdf.add_page()
    try:
        pdf.image(io.BytesIO(data), x=pdf.l_margin, y=pdf.t_margin,
                  w=pdf.epw, h=pdf.eph, keep_aspect_ratio=True)
    except Exception:  # noqa: BLE001 - ảnh lỗi/định dạng lạ -> bỏ qua, vẫn ra bảng
        pass


# ── ĐẦU RA 3: PDF A4 ngang — trang đầu là bản vẽ input, các trang sau là bảng ─
def build_report_pdf(report: AnalysisReport, drawing: bytes | list[bytes] | None = None) -> bytes:
    pdf = _new_pdf("L", "A4")
    for d in _as_drawings(drawing):      # gắn (các) bản vẽ input lên trước
        _drawing_page(pdf, d)
    pdf.add_page()
    _watermark(pdf)
    epw = pdf.epw
    _header(pdf, report, epw, logo_w=22)
    _totals_band(pdf, report, epw)
    _merged_table(pdf, report, epw)      # full width bằng header
    pdf.ln(1)
    _cung_meaning_box(pdf, report, epw)
    _ghichu_box(pdf, report, epw)
    return bytes(pdf.output())


# ── ĐẦU RA 2: PNG 4:5 — bảng gộp full width, watermark logo giữa ─────────────
def build_png_pdf(report: AnalysisReport, drawing: bytes | None = None) -> bytes:
    pdf = _new_pdf("P", _PNG_MM)
    pdf.add_page()
    _watermark(pdf)
    epw = pdf.epw
    _header(pdf, report, epw, logo_w=24)
    _totals_band(pdf, report, epw)
    _merged_table(pdf, report, epw)
    _cung_meaning_box(pdf, report, epw)
    _ghichu_box(pdf, report, epw)
    return bytes(pdf.output())
