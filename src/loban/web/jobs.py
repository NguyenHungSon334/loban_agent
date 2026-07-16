"""CRUD + truy vấn job trên SQLite (plan W2/W4)."""
from __future__ import annotations

import json
from pathlib import Path

from sqlmodel import select

from ..models import Profile
from .db import AnalysisJob, _now, session

# status chưa hoàn tất -> requeue khi khởi động lại (plan W-D4)
PENDING = ("queued", "extract", "classify", "render")


def create_job(
    ho_so: str,
    inputs: list[Path],
    *,
    khach_hang: str | None = None,
    dia_diem: str | None = None,
    huong_cong: str | None = None,
    vat_lieu: str | None = None,
    note: str = "",
    cau_hoi: str = "",
    light: bool = False,
    png: bool = True,
    pdf: bool = True,
) -> AnalysisJob:
    job = AnalysisJob(
        ho_so=ho_so,
        inputs=json.dumps([str(p) for p in inputs]),
        khach_hang=khach_hang,
        dia_diem=dia_diem,
        huong_cong=huong_cong,
        vat_lieu=vat_lieu,
        note=note,
        cau_hoi=cau_hoi,
        light=light,
        png=png,
        pdf=pdf,
    )
    with session() as s:
        s.add(job)
        s.commit()
        s.refresh(job)
    return job


def set_status(
    ho_so: str,
    status: str,
    *,
    step: str | None = None,
    error: str | None = None,
    n_dim: int | None = None,
) -> None:
    with session() as s:
        job = s.get(AnalysisJob, ho_so)
        if job is None:
            raise KeyError(ho_so)
        job.status = status
        job.step = step
        job.error = error   # None -> xóa lỗi cũ (vd khi thử lại)
        if n_dim is not None:
            job.n_dim = n_dim
        job.updated_at = _now()
        s.add(job)
        s.commit()


def delete_job(ho_so: str) -> bool:
    with session() as s:
        job = s.get(AnalysisJob, ho_so)
        if job is None:
            return False
        s.delete(job)
        s.commit()
        return True


def get_job(ho_so: str) -> AnalysisJob | None:
    with session() as s:
        return s.get(AnalysisJob, ho_so)


def list_jobs(offset: int = 0, limit: int = 20) -> list[AnalysisJob]:
    with session() as s:
        stmt = (
            select(AnalysisJob)
            .order_by(AnalysisJob.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(s.exec(stmt))


def pending_ho_so() -> list[str]:
    with session() as s:
        stmt = select(AnalysisJob.ho_so).where(AnalysisJob.status.in_(PENDING))
        return list(s.exec(stmt))


def input_paths(job: AnalysisJob) -> list[Path]:
    return [Path(p) for p in json.loads(job.inputs)]


def to_profile(job: AnalysisJob) -> Profile:
    return Profile(
        ho_so=job.ho_so,
        khach_hang=job.khach_hang,
        dia_diem=job.dia_diem,
        huong_cong=job.huong_cong,
        vat_lieu=job.vat_lieu,
    )
