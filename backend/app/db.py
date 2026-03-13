from __future__ import annotations

import asyncio
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiosqlite


FORBIDDEN_SQL = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "attach",
    "detach",
    "pragma",
    "vacuum",
    "create",
    "replace",
)


def _looks_safe_select(sql: str) -> bool:
    s = " ".join(sql.strip().split()).lower()
    if not s.startswith("select"):
        return False
    # Block obvious multi-statement tricks.
    if ";" in s:
        return False
    return not any(f" {kw} " in f" {s} " for kw in FORBIDDEN_SQL)


@dataclass(frozen=True)
class SqlQueryResult:
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    truncated: bool
    elapsed_ms: int


async def execute_readonly_query(
    sqlite_path: str,
    sql: str,
    params: Optional[Dict[str, Any]],
    *,
    max_rows: int,
    timeout_s: float,
) -> SqlQueryResult:
    if not _looks_safe_select(sql):
        raise ValueError("Only safe SELECT queries are allowed.")

    start = time.time()
    params = params or {}

    async def _run() -> SqlQueryResult:
        async with aiosqlite.connect(f"file:{sqlite_path}?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            async with db.execute(sql, params) as cursor:
                rows: List[List[Any]] = []
                columns = [d[0] for d in cursor.description] if cursor.description else []
                async for row in cursor:
                    if len(rows) >= max_rows:
                        break
                    rows.append([row[c] for c in columns])
                # Try to detect truncation by checking if there's more data
                truncated = False
                extra = await cursor.fetchone()
                if extra is not None:
                    truncated = True
        elapsed_ms = int((time.time() - start) * 1000)
        return SqlQueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
            elapsed_ms=elapsed_ms,
        )

    try:
        return await asyncio.wait_for(_run(), timeout=timeout_s)
    except asyncio.TimeoutError as e:
        raise TimeoutError("SQL query timed out.") from e


async def init_meta_db(sqlite_path: str) -> None:
    # Ensure session/message tables exist (in same sqlite for simplicity).
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              memory_json TEXT NOT NULL DEFAULT '{}',
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
              id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              meta_json TEXT NOT NULL DEFAULT '{}',
              created_at INTEGER NOT NULL,
              FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at)")
        await db.commit()

