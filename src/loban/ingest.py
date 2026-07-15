"""Chuẩn hoá input -> danh sách ảnh (bytes, mime) cho bước extract (plan mục 3 bước 1).

Hỗ trợ: ảnh (png/jpg/webp) truyền thẳng; PDF -> render từng trang thành ảnh.
Text mô tả thông số đi kèm dạng employee_note (chuỗi), không xử lý ở đây.
"""
from __future__ import annotations

from pathlib import Path

ImagePart = tuple[bytes, str]  # (dữ liệu, mime_type)

_IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
_PDF_DPI = 200


def load_inputs(paths: list[str | Path]) -> list[ImagePart]:
    parts: list[ImagePart] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(path)
        ext = path.suffix.lower()
        if ext in _IMAGE_MIME:
            parts.append((path.read_bytes(), _IMAGE_MIME[ext]))
        elif ext == ".pdf":
            parts.extend(_pdf_to_images(path))
        else:
            raise ValueError(f"Định dạng không hỗ trợ: {ext} ({path})")
    return parts


def _pdf_to_images(path: Path) -> list[ImagePart]:
    import fitz  # PyMuPDF — wheel thuần, không cần poppler (dễ deploy hosting)

    zoom = _PDF_DPI / 72  # 72 = DPI gốc của PDF
    matrix = fitz.Matrix(zoom, zoom)
    parts: list[ImagePart] = []
    with fitz.open(str(path)) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            parts.append((pix.tobytes("png"), "image/png"))
    return parts
