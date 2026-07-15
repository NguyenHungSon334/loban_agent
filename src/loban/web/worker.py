"""Asyncio job pool — chạy pipeline nền, cap song song (plan W-D3).

Cap concurrency = số consumer kéo từ 1 queue (đơn giản hơn Semaphore rời).
Bước extract (Gemini) + render (Playwright) là blocking -> đẩy threadpool để
không chẹn event loop. Bước chậm là network-I/O nên N consumer chạy song song tốt.
"""
from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from ..extract import extract
from ..ingest import load_inputs
from ..models import AnalysisReport
from ..pipeline import build_report
from ..render.analysis_json import write_analysis
from ..render.pdf_report import write_pdf
from ..render.png import write_png
from .db import AnalysisJob
from . import jobs
from .deps import settings

log = logging.getLogger("loban.worker")

_queue: asyncio.Queue[str] | None = None
_executor: ThreadPoolExecutor | None = None
_workers: list[asyncio.Task] = []


async def start(concurrency: int | None = None, *, requeue: bool = True) -> None:
    global _queue, _executor
    n = concurrency or settings().worker_concurrency
    _queue = asyncio.Queue()
    _executor = ThreadPoolExecutor(max_workers=n)
    if requeue:
        pending = jobs.pending_ho_so()
        if pending:
            log.info("requeue %d job kẹt sau restart: %s", len(pending), pending)
        for ho_so in pending:   # job kẹt sau restart -> chạy lại
            jobs.set_status(ho_so, "queued")
            _queue.put_nowait(ho_so)
    log.info("worker start: %d consumer song song", n)
    for _ in range(n):
        _workers.append(asyncio.create_task(_consumer()))


async def stop() -> None:
    for t in _workers:
        t.cancel()
    _workers.clear()
    if _executor is not None:
        _executor.shutdown(wait=False)


async def enqueue(ho_so: str) -> None:
    assert _queue is not None, "worker chưa start()"
    await _queue.put(ho_so)


async def _consumer() -> None:
    loop = asyncio.get_running_loop()
    assert _queue is not None
    while True:
        ho_so = await _queue.get()
        try:
            await loop.run_in_executor(_executor, _process, ho_so)
        except Exception as e:  # noqa: BLE001 - lỗi job không được hạ cả worker
            log.exception("[%s] LỖI job", ho_so)
            jobs.set_status(ho_so, "error", error=str(e))
        finally:
            _queue.task_done()


def _drawing_bytes(job: AnalysisJob) -> bytes | None:
    """Bytes ảnh bản vẽ đầu (trang 1) để nhúng vào PNG/PDF."""
    paths = jobs.input_paths(job)
    if not paths:
        return None
    images = load_inputs(paths[:1])
    return images[0][0] if images else None


def write_outputs(report: AnalysisReport, job: AnalysisJob, drawing: bytes | None) -> None:
    """Ghi 3 đầu ra theo cờ hồ sơ. Dùng chung cho chạy mới + xác nhận/tính lại."""
    out_dir = settings().output_dir / job.ho_so
    write_analysis(report, out_dir)
    if job.png:
        t = time.perf_counter()
        write_png(report, out_dir, drawing)
        log.info("[%s] render PNG %.2fs", job.ho_so, time.perf_counter() - t)
    if job.pdf:
        t = time.perf_counter()
        write_pdf(report, out_dir, drawing)
        log.info("[%s] render PDF %.2fs", job.ho_so, time.perf_counter() - t)


def _process(ho_so: str) -> None:
    """Chạy 1 job (blocking, trong threadpool). Cập nhật status + log thời gian từng bước."""
    job = jobs.get_job(ho_so)
    if job is None:
        raise KeyError(ho_so)

    t0 = time.perf_counter()
    log.info("[%s] BẮT ĐẦU (light=%s, png=%s, pdf=%s)", ho_so, job.light, job.png, job.pdf)

    jobs.set_status(ho_so, "extract")
    t = time.perf_counter()
    images = load_inputs(jobs.input_paths(job))
    extraction = extract(images, job.note, light=job.light)
    log.info("[%s] extract (Gemini, %d ảnh) %.2fs -> %d kích thước",
             ho_so, len(images), time.perf_counter() - t, len(extraction.dimensions))

    jobs.set_status(ho_so, "classify")
    t = time.perf_counter()
    report = build_report(extraction, jobs.to_profile(job))
    log.info("[%s] classify+suggest %.2fs", ho_so, time.perf_counter() - t)

    jobs.set_status(ho_so, "render")
    write_outputs(report, job, images[0][0] if images else None)

    jobs.set_status(ho_so, "done", n_dim=len(report.items))
    log.info("[%s] XONG tổng %.2fs, %d kích thước", ho_so, time.perf_counter() - t0, len(report.items))
