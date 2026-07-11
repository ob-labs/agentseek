{% raw %}
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

type ApprovalInterrupt = {
  id?: string;
  value: {
    kind: string;
    operation: string;
    dataset_id: string;
    document_ids?: string[];
    relative_paths?: string[];
    count: number;
  };
};

const streamState: {
  values: { todos?: Array<{ content: string; status: "completed" | "in_progress" | "pending" }> };
  messages: Array<Record<string, unknown>>;
  isLoading: boolean;
  error: null;
  submit: ReturnType<typeof vi.fn>;
  interrupt?: ApprovalInterrupt;
  interrupts: ApprovalInterrupt[];
} = {
  values: {
    todos: [
      { content: "Plan the report sections", status: "completed" },
      { content: "Research LangGraph 1.0 changes", status: "in_progress" },
      { content: "Write final summary", status: "pending" },
    ],
  },
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
  interrupts: [],
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
  streamState.interrupt = undefined;
  streamState.interrupts = [];
  streamState.submit.mockReset();
  streamState.values = {
    todos: [
      { content: "Plan the report sections", status: "completed" },
      { content: "Research LangGraph 1.0 changes", status: "in_progress" },
      { content: "Write final summary", status: "pending" },
    ],
  };
  streamState.messages = [
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
  ];
});

