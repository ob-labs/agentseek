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

export default function ToolCallCard({ card }: { card: ToolCard }): ReactNode {
  const [open, setOpen] = useState(card.status === "pending");
  const previousStatus = useRef<Status>(card.status);

  useEffect(() => {
    if (previousStatus.current === "pending" && card.status === "done") {
      setOpen(false);
    }
    previousStatus.current = card.status;
  }, [card.status]);

  const label = `Tool: ${card.name}`;
  const badge = card.status === "pending" ? "running…" : "done";

  return (
    <details
      className={`tool-card tool-card--${card.status}`}
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
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
        {card.result !== null && (
          <div className="tool-card__section">
            <div className="tool-card__label">result</div>
            <pre className="tool-card__code tool-card__code--result">{card.result}</pre>
          </div>
        )}
      </div>
    </details>
  );
}
