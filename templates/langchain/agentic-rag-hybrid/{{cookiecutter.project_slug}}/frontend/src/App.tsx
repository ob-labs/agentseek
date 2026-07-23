import { FormEvent, useMemo, useState } from "react";
import { useStream } from "@langchain/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import HybridCompare from "./HybridCompare";
import SampleLab from "./SampleLab";
import ToolCallCard, { type ToolCard } from "./ToolCallCard";

type RawToolCall = { id?: string; name?: string; args?: unknown };
type Message = {
  id?: string;
  type: string;
  content: unknown;
  artifact?: unknown;
  tool_calls?: RawToolCall[];
  tool_call_id?: string;
  name?: string;
};
type StreamState = {
  messages: Message[];
};

function defaultLangGraphApiUrl(): string {
  const host = window.location.hostname || "127.0.0.1";
  return `http://${host}:2024`;
}

function messageText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) =>
        typeof part === "string"
          ? part
          : typeof part === "object" && part !== null && "text" in part
            ? String((part as { text: unknown }).text ?? "")
            : "",
      )
      .join("");
  }
  return "";
}

type Row =
  | { kind: "prose"; key: string; type: "human" | "ai"; body: string }
  | { kind: "card"; key: string; card: ToolCard };

function buildRows(messages: Message[]): Row[] {
  const rows: Row[] = [];
  const cardByCallId = new Map<string, ToolCard>();
  for (const msg of messages) {
    if (msg.type === "human") {
      rows.push({
        kind: "prose",
        key: msg.id ?? `h-${rows.length}`,
        type: "human",
        body: messageText(msg.content),
      });
    } else if (msg.type === "ai") {
      const calls = msg.tool_calls ?? [];
      const body = messageText(msg.content).trim();
      if (body) {
        rows.push({
          kind: "prose",
          key: msg.id ?? `a-${rows.length}`,
          type: "ai",
          body,
        });
      }
      for (const call of calls) {
        const callId = call.id ?? `${msg.id}-${call.name}-${rows.length}`;
        const card: ToolCard = {
          callId,
          name: call.name ?? "tool",
          args: call.args ?? {},
          result: null,
          artifact: null,
          status: "pending",
        };
        cardByCallId.set(callId, card);
        rows.push({ kind: "card", key: `c-${callId}`, card });
      }
    } else if (msg.type === "tool") {
      const callId = msg.tool_call_id;
      if (callId && cardByCallId.has(callId)) {
        const card = cardByCallId.get(callId)!;
        card.result = messageText(msg.content);
        card.artifact = msg.artifact ?? null;
        card.status = "done";
      }
    }
  }
  return rows;
}

function ChatExperience() {
  const apiUrl =
    import.meta.env.VITE_LANGGRAPH_API_URL ?? defaultLangGraphApiUrl();

  const stream = useStream<StreamState>({
    apiUrl,
    assistantId: "hybrid-rag",
  });

  const [input, setInput] = useState("");
  const rows = useMemo(() => buildRows(stream.messages as Message[]), [stream.messages]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || stream.isLoading) return;
    setInput("");
    stream.submit({ messages: [{ type: "human", content: text }] });
  }

  return (
    <section className="chat-shell">
      <header className="workspace-panel workspace-panel--chat">
        <div>
          <p className="section-kicker">Ask agent</p>
          <h2>Let LangGraph choose the retrieval path.</h2>
          <p>Tool cards expose the hybrid trace when the agent searches indexed images.</p>
        </div>
      </header>

      <section className="chat" aria-label="Conversation">
        {rows.length === 0 && (
          <p className="hint">
            Try: Which image has a blue logo, and why did the agent choose it?
          </p>
        )}
        {rows.map((row) =>
          row.kind === "prose" ? (
            <article key={row.key} className={`msg msg--${row.type}`}>
              <header className="msg__role">{row.type}</header>
              <div className="msg__body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{row.body}</ReactMarkdown>
              </div>
            </article>
          ) : (
            <ToolCallCard key={row.key} card={row.card} />
          ),
        )}
        {stream.isLoading && (
          <div className="activity-card" aria-live="polite">
            <div className="activity-card__pulse" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <div className="activity-card__copy">
              <strong>Searching image knowledge base</strong>
              <span>Choosing a hybrid route and retrieving candidate images.</span>
            </div>
          </div>
        )}
        {stream.error ? <p className="error">{String(stream.error)}</p> : null}
      </section>

      <form className="composer" onSubmit={onSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about an indexed image, label, or visual detail"
          disabled={stream.isLoading}
        />
        <button type="submit" disabled={stream.isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </section>
  );
}

export default function App() {
  const [tab, setTab] = useState<"lab" | "compare" | "chat">("lab");
  const tabs = [
    { id: "lab", label: "Guided lab" },
    { id: "compare", label: "Compare modes" },
    { id: "chat", label: "Ask agent" },
  ] as const;

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="app-title">
          <p className="eyebrow">Agentic hybrid RAG</p>
          <h1>Hybrid image search lab</h1>
        </div>
        <div className="signal-strip" aria-label="Retrieval signals">
          <span className="signal-chip signal-chip--vector">vector</span>
          <span className="signal-chip signal-chip--text">keyword</span>
          <span className="signal-chip signal-chip--exact">exact</span>
          <span className="signal-chip signal-chip--meta">metadata</span>
        </div>
      </header>

      <nav className="tabs" aria-label="Hybrid RAG workspace">
        {tabs.map((item) => (
          <button
            className={tab === item.id ? "active" : ""}
            key={item.id}
            onClick={() => setTab(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === "lab" && <SampleLab />}
      {tab === "compare" && <HybridCompare />}
      {tab === "chat" && <ChatExperience />}
    </main>
  );
}
