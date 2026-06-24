import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ThinkingBlockProps = {
  body: string;
};

export default function ThinkingBlock({ body }: ThinkingBlockProps) {
  return (
    <details className="thinking-card">
      <summary className="thinking-card__summary">
        <span className="thinking-card__name">AI plan</span>
      </summary>
      <div className="thinking-card__body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
      </div>
    </details>
  );
}
