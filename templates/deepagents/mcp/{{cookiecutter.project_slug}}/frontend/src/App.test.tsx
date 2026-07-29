{% raw %}
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const streamState: {
  values: { todos?: Array<{ content: string; status: "completed" | "in_progress" | "pending" }> };
  messages: Array<Record<string, unknown>>;
  isLoading: boolean;
  error: unknown;
  submit: ReturnType<typeof vi.fn>;
} = {
  values: {
    todos: [
      { content: "Inspect calculator tool schema", status: "completed" },
      { content: "Call calculator_add", status: "in_progress" },
      { content: "Return the computed result", status: "pending" },
    ],
  },
  messages: [
    { id: "human-1", type: "human", content: "Add 19 and 23 with the calculator tool." },
    {
      id: "ai-1",
      type: "ai",
      content: "",
      tool_calls: [
        {
          id: "call-1",
          name: "calculator_add",
          args: { a: 19, b: 23 },
        },
      ],
    },
    {
      id: "tool-1",
      type: "tool",
      tool_call_id: "call-1",
      content: "42",
      status: "success",
    },
    {
      id: "ai-2",
      type: "ai",
      content: "The calculator returned 42.",
    },
  ],
  isLoading: false,
  error: null,
  submit: vi.fn(),
};

let capturedStreamOptions: Record<string, unknown> | null = null;

vi.mock("@langchain/react", () => ({
  useStream: (options: Record<string, unknown>) => {
    capturedStreamOptions = options;
    return streamState;
  },
}));

afterEach(() => {
  cleanup();
  capturedStreamOptions = null;
  window.history.replaceState({}, "", "http://localhost:3000/");
  streamState.isLoading = false;
  streamState.error = null;
  streamState.values = {
    todos: [
      { content: "Inspect calculator tool schema", status: "completed" },
      { content: "Call calculator_add", status: "in_progress" },
      { content: "Return the computed result", status: "pending" },
    ],
  };
  streamState.messages = [
    { id: "human-1", type: "human", content: "Add 19 and 23 with the calculator tool." },
    {
      id: "ai-1",
      type: "ai",
      content: "",
      tool_calls: [
        {
          id: "call-1",
          name: "calculator_add",
          args: { a: 19, b: 23 },
        },
      ],
    },
    {
      id: "tool-1",
      type: "tool",
      tool_call_id: "call-1",
      content: "42",
      status: "success",
    },
    {
      id: "ai-2",
      type: "ai",
      content: "The calculator returned 42.",
    },
  ];
});

