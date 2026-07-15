"""Ghép chuỗi classify -> suggest -> validate thành AnalysisReport (plan mục 2).

Bước extract (Gemini) tách riêng vì cần key; pipeline nhận sẵn ExtractionResult
nên chạy/kiểm thử được không cần mạng.
"""
from __future__ import annotations

from .classify import classify
from .models import AnalysisReport, AnalyzedItem, ExtractionResult, Profile
from .ruler import load_data
from .suggest import suggest
from .validate import MANDATORY_WARNING, mark_usability, needs_confirm


def analyze_dimensions(dims) -> list[AnalyzedItem]:
    items: list[AnalyzedItem] = []
    for d in dims:
        lb = classify(d)
        item = AnalyzedItem(dimension=d, loban=lb, suggestion=suggest(d, lb))
        items.append(mark_usability(item))
    return items


def build_report(extraction: ExtractionResult, profile: Profile) -> AnalysisReport:
    items = analyze_dimensions(extraction.dimensions)
    confirm = [it.dimension.label for it in items if needs_confirm(it.dimension)]
    near = [
        f"{it.dimension.label}: {it.loban.border_note}"
        for it in items
        if it.loban.near_border and it.loban.border_note
    ]
    return AnalysisReport(
        profile=profile,
        data_version=load_data()["version"],
        items=items,
        need_confirm=confirm,
        near_border=near,
        warnings=[MANDATORY_WARNING],
    )
