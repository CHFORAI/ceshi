import React, { useEffect, useMemo, useState } from "react";
import { useStore } from "../state/store";
import { Dashboard } from "./Dashboard";

export function App() {
  const {
    apiKey,
    setApiKey,
    sessions,
    activeSessionId,
    loadSessions,
    createSession,
    setActiveSession,
    messages,
    sendMessage,
    dashboard,
    sqlPreview,
    tablePreview,
    streamingAssistantId,
  } = useStore();

  const [input, setInput] = useState("");

  useEffect(() => {
    loadSessions().catch(() => {});
  }, [loadSessions]);

  const activeTitle = useMemo(() => {
    return sessions.find((s) => s.id === activeSessionId)?.title ?? "—";
  }, [sessions, activeSessionId]);

  return (
    <div className="layout">
      <div className="panel">
        <div className="panelHeader">
          <div>
            <div className="panelTitle">会话</div>
            <div className="muted">API Key 将仅存本地浏览器</div>
          </div>
          <button className="btn" onClick={() => createSession()}>
            新建
          </button>
        </div>
        <div style={{ padding: 10, borderBottom: "1px solid var(--border)" }}>
          <div className="muted" style={{ marginBottom: 6 }}>DashScope API Key</div>
          <input
            className="input"
            type="password"
            placeholder="请输入你的百炼 API Key（DASHSCOPE_API_KEY）"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <div className="muted" style={{ marginTop: 6 }}>
            未填写会导致后端无法真实调用模型。
          </div>
        </div>
        <div className="list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={
                "listItem " + (s.id === activeSessionId ? "listItemActive" : "")
              }
              onClick={() => setActiveSession(s.id)}
            >
              <div style={{ overflow: "hidden" }}>
                <div style={{ fontWeight: 650, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                  {s.title}
                </div>
                <div className="muted">{new Date(s.updated_at).toLocaleString()}</div>
              </div>
              <div className="muted">›</div>
            </div>
          ))}
          {!sessions.length && (
            <div className="muted" style={{ padding: 10 }}>
              还没有会话，点击“新建”
            </div>
          )}
        </div>
      </div>

      <div className="panel chat">
        <div className="panelHeader">
          <div>
            <div className="panelTitle">问答</div>
            <div className="muted">当前会话：{activeTitle}</div>
          </div>
          <div className="muted">
            {streamingAssistantId ? "生成中…" : "就绪"}
          </div>
        </div>
        <div className="chatMessages">
          {messages.map((m) => (
            <div key={m.id} className={"msg " + (m.role === "user" ? "msgUser" : "msgAssistant")}>
              {m.content || (m.role === "assistant" ? "…" : "")}
            </div>
          ))}
          {!messages.length && (
            <div className="muted">在下方输入一个分析问题，比如：按月份统计订单金额趋势。</div>
          )}
          {sqlPreview && (
            <div className="msg msgAssistant">
              <div style={{ fontWeight: 700, marginBottom: 6 }}>SQL</div>
              <div className="muted" style={{ whiteSpace: "pre-wrap" }}>{sqlPreview}</div>
            </div>
          )}
          {tablePreview && (
            <div className="msg msgAssistant">
              <div style={{ fontWeight: 700, marginBottom: 6 }}>结果预览</div>
              <div className="muted">{tablePreview.columns.join(" | ")}</div>
              <div className="muted" style={{ marginTop: 6 }}>
                {tablePreview.rows.slice(0, 6).map((r, idx) => (
                  <div key={idx}>{r.join(" | ")}</div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="composer">
          <input
            className="input"
            placeholder="输入你的问题（自然语言）…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                if (input.trim()) {
                  sendMessage(input.trim()).catch(() => {});
                  setInput("");
                }
              }
            }}
          />
          <button
            className="btn"
            disabled={!activeSessionId || !input.trim() || !!streamingAssistantId}
            onClick={() => {
              if (input.trim()) {
                sendMessage(input.trim()).catch(() => {});
                setInput("");
              }
            }}
          >
            发送
          </button>
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <div>
            <div className="panelTitle">可视化</div>
            <div className="muted">仪表盘（多图布局/联动）</div>
          </div>
        </div>
        <div className="dashboard">
          <Dashboard charts={dashboard} tablePreview={tablePreview} />
        </div>
      </div>
    </div>
  );
}

