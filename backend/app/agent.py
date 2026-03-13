from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .db import execute_readonly_query


class SqlPlan(BaseModel):
    sql: str = Field(..., description="A single SQLite SELECT statement. Must be safe and read-only.")
    params: Dict[str, Any] = Field(default_factory=dict, description="SQLite named parameters dict.")
    queryRef: str = Field(default="q1", description="Unique query reference id.")


class ChartPlan(BaseModel):
    chartId: str
    type: str
    title: str
    queryRef: str
    dataBinding: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    layout: Dict[str, Any] = Field(
        default_factory=lambda: {"x": 0, "y": 0, "w": 6, "h": 7},
        description="Grid layout for react-grid-layout: x,y,w,h",
    )
    links: List[Dict[str, Any]] = Field(default_factory=list)


class AgentPlan(BaseModel):
    answer: str = Field(..., description="Concise natural language answer.")
    sql: Optional[SqlPlan] = None
    dashboard: List[ChartPlan] = Field(default_factory=list)


@dataclass(frozen=True)
class AgentResult:
    answer: str
    sql: Optional[str]
    params: Optional[Dict[str, Any]]
    columns: Optional[List[str]]
    rows: Optional[List[List[Any]]]
    row_count: Optional[int]
    truncated: Optional[bool]
    dashboard: List[Dict[str, Any]]


SYSTEM_RULES = """你是一个智能数据分析助手。你可以基于用户问题生成 SQLite 查询并解释结果，并生成前端可视化仪表盘规格。
约束：
- 只允许生成一个 SQL，并且必须是 SELECT 开头。
- 默认添加 LIMIT（建议 200）。
- 不要编造不存在的表和字段；如果不知道 schema，请先要求用户提供表结构（但本系统会尽量提供 schema 摘要）。
- 你必须输出一个 JSON 对象，不要输出多余文本。"""

def build_planner_messages(schema_summary: str, question: str) -> List[Dict[str, str]]:
    schema = AgentPlan.model_json_schema()
    base = [
        {"role": "system", "content": SYSTEM_RULES},
        {"role": "system", "content": f"数据库 schema 摘要如下（可能不完整，仅供参考）：\n{schema_summary}"},
        {
            "role": "system",
            "content": "请严格输出一个 JSON（不要 Markdown code fence），其结构必须符合如下 JSON Schema：\n"
            + json.dumps(schema, ensure_ascii=False),
        },
        {"role": "user", "content": question},
    ]
    # If LangChain is available in the environment, we still keep messages in an OpenAI-like format.
    # This preserves the "LangChain + FastAPI" integration path without making runtime hard-depend on it.
    try:
        from langchain.prompts import PromptTemplate  # type: ignore

        _ = PromptTemplate.from_template("noop")  # smoke import
    except Exception:
        return base
    return base


async def run_agent_once(
    *,
    llm_complete: callable,
    question: str,
    schema_summary: str,
    sqlite_path: str,
    max_rows: int,
    sql_timeout_s: float,
) -> AgentResult:
    msgs = build_planner_messages(schema_summary=schema_summary, question=question)
    text = llm_complete(msgs)
    try:
        plan = AgentPlan.model_validate_json(text)
    except Exception:
        # If the model adds leading/trailing text, try to extract the first JSON object.
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0 and end > start:
            plan = AgentPlan.model_validate_json(text[start : end + 1])
        else:
            raise

    columns = rows = None
    row_count = None
    truncated = None
    sql = None
    params = None

    if plan.sql:
        sql = plan.sql.sql
        params = plan.sql.params
        qr = await execute_readonly_query(
            sqlite_path,
            sql,
            params,
            max_rows=max_rows,
            timeout_s=sql_timeout_s,
        )
        columns = qr.columns
        rows = qr.rows
        row_count = qr.row_count
        truncated = qr.truncated

    return AgentResult(
        answer=plan.answer,
        sql=sql,
        params=params,
        columns=columns,
        rows=rows,
        row_count=row_count,
        truncated=truncated,
        dashboard=[c.model_dump() for c in plan.dashboard],
    )

