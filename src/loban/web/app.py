"""FastAPI — 6 endpoint bọc pipeline + phục vụ frontend (plan W2/P9).

Không auth (nội bộ LAN/VPS — W-D5). 1 process uvicorn ôm asyncio pool (W-D6).
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import shutil
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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
    files: list[UploadFile] = File(default=[]),
    ho_so: str = Form(...),
    khach_hang: str | None = Form(None),
    dia_diem: str | None = Form(None),
    huong_cong: str | None = Form(None),
    vat_lieu: str | None = Form(None),
    note: str = Form(""),
    cau_hoi: str = Form(""),
    light: bool = Form(False),
    png: bool = Form(True),
    pdf: bool = Form(True),
):
    if not files and not (cau_hoi.strip() or note.strip()):
        raise HTTPException(422, "Cần file bản vẽ hoặc nhập số đo/câu hỏi")
    ma = _unique_ho_so(ho_so.strip())
    in_dir = settings().output_dir / ma / "input"
    in_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for f in files:
        dst = in_dir / Path(f.filename or "banve").name   # name -> chặn traversal
        dst.write_bytes(await f.read())
        saved.append(dst.resolve())   # path tuyệt đối -> retry/worker không lệ thuộc cwd

    jobs.create_job(
        ma, saved, khach_hang=khach_hang, dia_diem=dia_diem,
        huong_cong=huong_cong, vat_lieu=vat_lieu, note=note, cau_hoi=cau_hoi,
        light=light, png=png, pdf=pdf,
    )
    await worker.enqueue(ma)
    return {"ho_so": ma, "status": "queued"}


def _match_label(query: str, labels: list[str]) -> int | None:
    """Khớp tên hạng mục khách nói -> index. Chuẩn hóa dấu/hoa-thường để bớt trượt.
    Nhập nhằng (0 hoặc >1 khớp) -> None để tool hỏi lại, tránh sửa nhầm số đo."""
    from ..checklist import _norm

    q = _norm(query.strip())
    if not q:
        return None
    norm = [_norm(lb) for lb in labels]
    for i, lb in enumerate(norm):
        if lb == q:
            return i
    hits = [i for i, lb in enumerate(norm) if q in lb or lb in q]
    return hits[0] if len(hits) == 1 else None


import re

_EDIT_VERBS = ("đổi", "sửa", "chỉnh", "cập nhật", "thành", "set", "sang")


def _parse_mm(msg: str) -> float | None:
    """Bóc số đo ra mm từ câu chat. '1m2'->1200, '1m27'->1270, '1.27m'->1270,
    '490mm'->490, '49cm'->490, số trần >=100 coi là mm, <100 coi là cm."""
    m = msg.lower().replace(",", ".")
    x = re.search(r"(\d+)\s*m\s*(\d{1,2})\b", m)          # 1m2 / 1m27
    if x:
        d = x.group(2)
        return int(x.group(1)) * 1000 + int(d) * (100 if len(d) == 1 else 10)
    x = re.search(r"(\d+(?:\.\d+)?)\s*m(?![a-z])", m)     # 1.27m / 2m
    if x:
        return round(float(x.group(1)) * 1000)
    x = re.search(r"(\d+(?:\.\d+)?)\s*mm", m)             # 490mm
    if x:
        return round(float(x.group(1)))
    x = re.search(r"(\d+(?:\.\d+)?)\s*cm", m)             # 49cm
    if x:
        return round(float(x.group(1)) * 10)
    x = re.search(r"\b(\d+(?:\.\d+)?)\b", m)              # số trần
    if x:
        v = float(x.group(1))
        return round(v if v >= 100 else v * 10)
    return None


def _match_edit_label(msg: str, labels: list[str]) -> int | None:
    """Khớp nhãn cần sửa bằng cụm 2-3 từ đầu của nhãn xuất hiện trong câu. Mơ hồ -> None."""
    from ..checklist import _norm

    m = _norm(msg)
    hits = []
    for i, lb in enumerate(labels):
        words = _norm(lb).split()
        for n in (3, 2):
            if len(words) >= n and " ".join(words[:n]) in m:
                hits.append(i)
                break
    return hits[0] if len(hits) == 1 else None


def _forced_edit(ho_so: str, message: str) -> tuple[int, dict] | None:
    """Fallback: model không tự gọi tool -> tự sửa số đo khi câu lệnh RÕ là sửa.
    Trả (index, analysis_json_mới) nếu sửa được; None nếu không đủ chắc."""
    if not any(v in message.lower() for v in _EDIT_VERBS):
        return None
    value = _parse_mm(message)
    if value is None:
        return None
    name = Path(ho_so).name
    f = settings().output_dir / name / "analysis.json"
    if not f.exists():
        return None
    report = AnalysisReport.model_validate_json(f.read_text(encoding="utf-8"))
    labels = [it.dimension.label for it in report.items]
    idx = _match_edit_label(message, labels)
    if idx is None:
        return None
    try:
        data = apply_dimension_edit(name, idx, value)
    except (LookupError, ValueError):
        return None
    return idx, data


def _make_edit_tool(ho_so: str, on_edit=None):
    """Tool để Gemini sửa số đo trong hồ sơ hiện tại (function calling).
    on_edit() được gọi khi sửa thành công -> endpoint biết để báo UI refetch."""

    def sua_kich_thuoc(ten_hang_muc: str, value_mm: float) -> dict:
        """Sửa số đo 1 hạng mục trong hồ sơ rồi tính lại cung Lỗ Ban.

        CHỈ gọi khi khách yêu cầu ĐỔI/SỬA số đo (vd "đổi cổng thành 1m2").
        Args:
            ten_hang_muc: tên hạng mục như trong báo cáo (vd "Lọt lòng cổng").
            value_mm: số đo mới, tính bằng mm (1m2 -> 1200).
        """
        name = Path(ho_so).name
        f = settings().output_dir / name / "analysis.json"
        if not f.exists():
            return {"loi": "chưa có hồ sơ"}
        report = AnalysisReport.model_validate_json(f.read_text(encoding="utf-8"))
        labels = [it.dimension.label for it in report.items]
        idx = _match_label(ten_hang_muc, labels)
        if idx is None:
            return {"loi": f"không rõ hạng mục '{ten_hang_muc}'", "cac_hang_muc": labels}
        try:
            data = apply_dimension_edit(name, idx, value_mm)
        except (LookupError, ValueError) as e:
            return {"loi": str(e)}
        if on_edit:
            on_edit()
        lb = data["items"][idx]["loban"]
        return {
            "da_sua": labels[idx], "value_mm": value_mm,
            "cung": lb.get("cung"), "cung_nho": lb.get("cung_nho"),
            "tot": lb.get("cung_good"), "trang_thai": lb.get("status"),
        }

    return sua_kich_thuoc


@app.post("/api/chat")
async def chat_api(
    message: str = Form(...),
    ho_so: str | None = Form(None),
    files: list[UploadFile] | None = None,
):
    """Chat tư vấn Lỗ Ban. Hỏi nhanh (không ho_so) hoặc hỏi/sửa trong hồ sơ (có ho_so)."""
    import functools

    from ..chat import chat as run_chat

    images = [(await f.read(), f.content_type or "image/png") for f in (files or [])]
    context = None
    tools_extra = None
    edited = {"v": False}
    if ho_so:
        f = settings().output_dir / Path(ho_so).name / "analysis.json"
        if f.exists():
            context = f.read_text(encoding="utf-8")[:6000]   # gọn context, tránh tràn
            # cho phép sửa số đo; on_edit -> báo UI refetch báo cáo
            tools_extra = [_make_edit_tool(ho_so, on_edit=lambda: edited.__setitem__("v", True))]
    try:
        loop = asyncio.get_running_loop()
        call = functools.partial(
            run_chat, message, images or None, context, tools_extra=tools_extra
        )
        reply = await loop.run_in_executor(None, call)
    except Exception as e:  # noqa: BLE001 - lỗi LLM trả về UI, không 500
        raise HTTPException(502, f"Lỗi chat: {e}")

    # Fallback: model không tự gọi sua_kich_thuoc nhưng khách rõ ràng yêu cầu sửa
    # -> tự sửa số đo + ghi lại file, khỏi phụ thuộc model có chịu gọi tool hay không.
    if ho_so and not edited["v"]:
        forced = await loop.run_in_executor(None, _forced_edit, ho_so, message)
        if forced:
            idx, data = forced
            edited["v"] = True
            it = data["items"][idx]
            d, lo = it["dimension"], it["loban"]
            cung = lo.get("cung") or "—"
            if lo.get("cung_nho"):
                cung += f" › {lo['cung_nho']}"
            tt = "tốt" if lo.get("cung_good") else "chưa phù hợp"
            reply = f"Đã cập nhật {d['label']} thành {int(d['value_mm'])} mm — cung {cung} ({tt})."
    return {"reply": reply, "updated": edited["v"]}


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
    data = json.loads(f.read_text(encoding="utf-8"))
    job = jobs.get_job(ho_so)
    if job and job.cau_hoi:
        data["cau_hoi"] = job.cau_hoi   # trang Report tự hỏi câu này
    return JSONResponse(data)


def apply_dimension_edit(ho_so: str, index: int, value_mm: float | None) -> dict:
    """Sửa value_mm 1 kích thước -> tính lại Lỗ Ban + ghi output. Trả JSON analysis mới.

    Dùng chung cho endpoint /confirm và tool chat sua_kich_thuoc.
    Raise LookupError (404) / ValueError (422) để caller tự map lỗi.
    """
    job = jobs.get_job(ho_so)
    if job is None:
        raise LookupError("Không có hồ sơ")
    f = settings().output_dir / ho_so / "analysis.json"
    if not f.exists():
        raise LookupError("Chưa có kết quả")
    report = AnalysisReport.model_validate_json(f.read_text(encoding="utf-8"))
    dims = [it.dimension for it in report.items]
    if not 0 <= index < len(dims):
        raise ValueError("index không hợp lệ")

    d = dims[index]
    if value_mm is not None:
        d.value_mm = value_mm
    if d.value_mm is None:
        raise ValueError("Kích thước chưa có số — nhập value_mm để xác nhận")
    d.need_confirm = False       # đã xác nhận/sửa -> tin cậy cao, dùng cho kết luận
    d.confidence = "cao"
    d.estimated = False

    new = build_report(ExtractionResult(dimensions=dims), report.profile)
    worker.write_outputs(new, job, worker._drawing_bytes(job))
    jobs.set_status(ho_so, "done", n_dim=len(new.items))
    return json.loads(f.read_text(encoding="utf-8"))


class ConfirmIn(BaseModel):
    index: int                       # vị trí kích thước trong report.items
    value_mm: float | None = None    # số đã sửa/nhập tay (None = giữ số cũ, chỉ xác nhận)


@app.post("/api/report/{ho_so}/confirm")
def confirm(ho_so: str, payload: ConfirmIn):
    """Xác nhận 1 kích thước 'cần xác nhận' -> tính lại Lỗ Ban + ghi lại đầu ra ngay."""
    try:
        return JSONResponse(apply_dimension_edit(ho_so, payload.index, payload.value_mm))
    except LookupError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/jobs/{ho_so}/retry")
async def retry(ho_so: str):
    """Chạy lại từ đầu (extract lại bằng Gemini) trên đúng file bản vẽ đã lưu."""
    job = jobs.get_job(ho_so)
    if job is None:
        raise HTTPException(404, "Không có hồ sơ")
    # cho chạy lại khi còn ít nhất 1 file bản vẽ HOẶC còn số đo/câu hỏi dạng text
    has_file = any(p.exists() for p in jobs.input_paths(job))
    has_text = bool((job.note or "").strip() or (job.cau_hoi or "").strip())
    if not has_file and not has_text:
        raise HTTPException(422, "Không còn file bản vẽ và không có số đo để chạy lại")
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
