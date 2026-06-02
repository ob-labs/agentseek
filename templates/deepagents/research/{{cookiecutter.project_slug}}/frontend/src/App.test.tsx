{% raw %}
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

vi.mock("@langchain/react", () => ({
  useStream: () => ({
    messages: [
      { id: "human-1", type: "human", content: "Research IBM" },
      {
        id: "ai-1",
        type: "ai",
        content: "",
        tool_calls: [
          {
            id: "call-1",
            name: "task",
            args: {
              description: "Research IBM's LangGraph work",
              subagent_type: "research-agent",
            },
          },
        ],
      },
      {
        id: "tool-1",
        type: "tool",
        tool_call_id: "call-1",
        content: "IBM summary",
      },
      {
        id: "ai-2",
        type: "ai",
        content: "IBM published a LangGraph guide.",
      },
    ],
    isLoading: false,
    error: null,
    submit: vi.fn(),
  }),
}));

afterEach(() => {
  cleanup();
});

describe("App", () => {
  it("renders sub-agent cards from streamed task tool calls", () => {
    render(<App />);

    expect(screen.getByText("Sub-agent: research-agent")).toBeTruthy();
    expect(screen.getByText("IBM summary")).toBeTruthy();
    expect(screen.getByText("IBM published a LangGraph guide.")).toBeTruthy();
  });
});
{% endraw %}
