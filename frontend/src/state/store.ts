import { create } from "zustand";
import type { SseEvent, VizChartSpec } from "../protocol";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type Session = { id: string; title: string; updated_at: number };

type StoreState = {
  apiKey: string;
  sessions: Session[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  streamingAssistantId: string | null;
  dashboard: VizChartSpec[];
  sqlPreview: string | null;
  tablePreview: { columns: string[]; rows: unknown[][] } | null;

  setApiKey: (k: string) => void;
  loadSessions: () => Promise<void>;
  createSession: () => Promise<void>;
  setActiveSession: (id: string) => void;
  sendMessage: (content: string) => Promise<void>;
  applySseEvent: (ev: SseEvent) => void;
};

export const useStore = create<StoreState>((set, get) => ({
  apiKey: localStorage.getItem("dashscope_api_key") ?? "",
  sessions: [],
  activeSessionId: null,
  messages: [],
  streamingAssistantId: null,
  dashboard: [],
  sqlPreview: null,
  tablePreview: null,

  setApiKey: (k: string) => {
    localStorage.setItem("dashscope_api_key", k);
    set({ apiKey: k });
  },

  loadSessions: async () => {
    const res = await fetch("/api/sessions");
    const data = (await res.json()) as any[];
    set({
      sessions: data.map((s) => ({ id: s.id, title: s.title, updated_at: s.updated_at })),
    });
    if (!get().activeSessionId && data[0]?.id) {
      get().setActiveSession(data[0].id);
    }
  },

  createSession: async () => {
    const res = await fetch("/api/sessions", { method: "POST" });
    const s = await res.json();
    set((st) => ({ sessions: [s, ...st.sessions] }));
    get().setActiveSession(s.id);
  },

  setActiveSession: (id: string) => {
    set({ activeSessionId: id, messages: [], dashboard: [], sqlPreview: null, tablePreview: null });
  },

  sendMessage: async (content: string) => {
    const sessionId = get().activeSessionId;
    if (!sessionId) return;
    const apiKey = get().apiKey.trim();

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content };
    const assistantId = crypto.randomUUID();
    const assistantMsg: ChatMessage = { id: assistantId, role: "assistant", content: "" };

    set((st) => ({
      messages: [...st.messages, userMsg, assistantMsg],
      streamingAssistantId: assistantId,
      sqlPreview: null,
      tablePreview: null,
    }));

    const es = new EventSource(`/api/chat/${sessionId}/stream`, { withCredentials: false } as any);

    // EventSource can't POST; fallback: use fetch to get a stream and manually parse SSE would be required.
    // To keep this demo simple and standards-compliant, we use a POST that returns SSE via fetch + reader.
    es.close();

    const resp = await fetch(`/api/chat/${sessionId}/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, api_key: apiKey || undefined }),
    });

    const reader = resp.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";
      for (const part of parts) {
        const lines = part.split("\n");
        const eventLine = lines.find((l) => l.startsWith("event:"));
        const dataLine = lines.find((l) => l.startsWith("data:"));
        if (!dataLine) continue;
        const jsonStr = dataLine.slice("data:".length).trim();
        try {
          const ev = JSON.parse(jsonStr) as SseEvent;
          get().applySseEvent(ev);
        } catch {
          // ignore
        }
        if (eventLine?.includes("done")) {
          // keep reading until server closes
        }
      }
    }
  },

  applySseEvent: (ev: SseEvent) => {
    const assistantId = get().streamingAssistantId;
    if (!assistantId) return;

    if (ev.type === "token") {
      const delta = (ev.payload as any).delta as string;
      set((st) => ({
        messages: st.messages.map((m) => (m.id === assistantId ? { ...m, content: m.content + delta } : m)),
      }));
    } else if (ev.type === "sql") {
      set({ sqlPreview: (ev.payload as any).sql as string });
    } else if (ev.type === "result") {
      set({
        tablePreview: { columns: (ev.payload as any).columns, rows: (ev.payload as any).rows },
      });
    } else if (ev.type === "viz") {
      const dashboard = (ev.payload as any).dashboard as VizChartSpec[];
      set({ dashboard });
    } else if (ev.type === "done") {
      set({ streamingAssistantId: null });
    } else if (ev.type === "error") {
      const msg = ((ev.payload as any).message as string) || "error";
      set((st) => ({
        messages: st.messages.map((m) => (m.id === assistantId ? { ...m, content: m.content + `\n\n[Error] ${msg}` } : m)),
        streamingAssistantId: null,
      }));
    }
  },
}));

