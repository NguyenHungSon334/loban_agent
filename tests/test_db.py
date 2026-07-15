"""P8 — job state transitions trên SQLite (plan W5)."""
from __future__ import annotations

from pathlib import Path

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


def test_create_and_get(web_env):
    from loban.web import jobs
    job = jobs.create_job("HS01", [Path("a.png")], khach_hang="Ông A", light=True)
    assert job.status == "queued"
    got = jobs.get_job("HS01")
    assert got is not None
    assert got.khach_hang == "Ông A"
    assert got.light is True
    assert jobs.input_paths(got) == [Path("a.png")]


def test_status_transitions(web_env):
    from loban.web import jobs
    jobs.create_job("HS02", [Path("a.png")])
    for st in ("extract", "classify", "render"):
        jobs.set_status("HS02", st)
        assert jobs.get_job("HS02").status == st
    jobs.set_status("HS02", "done", n_dim=5)
    done = jobs.get_job("HS02")
    assert done.status == "done"
    assert done.n_dim == 5


def test_pending_and_list(web_env):
    from loban.web import jobs
    jobs.create_job("HS03", [Path("a.png")])            # queued
    jobs.create_job("HS04", [Path("b.png")])
    jobs.set_status("HS04", "done", n_dim=1)
    assert jobs.pending_ho_so() == ["HS03"]             # done không pending
    assert {j.ho_so for j in jobs.list_jobs()} == {"HS03", "HS04"}


def test_set_status_unknown_raises(web_env):
    from loban.web import jobs
    with pytest.raises(KeyError):
        jobs.set_status("NOPE", "done")
