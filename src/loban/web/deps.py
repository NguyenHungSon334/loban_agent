"""Settings + đường dẫn cho web layer (plan W-D3/W-D4/W-D6)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOBAN_WEB_", env_file=".env", extra="ignore"
    )
    output_dir: Path = Path("output")     # mỗi hồ sơ 1 thư mục con
    db_url: str = "sqlite:///web.db"       # SQLite — 1 VPS, không Redis
    worker_concurrency: int = 1            # số job nặng chạy song song; khớp RAM VPS (free tier -> 1)


@lru_cache
def settings() -> WebSettings:
    return WebSettings()
