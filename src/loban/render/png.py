"""Đầu ra 2 — PNG 4:5. fpdf2 dựng PDF 4:5 -> fitz đổi PNG (không browser)."""
from __future__ import annotations

from pathlib import Path

from ..models import AnalysisReport
from .build import build_png_pdf

_TARGET_W = 1080  # px chiều rộng ảnh (4:5 -> cao 1350)


def write_png(report: AnalysisReport, out_dir: str | Path, drawing: bytes | None = None) -> list[Path]:
    import fitz  # PyMuPDF — render PDF trang -> ảnh

    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    with fitz.open(stream=build_png_pdf(report, drawing), filetype="pdf") as doc:
        for i, page in enumerate(doc, start=1):
            zoom = _TARGET_W / page.rect.width
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            f = d / f"png_{i}.png"
            pix.save(str(f))
            files.append(f)
    return files
