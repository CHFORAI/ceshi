from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from typing_extensions import Literal

import aiosqlite


Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Session:
    id: str
    title: str
    memory: Dict[str, Any]
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class Message:
    id: str
    session_id: str
    role: Role
    content: str
    meta: Dict[str, Any]
    created_at: int


async def list_sessions(sqlite_path: str) -> List[Session]:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, title, memory_json, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        )
        out: List[Session] = []
        for r in rows:
            out.append(
                Session(
                    id=r["id"],
                    title=r["title"],
                    memory=json.loads(r["memory_json"] or "{}"),
                    created_at=int(r["created_at"]),
                    updated_at=int(r["updated_at"]),
                )
            )
        return out


async def create_session(sqlite_path: str, title: Optional[str] = None) -> Session:
    now = int(time.time() * 1000)
    sid = str(uuid.uuid4())
    title = title or "New chat"
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(
            "INSERT INTO sessions(id,title,memory_json,created_at,updated_at) VALUES(?,?,?,?,?)",
            (sid, title, "{}", now, now),
        )
        await db.commit()
    return Session(id=sid, title=title, memory={}, created_at=now, updated_at=now)


async def rename_session(sqlite_path: str, session_id: str, title: str) -> None:
    now = int(time.time() * 1000)
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute("UPDATE sessions SET title=?, updated_at=? WHERE id=?", (title, now, session_id))
        await db.commit()


async def delete_session(sqlite_path: str, session_id: str) -> None:
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        await db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        await db.commit()


async def add_message(
    sqlite_path: str,
    session_id: str,
    role: Role,
    content: str,
    meta: Optional[Dict[str, Any]],
) -> Message:
    now = int(time.time() * 1000)
    mid = str(uuid.uuid4())
    meta = meta or {}
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(
            "INSERT INTO messages(id,session_id,role,content,meta_json,created_at) VALUES(?,?,?,?,?,?)",
            (mid, session_id, role, content, json.dumps(meta, ensure_ascii=False), now),
        )
        await db.execute("UPDATE sessions SET updated_at=? WHERE id=?", (now, session_id))
        await db.commit()
    return Message(id=mid, session_id=session_id, role=role, content=content, meta=meta, created_at=now)


async def get_recent_messages(sqlite_path: str, session_id: str, limit: int = 20) -> List[Message]:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, session_id, role, content, meta_json, created_at FROM messages WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit),
        )
        out: List[Message] = []
        for r in reversed(rows):
            out.append(
                Message(
                    id=r["id"],
                    session_id=r["session_id"],
                    role=r["role"],
                    content=r["content"],
                    meta=json.loads(r["meta_json"] or "{}"),
                    created_at=int(r["created_at"]),
                )
            )
        return out


async def get_session_memory(sqlite_path: str, session_id: str) -> Dict[str, Any]:
    async with aiosqlite.connect(sqlite_path) as db:
        row = await db.execute_fetchone("SELECT memory_json FROM sessions WHERE id=?", (session_id,))
        if not row:
            return {}
        return json.loads(row[0] or "{}")


async def set_session_memory(sqlite_path: str, session_id: str, memory: Dict[str, Any]) -> None:
    now = int(time.time() * 1000)
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(
            "UPDATE sessions SET memory_json=?, updated_at=? WHERE id=?",
            (json.dumps(memory, ensure_ascii=False), now, session_id),
        )
        await db.commit()