describe("App", () => {
  it("keeps a durable accessible label on the message composer", () => {
    render(<App />);

    const composer = screen.getByRole("textbox", { name: "Message the MCP agent" });
    expect(composer.getAttribute("placeholder")).toBe("Ask the MCP-enabled agent…");
  });

  it("connects the browser to the mcp graph on the browser host", () => {
    render(<App />);

    expect(capturedStreamOptions?.assistantId).toBe("mcp");
    const apiUrl = new URL(String(capturedStreamOptions?.apiUrl));
    expect(apiUrl.protocol).toBe("http:");
    expect(apiUrl.hostname).toBe(window.location.hostname);
  });

  it("shows that a thread URL will be added after the first message", () => {
    render(<App />);

    expect(screen.getByText("Thread link ready")).toBeTruthy();
    expect(
      screen.getByText(
        "Send the first message to create a reusable URL for this streamed run.",
      ),
    ).toBeTruthy();
  });

  it("renders live todo progress from deepagents state", () => {
    render(<App />);

    expect(screen.getByText("Execution plan")).toBeTruthy();
    expect(screen.getByText("1/3 completed")).toBeTruthy();
    expect(screen.getByText("33%")).toBeTruthy();
    expect(screen.getByText("Inspect calculator tool schema")).toBeTruthy();
    expect(screen.getByText("Call calculator_add")).toBeTruthy();
    expect(screen.getByText("Return the computed result")).toBeTruthy();
  });

  it("renders prefixed calculator cards from streamed MCP tool calls", () => {
    render(<App />);

    expect(screen.getByText("mcp/calculator_add")).toBeTruthy();
    expect(screen.getByText("42")).toBeTruthy();
    expect(screen.getByText("The calculator returned 42.")).toBeTruthy();
  });

  it("renders structured reasoning beside mixed ai text and tool calls", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Add 19 and 23." },
      {
        id: "ai-1",
        type: "ai",
        content: [
          {
            type: "reasoning",
            reasoning:
              "## SESSION INTENT\nUse the calculator tool.\n\n## SUMMARY\nThe user requested a specific multi-step workflow.",
          },
          { type: "text", text: "I will use the calculator." },
        ],
        tool_calls: [
          {
            id: "call-1",
            name: "calculator_add",
            args: { a: 19, b: 23 },
          },
        ],
      },
      {
        id: "tool-1",
        type: "tool",
        tool_call_id: "call-1",
        content: "42",
        status: "success",
      },
    ];

    render(<App />);

    expect(screen.getByText("Agent plan")).toBeTruthy();
    expect(screen.getByText("SESSION INTENT")).toBeTruthy();
    expect(screen.getByText("Agent plan").closest("details")?.hasAttribute("open")).toBe(false);
    expect(screen.getByText("I will use the calculator.")).toBeTruthy();
    expect(screen.getByText("mcp/calculator_add")).toBeTruthy();
    expect(screen.getByText("42")).toBeTruthy();
  });

  it("renders a standalone reasoning block as a collapsed agent plan block", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Add 19 and 23." },
      {
        id: "ai-1",
        type: "ai",
        content: [
          {
            type: "reasoning",
            reasoning:
              "## SESSION INTENT\nUse the calculator tool.\n\n## SUMMARY\nThe user requested a specific multi-step workflow.",
          },
        ],
      },
      {
        id: "ai-2",
        type: "ai",
        content: "Final answer after planning.",
      },
    ];

    render(<App />);

    expect(screen.getByText("Agent plan")).toBeTruthy();
    expect(screen.getByText("SESSION INTENT")).toBeTruthy();
    expect(screen.getByText("Final answer after planning.")).toBeTruthy();
  });

  it("renders substantive mixed ai content as a normal assistant answer", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Multiply 6 and 7." },
      {
        id: "ai-1",
        type: "ai",
        content:
          "- **Calculation:** 6 multiplied by 7.\n- **Expected result:** 42.",
        tool_calls: [
          {
            id: "call-1",
            name: "calculator_multiply",
            args: { a: 6, b: 7 },
          },
        ],
      },
      {
        id: "tool-1",
        type: "tool",
        tool_call_id: "call-1",
        content: "42",
        status: "success",
      },
    ];

    render(<App />);

    expect(screen.queryByText("Agent plan")).toBeNull();
    expect(screen.getByText("Calculation:")).toBeTruthy();
    expect(screen.getByText("mcp/calculator_multiply")).toBeTruthy();
    expect(screen.getByText("42")).toBeTruthy();
  });

  it("keeps a final answer with summary headings visible as assistant prose", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Summarize the completed calculation." },
      {
        id: "ai-1",
        type: "ai",
        content:
          "## Summary\nThe calculator returned 42.\n\n## Next Steps\nUse the result in the report.",
      },
    ];

    render(<App />);

    expect(screen.queryByText("Agent plan")).toBeNull();
    expect(screen.getByRole("heading", { name: "Summary" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Next Steps" })).toBeTruthy();
    expect(screen.getByText("The calculator returned 42.")).toBeTruthy();
  });

  it("renders a successful prefixed MCP tool call from streamed messages", () => {
    streamState.messages = [
      {
        id: "ai-1",
        type: "ai",
        content: "",
        tool_calls: [{ id: "call-1", name: "calculator_add", args: { a: 2, b: 3 } }],
      },
      {
        id: "tool-1",
        type: "tool",
        tool_call_id: "call-1",
        content: "5",
        status: "success",
      },
    ];

    render(<App />);

    expect(screen.getByText("mcp/calculator_add")).toBeTruthy();
    expect(screen.getByText("success")).toBeTruthy();
    expect(screen.getByText("5")).toBeTruthy();
  });

  it("keeps a failed MCP tool call open and explains which tool failed", () => {
    streamState.messages = [
      {
        id: "ai-1",
        type: "ai",
        content: "",
        tool_calls: [{ id: "call-2", name: "calculator_divide", args: { a: 1, b: 0 } }],
      },
      {
        id: "tool-2",
        type: "tool",
        tool_call_id: "call-2",
        content: "Division by zero",
        status: "error",
      },
    ];

    render(<App />);

    const failedTool = screen.getByText("mcp/calculator_divide").closest("details");
    expect(failedTool?.hasAttribute("open")).toBe(true);
    expect(screen.getByRole("alert").textContent).toContain("Tool calculator_divide failed.");
    expect(screen.getByRole("alert").textContent).toContain("Division by zero");
  });

  it("identifies the agent stream when the stream itself fails", () => {
    streamState.error = new Error("Backend unavailable");

    render(<App />);

    expect(screen.getByRole("alert").textContent).toContain("Agent stream failed:");
    expect(screen.getByRole("alert").textContent).toContain("Backend unavailable");
  });

  it("renders an activity card while the agent is working", () => {
    streamState.isLoading = true;

    render(<App />);

    expect(screen.getByText("Agent is working")).toBeTruthy();
    expect(screen.getByText("Waiting for the next message or MCP tool result.")).toBeTruthy();
  });

  it("writes the created thread id into the URL and shows the session link", () => {
    render(<App />);

    act(() => {
      (capturedStreamOptions?.onThreadId as ((id: string) => void) | undefined)?.("thread-123");
    });

    expect(window.location.search).toBe("?thread=thread-123");
    expect(screen.getByText("Thread link active")).toBeTruthy();
    expect(screen.getByText("Reopen this streamed run later with the current URL.")).toBeTruthy();
    expect(screen.getByText("http://localhost:3000/?thread=thread-123")).toBeTruthy();
  });

  it("skips the todo panel when the backend has not emitted todos yet", () => {
    streamState.values = {};

    render(<App />);

    expect(screen.queryByText("Execution plan")).toBeNull();
    expect(screen.getByText("mcp/calculator_add")).toBeTruthy();
  });
});
{% endraw %}
