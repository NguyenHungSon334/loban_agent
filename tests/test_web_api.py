"""P9 — API smoke: route code, analyze tạo job + enqueue, guard tải file."""
from __future__ import annotations

import time

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LOBAN_WEB_DB_URL", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    monkeypatch.setenv("LOBAN_WEB_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("LOBAN_RULES_PATH", str(tmp_path / "rules.json"))  # không đụng data thật
    from loban.classify import _load_file
    _load_file.cache_clear()
    from loban.web import app as appmod
    from loban.web import db, deps, jobs, worker
    deps.settings.cache_clear()
    db.reset_engine()

    def fake_process(ho_so: str) -> None:  # thay Gemini+Playwright
        out = deps.settings().output_dir / ho_so
        out.mkdir(parents=True, exist_ok=True)
        (out / "analysis.json").write_text('{"items": []}', encoding="utf-8")
        (out / "png_1.png").write_bytes(b"\x89PNG")
        jobs.set_status(ho_so, "done", n_dim=0)

    monkeypatch.setattr(worker, "_process", fake_process)
    from fastapi.testclient import TestClient
    with TestClient(appmod.app) as c:
        yield c
    deps.settings.cache_clear()
    db.reset_engine()


def _wait_done(client, ho_so, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        r = client.get(f"/api/jobs/{ho_so}")
        if r.json()["status"] in ("done", "error"):
            return r.json()
        time.sleep(0.05)
    raise AssertionError("job không hoàn tất kịp")


def test_analyze_creates_and_runs_job(client):
    r = client.post(
        "/api/analyze",
        data={"ho_so": "HS01", "khach_hang": "Ông A", "light": "true"},
        files=[("files", ("ban_ve.png", b"fakeimg", "image/png"))],
    )
    assert r.status_code == 200
    ho_so = r.json()["ho_so"]
    assert ho_so == "HS01"
    assert _wait_done(client, ho_so)["status"] == "done"


def test_analyze_duplicate_ho_so_gets_unique(client):
    args = dict(
        data={"ho_so": "DUP"},
        files=[("files", ("a.png", b"x", "image/png"))],
    )
    first = client.post("/api/analyze", **args).json()["ho_so"]
    second = client.post("/api/analyze", **args).json()["ho_so"]
    assert first == "DUP"
    assert second != "DUP" and second.startswith("DUP-")


def test_report_and_files(client):
    client.post(
        "/api/analyze",
        data={"ho_so": "HS02"},
        files=[("files", ("a.png", b"x", "image/png"))],
    )
    _wait_done(client, "HS02")
    assert client.get("/api/report/HS02").status_code == 200
    assert client.get("/api/files/HS02/analysis.json").status_code == 200
    assert client.get("/api/files/HS02/png_1.png").status_code == 200


def test_bundle_png_zip(client):
    client.post("/api/analyze", data={"ho_so": "HSZ"},
                files=[("files", ("a.png", b"x", "image/png"))])
    _wait_done(client, "HSZ")
    r = client.get("/api/bundle/HSZ?kind=png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert r.content[:2] == b"PK"       # chữ ký zip
    assert client.get("/api/bundle/HSZ?kind=all").status_code == 200


def test_report_404_before_done(client):
    assert client.get("/api/report/NOPE").status_code == 404
    assert client.get("/api/jobs/NOPE").status_code == 404


def test_files_guard(client):
    client.post(
        "/api/analyze",
        data={"ho_so": "HS03"},
        files=[("files", ("a.png", b"x", "image/png"))],
    )
    _wait_done(client, "HS03")
    assert client.get("/api/files/HS03/secret.txt").status_code == 403
    # traversal bị Path(name).name làm phẳng -> không thoát thư mục
    assert client.get("/api/files/HS03/..%2f..%2fweb.db").status_code in (403, 404)


def test_confirm_marks_dimension_and_recomputes(client):
    from loban.models import Dimension, ExtractionResult, Profile
    from loban.pipeline import build_report
    from loban.render.analysis_json import write_analysis
    from loban.web import deps, jobs

    jobs.create_job("HSC", [], png=False, pdf=False)  # không file, không render ảnh
    dim = Dimension(label="Cổng mờ", category="cong", kind="thong_thuy",
                    value_mm=2060, confidence="thap", need_confirm=True)
    report = build_report(ExtractionResult(dimensions=[dim]), Profile(ho_so="HSC"))
    write_analysis(report, deps.settings().output_dir / "HSC")

    assert client.get("/api/report/HSC").json()["need_confirm"]  # trước: cần xác nhận
    r = client.post("/api/report/HSC/confirm", json={"index": 0})
    assert r.status_code == 200
    assert r.json()["need_confirm"] == []                        # sau: sạch
    assert r.json()["items"][0]["dimension"]["need_confirm"] is False
    assert r.json()["items"][0]["usable"] is True


def test_confirm_with_edited_value(client):
    from loban.models import Dimension, ExtractionResult, Profile
    from loban.pipeline import build_report
    from loban.render.analysis_json import write_analysis
    from loban.web import deps, jobs

    jobs.create_job("HSE", [], png=False, pdf=False)
    dim = Dimension(label="KT mờ", category="mo", kind="phu_bi", value_mm=None,
                    confidence="chua_xac_dinh", need_confirm=True)
    report = build_report(ExtractionResult(dimensions=[dim]), Profile(ho_so="HSE"))
    write_analysis(report, deps.settings().output_dir / "HSE")

    r = client.post("/api/report/HSE/confirm", json={"index": 0, "value_mm": 870})
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["dimension"]["value_mm"] == 870
    assert item["loban"]["cung"] == "Vượng"     # 870 trên 38.8 -> tính được


def test_delete_removes_job_and_files(client):
    client.post("/api/analyze", data={"ho_so": "HSD"},
                files=[("files", ("a.png", b"x", "image/png"))])
    _wait_done(client, "HSD")
    assert client.delete("/api/ho-so/HSD").status_code == 200
    assert client.get("/api/jobs/HSD").status_code == 404
    assert client.delete("/api/ho-so/HSD").status_code == 404   # xóa lần 2


def test_retry_requeues_and_runs(client):
    client.post("/api/analyze", data={"ho_so": "HSR"},
                files=[("files", ("a.png", b"x", "image/png"))])
    _wait_done(client, "HSR")
    r = client.post("/api/jobs/HSR/retry")
    assert r.status_code == 200 and r.json()["status"] == "queued"
    assert _wait_done(client, "HSR")["status"] == "done"


def test_rules_get_default(client):
    r = client.get("/api/rules").json()
    assert "categories" in r and "checklist" in r
    # cấu hình thước theo hạng mục đã bỏ hẳn
    assert not any(k.endswith("_ruler") for k in r)


def test_rules_put_khong_doi_duoc_thuoc(client):
    cfg = {"categories": [{"key": "mo", "label": "Mộ"}],
           "category_ruler": {"loi_di": "42.9", "mo": "52.2"}}
    saved = client.put("/api/rules", json=cfg)
    assert saved.status_code == 200
    assert "category_ruler" not in saved.json()      # key thước cũ bị loại khi lưu
    from loban.classify import ruler_for
    assert ruler_for("mo", "phu_bi") == "38.8"


def test_rules_put_invalid(client):
    r = client.put("/api/rules", json={"categories": "khong-phai-list"})
    assert r.status_code == 422


def test_ho_so_list_and_rulers(client):
    client.post(
        "/api/analyze",
        data={"ho_so": "HS04"},
        files=[("files", ("a.png", b"x", "image/png"))],
    )
    lst = client.get("/api/ho-so").json()
    assert any(j["ho_so"] == "HS04" for j in lst)
    rulers = client.get("/api/rulers").json()
    assert list(rulers["rulers"]) == ["38.8"]   # API chỉ trả thước 38.8
