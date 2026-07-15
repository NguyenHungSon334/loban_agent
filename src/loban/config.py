"""Cấu hình runtime — đọc từ .env (plan mục 3)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LOBAN_", extra="ignore")

    gemini_api_key: str = ""
    model_extract: str = "gemini-3.5-flash"        # bóc tách chính
    model_extract_light: str = "gemini-3.5-flash"  # ảnh đơn giản/rẻ
    extract_temperature: float = 0.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
