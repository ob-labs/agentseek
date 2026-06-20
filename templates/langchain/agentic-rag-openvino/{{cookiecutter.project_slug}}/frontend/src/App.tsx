import { FormEvent, useMemo, useState } from "react";
import { useStream } from "@langchain/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ToolCallCard, { type ToolCard } from "./ToolCallCard";

type RawToolCall = { id?: string; name?: string; args?: unknown };
type Message = {
  id?: string;
  type: string;
  content: unknown;
  tool_calls?: RawToolCall[];
  tool_call_id?: string;
  name?: string;
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
    import.meta.env.VITE_LANGGRAPH_API_URL ?? "http://127.0.0.1:2024";

  const stream = useStream<StreamState>({
    apiUrl,
    assistantId: "rag",
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
    <main>
      <h1>Agentic RAG</h1>

      <section className="chat" aria-label="Conversation">
        {rows.length === 0 && (
          <p className="hint">
            Ask a question about your indexed documents.
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
              <strong>Searching knowledge base</strong>
              <span>Retrieving and synthesizing relevant documents.</span>
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
          placeholder="Ask a question…"
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
