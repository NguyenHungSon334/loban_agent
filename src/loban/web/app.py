"""FastAPI — 6 endpoint bọc pipeline + phục vụ frontend (plan W2/P9).

Không auth (nội bộ LAN/VPS — W-D5). 1 process uvicorn ôm asyncio pool (W-D6).
"""
from __future__ import annotations

import io
import json
import logging
import shutil
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..classify import load_rules, save_rules
from ..models import AnalysisReport, ExtractionResult
from ..pipeline import build_report
from ..ruler import load_data
from . import jobs, worker
from .db import AnalysisJob
from .deps import settings

# tên file output cho phép tải — chặn path traversal (W-D8)
ALLOWED_PREFIXES = ("analysis.json", "report.pdf")
ALLOWED_SUFFIX = ".png"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # log INFO ra console để theo dõi tiến trình xử lý hồ sơ
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    await worker.start()          # spawn consumer + requeue job kẹt
    yield
    await worker.stop()


app = FastAPI(title="Agent Lỗ Ban", lifespan=lifespan)


def _unique_ho_so(ma: str) -> str:
    """W-D8: tránh 2 nhân viên đè output khi trùng mã."""
    if jobs.get_job(ma) is None:
        return ma
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{ma}-{stamp}"


def _job_dto(j: AnalysisJob) -> dict:
    return {
        "ho_so": j.ho_so,
        "status": j.status,
        "step": j.step,
        "error": j.error,
        "khach_hang": j.khach_hang,
        "dia_diem": j.dia_diem,
        "n_dim": j.n_dim,
        "created_at": j.created_at.isoformat(),
    }


@app.post("/api/analyze")
async def analyze(
    files: list[UploadFile],
    ho_so: str = Form(...),
    khach_hang: str | None = Form(None),
    dia_diem: str | None = Form(None),
    huong_cong: str | None = Form(None),
    vat_lieu: str | None = Form(None),
    note: str = Form(""),
    light: bool = Form(False),
    png: bool = Form(True),
    pdf: bool = Form(True),
):
    if not files:
        raise HTTPException(422, "Thiếu file bản vẽ")
    ma = _unique_ho_so(ho_so.strip())
    in_dir = settings().output_dir / ma / "input"
    in_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for f in files:
        dst = in_dir / Path(f.filename or "banve").name   # name -> chặn traversal
        dst.write_bytes(await f.read())
        saved.append(dst)

    jobs.create_job(
        ma, saved, khach_hang=khach_hang, dia_diem=dia_diem,
        huong_cong=huong_cong, vat_lieu=vat_lieu, note=note,
        light=light, png=png, pdf=pdf,
    )
    await worker.enqueue(ma)
    return {"ho_so": ma, "status": "queued"}


@app.get("/api/jobs/{ho_so}")
def job_status(ho_so: str):
    j = jobs.get_job(ho_so)
    if j is None:
        raise HTTPException(404, "Không có hồ sơ")
    return _job_dto(j)


@app.get("/api/report/{ho_so}")
def report(ho_so: str):
    f = settings().output_dir / ho_so / "analysis.json"
    if not f.exists():
        raise HTTPException(404, "Chưa có kết quả")
    return JSONResponse(json.loads(f.read_text(encoding="utf-8")))


class ConfirmIn(BaseModel):
    index: int                       # vị trí kích thước trong report.items
    value_mm: float | None = None    # số đã sửa/nhập tay (None = giữ số cũ, chỉ xác nhận)


