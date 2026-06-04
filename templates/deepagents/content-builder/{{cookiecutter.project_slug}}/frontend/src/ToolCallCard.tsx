import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import ImageCard from "./ImageCard";

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

const IMAGE_TOOL_NAMES = new Set(["generate_cover", "generate_social_image"]);
const IMAGE_PATH_RE = /(?:Image saved to )([^\s]+\.(?:png|jpg|jpeg|webp|gif))/i;

export default function ToolCallCard({ card, apiUrl }: { card: ToolCard; apiUrl: string }): ReactNode {
  const [open, setOpen] = useState(card.status === "pending");
  const previousStatus = useRef<Status>(card.status);

  useEffect(() => {
    if (previousStatus.current === "pending" && card.status === "done") {
      setOpen(false);
    }
    previousStatus.current = card.status;
  }, [card.status]);

  const isImageTool = IMAGE_TOOL_NAMES.has(card.name);
  const imagePath = isImageTool && card.result ? IMAGE_PATH_RE.exec(card.result)?.[1] ?? null : null;

  const label =
    card.name === "task"
      ? "Sub-agent: researcher"
      : isImageTool
        ? `Image: ${card.name}`
        : `Tool: ${card.name}`;
  const badge = card.status === "pending" ? "running…" : "done";

  return (
    <>
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
      {imagePath && <ImageCard path={imagePath} apiUrl={apiUrl} />}
    </>
  );
}
