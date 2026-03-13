from __future__ import annotations

import sqlite3
from typing import Any

import aiosqlite


async def get_schema_summary(sqlite_path: str, max_tables: int = 30, max_cols: int = 50) -> str:
    """
    Lightweight schema summary for LLM grounding.
    """
    async with aiosqlite.connect(f"file:{sqlite_path}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        tables = await db.execute_fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT ?",
            (max_tables,),
        )
        parts: list[str] = []
        for t in tables:
            name = t["name"]
            cols = await db.execute_fetchall(f"PRAGMA table_info('{name}')")
            col_names = [c[1] for c in cols][:max_cols]
            parts.append(f"- {name}({', '.join(col_names)})")
        return "\n".join(parts) if parts else "(no tables found)"

