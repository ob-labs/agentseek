import { s } from "@hashbrownai/core";
import {
  exposeComponent,
  exposeMarkdown,
  type ExposedComponent,
  type UiKit,
  useJsonParser,
  useUiKit,
} from "@hashbrownai/react";
import { CopilotChatAssistantMessage, useAgentContext } from "@copilotkit/react-core/v2";
import { createContext, memo, useContext, type ComponentProps, type ComponentType, type ReactNode } from "react";

type AnyKit = UiKit<ExposedComponent<ComponentType<any>>>;

const LangChainUiKitContext = createContext<AnyKit | null>(null);

function Card({ children }: { children?: ReactNode }) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 12,
        marginBlock: 6,
        background: "#fff",
      }}
    >
      {children}
    </div>
  );
}

function Row({ gap, children }: { gap?: string; children?: ReactNode }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        flexWrap: "wrap",
        gap: gap ?? "8px",
        alignItems: "flex-start",
      }}
    >
      {children}
    </div>
  );
}

function Column({ children }: { children?: ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{children}</div>
  );
}

function SimpleChart({
  labels,
  values,
}: {
  labels: string[];
  values: number[];
}) {
  const max = Math.max(1, ...values.map((v) => Math.abs(v)));
  return (
    <div style={{ marginBlock: 8, fontFamily: "system-ui, sans-serif", fontSize: 13 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {labels.map((label, i) => {
          const v = values[i] ?? 0;
          const pct = (Math.abs(v) / max) * 100;
          return (
            <div key={`${label}-${i}`}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                <span>{label}</span>
                <span style={{ color: "#71717a" }}>{v}</span>
              </div>
              <div style={{ background: "#f4f4f5", borderRadius: 4, height: 8 }}>
                <div
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    borderRadius: 4,
                    background: "#18181b",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CodeBlock({ code, language }: { code: string; language?: string }) {
  return (
    <pre
      style={{
        background: "#0b1120",
        color: "#e4e4e7",
        padding: 12,
        borderRadius: 8,
        overflow: "auto",
        fontSize: 13,
      }}
    >
      {language ? (
        <div style={{ color: "#a1a1aa", fontSize: 11, marginBottom: 8 }}>{language}</div>
      ) : null}
      <code>{code}</code>
    </pre>
  );
}

function Button({ children }: { children?: ReactNode }) {
  return (
    <button
      type="button"
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 6,
        padding: "6px 12px",
        background: "#18181b",
        color: "#fafafa",
        cursor: "pointer",
        fontSize: 14,
      }}
    >
      {children}
    </button>
  );
}

export function LangChainGenerativeUiProvider({ children }: { children: ReactNode }) {
  const kit = useUiKit({
    components: [
      exposeMarkdown(),
      exposeComponent(Card, {
        name: "card",
        description: "Card to wrap generative UI content.",
        children: "any",
      }),
      exposeComponent(Row, {
        name: "row",
        description: "Horizontal row layout.",
        props: {
          gap: s.string("Tailwind gap size") as never,
        },
        children: "any",
      }),
      exposeComponent(Column, {
        name: "column",
        description: "Vertical column layout.",
        children: "any",
      }),
      exposeComponent(SimpleChart, {
        name: "chart",
        description: "Simple bar-style chart for numeric series.",
        props: {
          labels: s.array("Category labels", s.string("A label")),
          values: s.array("Numeric values", s.number("A value")),
        },
        children: false,
      }),
      exposeComponent(CodeBlock, {
        name: "code_block",
        description: "Syntax-highlighted code block.",
        props: {
          code: s.streaming.string("The code to display"),
          language: s.string("Programming language") as never,
        },
        children: false,
      }),
      exposeComponent(Button, {
        name: "button",
        description: "Clickable button.",
        children: "text",
      }),
    ],
  });

  useAgentContext({
    description: "output_schema",
    value: s.toJsonSchema(kit.schema),
  });

  return <LangChainUiKitContext.Provider value={kit}>{children}</LangChainUiKitContext.Provider>;
}

type MarkdownRendererProps = ComponentProps<typeof CopilotChatAssistantMessage.MarkdownRenderer>;

const HashbrownAssistantMarkdownInner = memo(function HashbrownAssistantMarkdownInner({
  kit,
  content,
  className,
  ...rest
}: MarkdownRendererProps & { kit: AnyKit }) {
  const { value } = useJsonParser(content ?? "", kit.schema);

  if (value) {
    const nodes = kit.render(value);
    return (
      <div className={`magic-text-output ${className ?? ""}`.trim()} {...rest}>
        {nodes}
      </div>
    );
  }

  if (!content?.trim()) {
    return null;
  }

  return <CopilotChatAssistantMessage.MarkdownRenderer content={content} className={className} {...rest} />;
});

export const HashbrownAssistantMarkdown = memo(function HashbrownAssistantMarkdown(
  props: MarkdownRendererProps,
) {
  const kit = useContext(LangChainUiKitContext);
  if (!kit) {
    const { content, className, ...rest } = props;
    return (
      <pre className={className} {...rest}>
        {content}
      </pre>
    );
  }
  return <HashbrownAssistantMarkdownInner {...props} kit={kit} />;
});