describe("App", () => {
  it("renders a RAGFlow approval request and resumes cancellation", () => {
    const pendingInterrupt = {
      id: "interrupt-parse",
      value: {
        kind: "ragflow_approval",
        operation: "parse_documents",
        dataset_id: "dataset-1",
        document_ids: ["document-1", "document-2"],
        count: 2,
      },
    };
    streamState.interrupt = pendingInterrupt;
    streamState.interrupts = [pendingInterrupt];

    render(<App />);

    expect(screen.getByText("Approval required")).toBeTruthy();
    expect(screen.getByText("parse_documents")).toBeTruthy();
    expect(screen.getByText("dataset-1")).toBeTruthy();
    expect(screen.getByText("document-1")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(streamState.submit).toHaveBeenCalledWith(null, {
      command: {
        resume: { "interrupt-parse": { approved: false } },
      },
    });
  });

  it("collects an ID-addressed decision for every pending approval", () => {
    const uploadInterrupt = {
      id: "interrupt-upload",
      value: {
        kind: "ragflow_approval",
        operation: "upload_documents",
        dataset_id: "dataset-1",
        relative_paths: ["policy.md"],
        count: 1,
      },
    };
    const parseInterrupt = {
      id: "interrupt-parse",
      value: {
        kind: "ragflow_approval",
        operation: "parse_documents",
        dataset_id: "dataset-1",
        document_ids: ["document-1"],
        count: 1,
      },
    };
    streamState.interrupt = uploadInterrupt;
    streamState.interrupts = [uploadInterrupt, parseInterrupt];

    render(<App />);

    expect(screen.getAllByText("Approval required")).toHaveLength(2);
    const approveButtons = screen.getAllByRole("button", { name: "Approve" });
    fireEvent.click(approveButtons[0]);
    expect(streamState.submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getAllByRole("button", { name: "Cancel" })[1]);
    expect(streamState.submit).toHaveBeenCalledWith(null, {
      command: {
        resume: {
          "interrupt-upload": { approved: true },
          "interrupt-parse": { approved: false },
        },
      },
    });
  });

  it("blocks approval when an interrupt has no resumable ID", () => {
    const missingIdInterrupt = {
      value: {
        kind: "ragflow_approval",
        operation: "upload_documents",
        dataset_id: "dataset-1",
        relative_paths: ["policy.md"],
        count: 1,
      },
    };
    streamState.interrupt = missingIdInterrupt;
    streamState.interrupts = [missingIdInterrupt];

    render(<App />);

    expect(screen.getByText("Cannot resume an approval without an interrupt ID.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cancel" }).hasAttribute("disabled")).toBe(true);
    expect(screen.getByRole("button", { name: "Approve" }).hasAttribute("disabled")).toBe(true);
    expect(streamState.submit).not.toHaveBeenCalled();
  });

  it("shows that a thread URL will be added after the first message", () => {
    render(<App />);

    expect(screen.getByText("Session link ready")).toBeTruthy();
    expect(
      screen.getByText(
        "After the first message, this page adds a thread URL so you can reopen the same conversation later.",
      ),
    ).toBeTruthy();
  });

  it("renders live todo progress from deepagents state", () => {
    render(<App />);

    expect(screen.getByText("Agent plan")).toBeTruthy();
    expect(screen.getByText("1/3 completed")).toBeTruthy();
    expect(screen.getByText("33%")).toBeTruthy();
    expect(screen.getByText("Plan the report sections")).toBeTruthy();
    expect(screen.getByText("Research LangGraph 1.0 changes")).toBeTruthy();
    expect(screen.getByText("Write final summary")).toBeTruthy();
  });

  it("renders sub-agent cards from streamed task tool calls", () => {
    render(<App />);

    expect(screen.getByText("Sub-agent: research-agent")).toBeTruthy();
    expect(screen.getByText("IBM summary")).toBeTruthy();
    expect(screen.getByText("IBM published a LangGraph guide.")).toBeTruthy();
  });

  it("renders planning-shaped mixed ai content as a collapsed AI plan block", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Research IBM" },
      {
        id: "ai-1",
        type: "ai",
        content:
          "## SESSION INTENT\nCompare LangGraph 1.0 and 0.x.\n\n## SUMMARY\nThe user requested a specific multi-step workflow.",
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
    ];

    render(<App />);

    expect(screen.getByText("AI plan")).toBeTruthy();
    expect(screen.getByText("SESSION INTENT")).toBeTruthy();
    expect(screen.getByText("AI plan").closest("details")?.hasAttribute("open")).toBe(false);
    expect(screen.getByText("Sub-agent: research-agent")).toBeTruthy();
    expect(screen.getByText("IBM summary")).toBeTruthy();
  });

  it("renders a standalone planning message as a collapsed AI plan block", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Research IBM" },
      {
        id: "ai-1",
        type: "ai",
        content:
          "## SESSION INTENT\nCompare LangGraph 1.0 and 0.x.\n\n## SUMMARY\nThe user requested a specific multi-step workflow.",
      },
      {
        id: "ai-2",
        type: "ai",
        content: "Final answer after planning.",
      },
    ];

    render(<App />);

    expect(screen.getByText("AI plan")).toBeTruthy();
    expect(screen.getByText("SESSION INTENT")).toBeTruthy();
    expect(screen.getByText("Final answer after planning.")).toBeTruthy();
  });

  it("renders substantive mixed ai content as a normal assistant answer", () => {
    streamState.messages = [
      { id: "human-1", type: "human", content: "Research IBM" },
      {
        id: "ai-1",
        type: "ai",
        content:
          "- **Answer point one:** LangGraph 1.0 adds a functional API.\n- **Answer point two:** LangGraph 1.0 improves deployment tooling.",
        tool_calls: [
          {
            id: "call-1",
            name: "write_todos",
            args: {
              todos: [{ content: "Wrap up", status: "completed" }],
            },
          },
        ],
      },
      {
        id: "tool-1",
        type: "tool",
        tool_call_id: "call-1",
        content: "Updated todo list",
      },
    ];

    render(<App />);

    expect(screen.queryByText("AI plan")).toBeNull();
    expect(screen.getByText("Answer point one:")).toBeTruthy();
    expect(screen.getByText("Tool: write_todos")).toBeTruthy();
    expect(screen.getByText("Updated todo list")).toBeTruthy();
  });

  it("renders an activity card while research is in progress", () => {
    streamState.isLoading = true;

    render(<App />);

    expect(screen.getByText("Knowledge search in progress")).toBeTruthy();
    expect(screen.getByText("Waiting for RAGFlow evidence and final synthesis.")).toBeTruthy();
  });

  it("writes the created thread id into the URL and shows the session link", () => {
    render(<App />);

    act(() => {
      (capturedStreamOptions?.onThreadId as ((id: string) => void) | undefined)?.("thread-123");
    });

    expect(window.location.search).toBe("?thread=thread-123");
    expect(screen.getByText("Session link active")).toBeTruthy();
    expect(screen.getByText("Reopen this conversation later with the current URL.")).toBeTruthy();
    expect(screen.getByText("http://localhost:3000/?thread=thread-123")).toBeTruthy();
  });

  it("skips the todo panel when the backend has not emitted todos yet", () => {
    streamState.values = {};

    render(<App />);

    expect(screen.queryByText("Agent plan")).toBeNull();
    expect(screen.getByText("Sub-agent: research-agent")).toBeTruthy();
  });
});
{% endraw %}
