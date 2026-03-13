from __future__ import annotations

import json
import time
import uuid
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .agent import run_agent_once
from .config import get_settings
from .db import init_meta_db
from .llm_qwen import Qwen3Client
from .protocol import ChatRequest, SseEvent
from .schema_introspect import get_schema_summary
from .session_store import (
    add_message,
    create_session,
    delete_session,
    list_sessions,
    rename_session,
)


load_dotenv()
settings = get_settings()
app = FastAPI(title="Intelligent Data Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = Qwen3Client(api_key=settings.dashscope_api_key, model=settings.dashscope_model)


@app.on_event("startup")
async def _startup() -> None:
    await init_meta_db(settings.sqlite_path)


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "sqlite_path": settings.sqlite_path, "model": settings.dashscope_model}


@app.get("/api/sessions")
async def api_list_sessions():
    return [s.__dict__ for s in await list_sessions(settings.sqlite_path)]


@app.post("/api/sessions")
async def api_create_session():
    s = await create_session(settings.sqlite_path)
    return s.__dict__


@app.patch("/api/sessions/{session_id}")
async def api_rename_session(session_id: str, body: dict):
    title = (body or {}).get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Missing title")
    await rename_session(settings.sqlite_path, session_id, title)
    return {"ok": True}


@app.delete("/api/sessions/{session_id}")
async def api_delete_session(session_id: str):
    await delete_session(settings.sqlite_path, session_id)
    return {"ok": True}


def _sse(event: SseEvent) -> str:
    return f"event: {event.type}\n" + f"data: {event.model_dump_json()}\n\n"

def _log(trace_id: str, msg: str, **fields) -> None:
    # Minimal structured logging; can be replaced by loguru/structlog later.
    rec = {"ts_ms": int(time.time() * 1000), "trace_id": trace_id, "msg": msg, **fields}
    print(json.dumps(rec, ensure_ascii=False))


@app.post("/api/chat/{session_id}/stream")
async def chat_stream(session_id: str, req: ChatRequest):
    trace_id = str(uuid.uuid4())

    async def gen() -> AsyncIterator[str]:
        ts0 = int(time.time() * 1000)
        _log(trace_id, "chat_start", session_id=session_id)
        await add_message(settings.sqlite_path, session_id, "user", req.content, {"trace_id": trace_id})

        schema_summary = await get_schema_summary(settings.sqlite_path)

        # Emit a small tool_call event so the UI can show "planning..."
        yield _sse(
            SseEvent(
                type="tool_call",
                trace_id=trace_id,
                session_id=session_id,
                ts_ms=ts0,
                payload={"name": "planner", "status": "start"},
            )
        )

        api_key = (req.api_key or "").strip() or settings.dashscope_api_key
        if not api_key:
            msg = "Missing API key. Please provide it in request body (api_key) or set DASHSCOPE_API_KEY."
            _log(trace_id, "missing_api_key", session_id=session_id)
            yield _sse(
                SseEvent(
                    type="error",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"message": msg},
                )
            )
            yield _sse(
                SseEvent(
                    type="done",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"ok": False},
                )
            )
            return

        try:
            result = await run_agent_once(
                llm_complete=lambda messages: llm.complete(messages, api_key=api_key),
                question=req.content,
                schema_summary=schema_summary,
                sqlite_path=settings.sqlite_path,
                max_rows=settings.max_rows,
                sql_timeout_s=settings.sql_timeout_s,
            )
        except Exception as e:
            _log(trace_id, "chat_error", session_id=session_id, error=str(e))
            yield _sse(
                SseEvent(
                    type="error",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"message": str(e)},
                )
            )
            yield _sse(
                SseEvent(
                    type="done",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"ok": False},
                )
            )
            return

        # Stream answer as tokens (cheap approximation: chunk by characters).
        # If you need true model token streaming, switch to llm.stream and generate the plan differently.
        answer = result.answer or ""
        for chunk in [answer[i : i + 12] for i in range(0, len(answer), 12)]:
            yield _sse(
                SseEvent(
                    type="token",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"delta": chunk},
                )
            )

        if result.sql:
            _log(trace_id, "sql_generated", sql=result.sql)
            yield _sse(
                SseEvent(
                    type="sql",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"sql": result.sql, "params": result.params or {}},
                )
            )
        if result.columns is not None and result.rows is not None:
            _log(trace_id, "sql_result", row_count=result.row_count or 0, truncated=bool(result.truncated))
            yield _sse(
                SseEvent(
                    type="result",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={
                        "columns": result.columns,
                        "rows": result.rows,
                        "row_count": result.row_count or 0,
                        "truncated": bool(result.truncated),
                    },
                )
            )
        if result.dashboard:
            _log(trace_id, "viz_spec", charts=len(result.dashboard))
            yield _sse(
                SseEvent(
                    type="viz",
                    trace_id=trace_id,
                    session_id=session_id,
                    ts_ms=int(time.time() * 1000),
                    payload={"dashboard": result.dashboard, "activeFilters": {}},
                )
            )

        await add_message(settings.sqlite_path, session_id, "assistant", answer, {"trace_id": trace_id})
        _log(trace_id, "chat_done", session_id=session_id)
        yield _sse(
            SseEvent(
                type="done",
                trace_id=trace_id,
                session_id=session_id,
                ts_ms=int(time.time() * 1000),
                payload={"ok": True},
            )
        )

    return StreamingResponse(gen(), media_type="text/event-stream")

