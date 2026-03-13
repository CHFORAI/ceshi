from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import Literal

from pydantic import BaseModel, Field


SseEventType = Literal["token", "tool_call", "sql", "result", "viz", "error", "done"]


class SseEvent(BaseModel):
    """
    Server-Sent Events payload contract shared by all streaming endpoints.
    The FastAPI endpoint will emit:
      - event: <type>
      - data: JSON string of this model
    """

    type: SseEventType
    trace_id: str
    session_id: str
    ts_ms: int
    payload: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1)
    api_key: Optional[str] = Field(default=None, description="DashScope (Bailian) API key for this request.")


class ChatTokenPayload(BaseModel):
    delta: str


class ChatSqlPayload(BaseModel):
    sql: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ChatResultPayload(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    truncated: bool = False


class VizLink(BaseModel):
    sourceChartId: str
    targetChartId: str
    trigger: Literal["click", "brush", "legend"]
    action: Literal["filter"]
    field: str


class VizLayout(BaseModel):
    x: int
    y: int
    w: int
    h: int


class VizChartSpec(BaseModel):
    chartId: str
    type: Literal["table", "line", "bar", "pie", "scatter", "area"]
    title: str
    queryRef: str
    dataBinding: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    layout: VizLayout
    links: List[VizLink] = Field(default_factory=list)


class VizDashboardPayload(BaseModel):
    dashboard: List[VizChartSpec]
    activeFilters: Dict[str, Any] = Field(default_factory=dict)


class ChatDonePayload(BaseModel):
    ok: bool = True
    message: Optional[str] = None

