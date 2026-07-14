import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

type Status = "pending" | "done";

export type ToolCard = {
  callId: string;
  name: string;
  args: unknown;
  result: string | null;
  status: Status;
};

function formatArgs(args: unknown): string {
  try {
    return JSON.stringify(args, null, 2);
  } catch {
    return String(args);
  }
}

function cardLabel(name: string): string {
  switch (name) {
    case "execute":
      return "Shell: execute";
    case "read_file":
      return "File: read";
    case "write_file":
      return "File: write";
    case "edit_file":
      return "File: edit";
    case "ls":
      return "Directory: list";
    case "glob":
      return "File: glob";
    case "grep":
      return "File: grep";
    default:
      return `Tool: ${name}`;
  }
}

function ExecuteBody({ card }: { card: ToolCard }) {
  const args = card.args as Record<string, unknown> | null;
  const command = args?.command ? String(args.command) : formatArgs(card.args);

  return (
    <div className="tool-card__body">
      <div className="tool-card__section">
        <div className="tool-card__label">command</div>
        <pre className="tool-card__code tool-card__code--command">{command}</pre>
      </div>
      {card.result !== null && (
        <div className="tool-card__section">
          <div className="tool-card__label">output</div>
          <pre className="tool-card__code tool-card__code--result">{card.result}</pre>
        </div>
      )}
    </div>
  );
}

function FileBody({ card }: { card: ToolCard }) {
  const args = card.args as Record<string, unknown> | null;
  const path = args?.path ?? args?.file_path ?? "";

  return (
    <div className="tool-card__body">
      <div className="tool-card__section">
        <div className="tool-card__label">path</div>
        <pre className="tool-card__code">{String(path)}</pre>
      </div>
      {args?.content != null && (
        <div className="tool-card__section">
          <div className="tool-card__label">content</div>
          <pre className="tool-card__code tool-card__code--result">{String(args.content)}</pre>
        </div>
      )}
      {card.result !== null && (
        <div className="tool-card__section">
          <div className="tool-card__label">result</div>
          <pre className="tool-card__code tool-card__code--result">{card.result}</pre>
        </div>
      )}
    </div>
  );
}

function GenericBody({ card }: { card: ToolCard }) {
  return (
    <div className="tool-card__body">
      <div className="tool-card__section">
        <div className="tool-card__label">arguments</div>
        <pre className="tool-card__code">{formatArgs(card.args)}</pre>
      </div>
      {card.result !== null && (
        <div className="tool-card__section">
          <div className="tool-card__label">result</div>
          <pre className="tool-card__code tool-card__code--result">{card.result}</pre>
        </div>
      )}
    </div>
  );
}

export default function ToolCallCard({ card }: { card: ToolCard }): ReactNode {
  const [open, setOpen] = useState(card.status === "pending");
  const previousStatus = useRef<Status>(card.status);

  useEffect(() => {
    if (previousStatus.current === "pending" && card.status === "done") {
      setOpen(false);
    }
    previousStatus.current = card.status;
  }, [card.status]);

  const isFile = ["read_file", "write_file", "edit_file"].includes(card.name);
  const isExecute = card.name === "execute";
  const badge = card.status === "pending" ? "running…" : "done";

  return (
    <details
      className={`tool-card tool-card--${card.status}`}
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
    >
      <summary className="tool-card__summary">
        <span className="tool-card__name">{cardLabel(card.name)}</span>
        <span className={`tool-card__badge tool-card__badge--${card.status}`}>{badge}</span>
      </summary>
      {isExecute ? (
        <ExecuteBody card={card} />
      ) : isFile ? (
        <FileBody card={card} />
      ) : (
        <GenericBody card={card} />
      )}
    </details>
  );
}
