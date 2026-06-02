import { FormEvent, useState } from "react";
import { useStream } from "@langchain/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = { id?: string; type: string; content: unknown };

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

export default function App() {
  const apiUrl =
    import.meta.env.VITE_LANGGRAPH_API_URL ?? "http://127.0.0.1:{{ cookiecutter.langgraph_port }}";

  const stream = useStream<{ messages: Message[] }>({
    apiUrl,
    assistantId: "agent",
  });

  const [input, setInput] = useState("");

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || stream.isLoading) return;
    setInput("");
    stream.submit({ messages: [{ type: "human", content: text }] });
  }

  return (
    <main>
      <h1>{{ cookiecutter.project_name }}</h1>

      <section className="chat" aria-label="Conversation">
        {stream.messages.length === 0 && (
          <p className="hint">
            Try: <em>"show me a table of three colors with hex codes"</em>
          </p>
        )}
        {stream.messages.map((msg, i) => (
          <article key={msg.id ?? i} className={`msg msg--${msg.type}`}>
            <header className="msg__role">{msg.type}</header>
            <div className="msg__body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{messageText(msg.content)}</ReactMarkdown>
            </div>
          </article>
        ))}
        {stream.isLoading && <p className="hint">...thinking</p>}
        {stream.error ? <p className="error">{String(stream.error)}</p> : null}
      </section>

      <form className="composer" onSubmit={onSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something..."
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
