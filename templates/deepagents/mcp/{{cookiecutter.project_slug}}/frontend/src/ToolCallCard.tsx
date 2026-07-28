import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

type Status = "pending" | "done" | "error";

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

export default function ToolCallCard({ card }: { card: ToolCard }): ReactNode {
  const [open, setOpen] = useState(card.status !== "done");
  const previousStatus = useRef<Status>(card.status);

  useEffect(() => {
    if (previousStatus.current === "pending" && card.status === "done") {
      setOpen(false);
    } else if (card.status === "error") {
      setOpen(true);
    }
    previousStatus.current = card.status;
  }, [card.status]);

  const label = `mcp/${card.name}`;
  const badge = card.status === "pending" ? "running" : card.status === "error" ? "error" : "success";

  return (
    <details
      className={`tool-card tool-card--${card.status}`}
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
      aria-label={`${label} ${badge}`}
    >
      <summary className="tool-card__summary">
        <span className="tool-card__name">{label}</span>
        <span className={`tool-card__badge tool-card__badge--${card.status}`}>{badge}</span>
      </summary>
      <div className="tool-card__body">
        <div className="tool-card__section">
          <div className="tool-card__label">arguments</div>
          <pre className="tool-card__code">{formatArgs(card.args)}</pre>
        </div>
        {card.status === "error" ? (
          <p className="tool-card__error" role="alert">
            <strong>Tool {card.name} failed.</strong>{" "}
            {card.result || "No error details were returned."}
          </p>
        ) : card.result !== null ? (
          <div className="tool-card__section">
            <div className="tool-card__label">result</div>
            <pre className="tool-card__code tool-card__code--result">{card.result}</pre>
          </div>
        ) : null}
      </div>
    </details>
  );
}
