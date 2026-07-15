"""Đầu ra 3 — PDF A4 ngang (fpdf2, thuần Python — không browser/native)."""
from __future__ import annotations

from pathlib import Path

from ..models import AnalysisReport
from .build import build_report_pdf


def write_pdf(report: AnalysisReport, out_dir: str | Path, drawing: bytes | None = None) -> Path:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "report.pdf"
    f.write_bytes(build_report_pdf(report, drawing))
    return f
