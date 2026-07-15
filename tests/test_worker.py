"""P8 — asyncio pool cap song song (plan W-D3). Gốc: sai cap = quá tải VPS."""
from __future__ import annotations

import asyncio
import threading
import time

import pytest


@pytest.fixture
def web_env(tmp_path, monkeypatch):
    monkeypatch.setenv("LOBAN_WEB_DB_URL", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    monkeypatch.setenv("LOBAN_WEB_OUTPUT_DIR", str(tmp_path / "out"))
    from loban.web import db, deps
    deps.settings.cache_clear()
    db.reset_engine()
    yield
    deps.settings.cache_clear()
    db.reset_engine()


def test_concurrency_cap(web_env, monkeypatch):
    """N=2 consumer -> tối đa 2 job chạy đồng thời dù enqueue 6."""
    from loban.web import worker

    lock = threading.Lock()
    active = 0
    max_active = 0

    def fake_process(ho_so: str) -> None:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1

    monkeypatch.setattr(worker, "_process", fake_process)

    async def run() -> None:
        await worker.start(concurrency=2, requeue=False)
        for i in range(6):
            await worker.enqueue(f"H{i}")
        await asyncio.wait_for(worker._queue.join(), timeout=5)
        await worker.stop()

    asyncio.run(run())
    assert max_active == 2  # đủ job để bão hòa 2 slot, không vượt


def test_job_error_marked(web_env, monkeypatch):
    """Job lỗi -> status=error, worker không chết."""
    from pathlib import Path

    from loban.web import jobs, worker

    jobs.create_job("HSERR", [Path("x.png")])

    def boom(ho_so: str) -> None:
        raise RuntimeError("gemini down")

    monkeypatch.setattr(worker, "_process", boom)

    async def run() -> None:
        await worker.start(concurrency=1, requeue=False)
        await worker.enqueue("HSERR")
        await asyncio.wait_for(worker._queue.join(), timeout=5)
        await worker.stop()

    asyncio.run(run())
    job = jobs.get_job("HSERR")
    assert job.status == "error"
    assert "gemini down" in job.error
