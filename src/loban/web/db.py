"""SQLite state cho job/hồ sơ (plan W-D4).

Ponytail: gộp Job + HoSo thành 1 bảng — mỗi `ho_so` = 1 lần phân tích = 1 thư
mục output. Tách 2 bảng khi 1 hồ sơ cần nhiều lần chạy có lịch sử riêng.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine

from .deps import settings

# vòng đời status: queued -> extract -> classify -> render -> done | error
Status = str


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisJob(SQLModel, table=True):
    ho_so: str = Field(primary_key=True)
    status: Status = "queued"
    step: str | None = None          # thông điệp chi tiết cho UI (tùy chọn)
    error: str | None = None
    # profile hồ sơ (snapshot lúc submit)
    khach_hang: str | None = None
    dia_diem: str | None = None
    huong_cong: str | None = None
    vat_lieu: str | None = None
    note: str = ""
    cau_hoi: str = ""                # câu hỏi kèm lúc submit -> tự hỏi ở trang Report
    # flags render
    light: bool = False
    png: bool = True
    pdf: bool = True
    inputs: str = "[]"               # JSON list đường dẫn file bản vẽ
    n_dim: int | None = None         # số kích thước sau khi done
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings().db_url, connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(_engine)
        _migrate(_engine)
    return _engine


def _migrate(eng) -> None:
    """ADD COLUMN idempotent cho DB cũ (create_all không ALTER bảng có sẵn)."""
    with eng.connect() as c:
        cols = {r[1] for r in c.execute(text("PRAGMA table_info(analysisjob)"))}
        if "cau_hoi" not in cols:
            c.execute(text("ALTER TABLE analysisjob ADD COLUMN cau_hoi VARCHAR DEFAULT ''"))
            c.commit()


def reset_engine() -> None:
    """Dùng trong test — ép tạo lại engine sau khi đổi db_url."""
    global _engine
    _engine = None


def session() -> Session:
    return Session(engine())
