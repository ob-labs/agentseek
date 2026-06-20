import { FormEvent, useMemo, useState } from "react";
import { useStream } from "@langchain/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = {
  id?: string;
  type: string;
  content: unknown;
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

type Row = { key: string; type: "human" | "ai"; body: string };

function buildRows(messages: Message[]): Row[] {
  const rows: Row[] = [];
  for (const msg of messages) {
    if (msg.type === "human" || msg.type === "ai") {
      const body = messageText(msg.content).trim();
      if (body) {
        rows.push({
          key: msg.id ?? `${msg.type}-${rows.length}`,
          type: msg.type,
          body,
        });
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
      <h1>OpenVINO RAG</h1>

      <section className="chat" aria-label="Conversation">
        {rows.length === 0 && (
          <p className="hint">
            Ask a question about your indexed documents.
          </p>
        )}
        {rows.map((row) => (
          <article key={row.key} className={`msg msg--${row.type}`}>
            <header className="msg__role">{row.type}</header>
            <div className="msg__body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{row.body}</ReactMarkdown>
            </div>
          </article>
        ))}
        {stream.isLoading && (
          <div className="activity-card" aria-live="polite">
            <div className="activity-card__pulse" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <div className="activity-card__copy">
              <strong>Thinking</strong>
              <span>Retrieving context and generating answer…</span>
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
