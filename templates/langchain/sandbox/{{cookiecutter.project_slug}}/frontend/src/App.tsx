import { FormEvent, useMemo, useState } from "react";
import { useStream } from "@langchain/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ToolCallCard, { type ToolCard } from "./ToolCallCard";
import ConnectionBanner from "./ConnectionBanner";

type RawToolCall = { id?: string; name?: string; args?: unknown };
type Message = {
  id?: string;
  type: string;
  content: unknown;
  tool_calls?: RawToolCall[];
  tool_call_id?: string;
};

type StreamState = {
  messages: Message[];
};

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
      const body = messageText(msg.content).trim();
      if (body) {
        rows.push({ kind: "prose", key: msg.id ?? `h-${rows.length}`, type: "human", body });
      }
    } else if (msg.type === "ai") {
      const body = messageText(msg.content).trim();
      const calls = msg.tool_calls ?? [];
      if (body) {
        rows.push({ kind: "prose", key: msg.id ?? `a-${rows.length}`, type: "ai", body });
      }
      for (const call of calls) {
        const callId = call.id ?? `${msg.id}-${call.name}-${rows.length}`;
        const card: ToolCard = {
          callId,
          name: call.name ?? "tool",
          args: call.args ?? {},
          result: null,
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
        card.status = "done";
      }
    }
  }
  return rows;
}

export default function App() {
  const apiUrl =
    import.meta.env.VITE_LANGGRAPH_API_URL ?? "http://127.0.0.1:{{ cookiecutter.langgraph_port }}";

  const [threadId, setThreadId] = useState<string | undefined>(
    () =>
      new URLSearchParams(window.location.search).get("thread") ??
      sessionStorage.getItem("activeThreadId") ??
      undefined,
  );
  const [connected, setConnected] = useState(true);
  const [mountKey, setMountKey] = useState(0);

  const stream = useStream<StreamState>({
    apiUrl,
    assistantId: "sandbox",
    threadId,
    onThreadId: (id) => {
      setThreadId(id);
      sessionStorage.setItem("activeThreadId", id);
      const url = new URL(window.location.href);
      url.searchParams.set("thread", id);
      window.history.replaceState({}, "", url);
    },
  });

  function disconnect() {
    void stream.stop();
    setConnected(false);
  }

  function rejoin() {
    setMountKey((k) => k + 1);
    setConnected(true);
  }

  const [input, setInput] = useState("");
  const rows = useMemo(() => buildRows(stream.messages as Message[]), [stream.messages]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || stream.isLoading) return;
    setInput("");
    stream.submit({ messages: [{ type: "human", content: text }] });
  }

  const sessionUrl = threadId
    ? `${window.location.origin}${window.location.pathname}?thread=${threadId}`
    : null;

  return (
    <main key={mountKey}>
      <h1>{{ cookiecutter.project_name }}</h1>

      <ConnectionBanner
        connected={connected}
        sessionUrl={sessionUrl}
        onDisconnect={disconnect}
        onRejoin={rejoin}
        isLoading={stream.isLoading}
      />

      <section className="chat" aria-label="Sandbox conversation">
        {rows.length === 0 && (
          <p className="hint">
            Try: <em>"Create a Python hello-world script and run it"</em>
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
              <strong>Sandbox running</strong>
              <span>Executing commands in the isolated environment.</span>
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
          placeholder="Ask the coding agent…"
          disabled={stream.isLoading}
          autoFocus
        />
        <button type="submit" disabled={stream.isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </main>
  );
}
