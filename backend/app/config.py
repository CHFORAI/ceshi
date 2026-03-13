from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    dashscope_api_key: Optional[str]
    dashscope_model: str
    sqlite_path: str
    max_rows: int
    sql_timeout_s: float


def get_settings() -> Settings:
    return Settings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("DASHCOPE_API_KEY"),
        dashscope_model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
        sqlite_path=os.getenv("SQLITE_PATH", os.path.abspath(os.path.join(os.getcwd(), "..", "data.db"))),
        max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
        sql_timeout_s=float(os.getenv("SQL_TIMEOUT_S", "3.0")),
    )

