"""Đầu ra 1 — ghi AnalysisReport ra JSON (plan mục 8)."""
from __future__ import annotations

from pathlib import Path

from ..models import AnalysisReport


def write_analysis(report: AnalysisReport, out_dir: str | Path) -> Path:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "analysis.json"
    f.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return f
