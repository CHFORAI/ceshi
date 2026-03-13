export type SseEventType =
  | "token"
  | "tool_call"
  | "sql"
  | "result"
  | "viz"
  | "error"
  | "done";

export type SseEvent = {
  type: SseEventType;
  trace_id: string;
  session_id: string;
  ts_ms: number;
  payload: Record<string, unknown>;
};

export type ChatTokenPayload = { delta: string };

export type ChatSqlPayload = { sql: string; params?: Record<string, unknown> };

export type ChatResultPayload = {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  truncated?: boolean;
};

export type VizLink = {
  sourceChartId: string;
  targetChartId: string;
  trigger: "click" | "brush" | "legend";
  action: "filter";
  field: string;
};

export type VizLayout = { x: number; y: number; w: number; h: number };

export type VizChartSpec = {
  chartId: string;
  type: "table" | "line" | "bar" | "pie" | "scatter" | "area";
  title: string;
  queryRef: string;
  dataBinding?: Record<string, unknown>;
  options?: Record<string, unknown>;
  layout: VizLayout;
  links?: VizLink[];
};

export type VizDashboardPayload = {
  dashboard: VizChartSpec[];
  activeFilters?: Record<string, unknown>;
};

export type ChatDonePayload = { ok: boolean; message?: string };