@app.post("/api/report/{ho_so}/confirm")
def confirm(ho_so: str, payload: ConfirmIn):
    """Xác nhận 1 kích thước 'cần xác nhận' -> tính lại Lỗ Ban + ghi lại đầu ra ngay."""
    job = jobs.get_job(ho_so)
    if job is None:
        raise HTTPException(404, "Không có hồ sơ")
    f = settings().output_dir / ho_so / "analysis.json"
    if not f.exists():
        raise HTTPException(404, "Chưa có kết quả")
    report = AnalysisReport.model_validate_json(f.read_text(encoding="utf-8"))
    dims = [it.dimension for it in report.items]
    if not 0 <= payload.index < len(dims):
        raise HTTPException(422, "index không hợp lệ")

    d = dims[payload.index]
    if payload.value_mm is not None:
        d.value_mm = payload.value_mm
    if d.value_mm is None:
        raise HTTPException(422, "Kích thước chưa có số — nhập value_mm để xác nhận")
    d.need_confirm = False       # đã xác nhận -> tin cậy cao, dùng cho kết luận
    d.confidence = "cao"
    d.estimated = False

    new = build_report(ExtractionResult(dimensions=dims), report.profile)
    worker.write_outputs(new, job, worker._drawing_bytes(job))
    jobs.set_status(ho_so, "done", n_dim=len(new.items))
    return JSONResponse(json.loads(f.read_text(encoding="utf-8")))


@app.post("/api/jobs/{ho_so}/retry")
async def retry(ho_so: str):
    """Chạy lại từ đầu (extract lại bằng Gemini) trên đúng file bản vẽ đã lưu."""
    job = jobs.get_job(ho_so)
    if job is None:
        raise HTTPException(404, "Không có hồ sơ")
    if not jobs.input_paths(job):
        raise HTTPException(422, "Không còn file bản vẽ để chạy lại")
    jobs.set_status(ho_so, "queued")   # xóa lỗi cũ
    await worker.enqueue(ho_so)
    return {"ho_so": ho_so, "status": "queued"}


@app.delete("/api/ho-so/{ho_so}")
def delete_ho_so(ho_so: str):
    """Xóa hồ sơ: bản ghi DB + toàn bộ thư mục output/<ho_so>."""
    existed = jobs.delete_job(ho_so)
    shutil.rmtree(settings().output_dir / ho_so, ignore_errors=True)
    if not existed:
        raise HTTPException(404, "Không có hồ sơ")
    return {"deleted": ho_so}


@app.get("/api/ho-so")
def ho_so_list(offset: int = 0, limit: int = 20):
    return [_job_dto(j) for j in jobs.list_jobs(offset, limit)]


@app.get("/api/rulers")
def rulers():
    return load_data()


@app.get("/api/rules")
def get_rules():
    return load_rules()


@app.put("/api/rules")
def put_rules(cfg: dict):
    try:
        return save_rules(cfg)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/api/bundle/{ho_so}")
def bundle(ho_so: str, kind: str = "png"):
    """Zip nhiều file cùng loại để tải 1 lần (png nhiều trang, hoặc all)."""
    ho_so = Path(ho_so).name          # chặn traversal
    d = settings().output_dir / ho_so
    if not d.exists():
        raise HTTPException(404, "Không có hồ sơ")
    if kind == "png":
        files = sorted(d.glob("png_*.png"))
    elif kind == "all":
        files = sorted(
            p for p in d.iterdir()
            if p.is_file() and (p.name in ALLOWED_PREFIXES or p.suffix == ALLOWED_SUFFIX)
        )
    else:
        raise HTTPException(422, "kind không hợp lệ")
    if not files:
        raise HTTPException(404, "Không có file")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.name)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{ho_so}_{kind}.zip"'},
    )


@app.get("/api/files/{ho_so}/{name}")
def download(ho_so: str, name: str):
    name = Path(name).name  # chặn traversal
    if not (name in ALLOWED_PREFIXES or name.endswith(ALLOWED_SUFFIX)):
        raise HTTPException(403, "File không cho phép")
    f = settings().output_dir / ho_so / name
    if not f.exists():
        raise HTTPException(404, "Không có file")
    return FileResponse(f)


# phục vụ frontend build (prod) — mount cuối để không nuốt /api
_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="spa")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104 - nội bộ VPS
