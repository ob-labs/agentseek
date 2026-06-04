{% raw %}
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const streamState: {
  values: { todos?: Array<{ content: string; status: "completed" | "in_progress" | "pending" }> };
  messages: Array<Record<string, unknown>>;
  isLoading: boolean;
  error: null;
  submit: ReturnType<typeof vi.fn>;
} = {
  values: {
    todos: [
      { content: "Research AI agents topic", status: "completed" },
      { content: "Write blog post", status: "in_progress" },
      { content: "Generate cover image", status: "pending" },
    ],
  },
  messages: [
    { id: "human-1", type: "human", content: "Write a blog post about AI agents" },
    {
      id: "ai-1",
      type: "ai",
      content: "",
      tool_calls: [
        {
          id: "call-1",
          name: "task",
          args: {
            description: "Research AI agents. Save to research/ai-agents.md",
            subagent_type: "researcher",
          },
        },
      ],
    },
    {
      id: "tool-1",
      type: "tool",
      tool_call_id: "call-1",
      content: "Research findings saved",
    },
    {
      id: "ai-2",
      type: "ai",
      content: "",
      tool_calls: [
        {
          id: "call-2",
          name: "generate_cover",
          args: {
            prompt: "Isometric 3D illustration of AI agents",
            slug: "ai-agents",
          },
        },
      ],
    },
    {
      id: "tool-2",
      type: "tool",
      tool_call_id: "call-2",
      content: "Image saved to blogs/ai-agents/hero.png",
    },
    {
      id: "ai-3",
      type: "ai",
      content: "Your blog post about AI agents has been created.",
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
  streamState.values = {
    todos: [
      { content: "Research AI agents topic", status: "completed" },
      { content: "Write blog post", status: "in_progress" },
      { content: "Generate cover image", status: "pending" },
    ],
  };
  streamState.messages = [
    { id: "human-1", type: "human", content: "Write a blog post about AI agents" },
    {
      id: "ai-1",
      type: "ai",
      content: "",
      tool_calls: [
        {
          id: "call-1",
          name: "task",
          args: {
            description: "Research AI agents. Save to research/ai-agents.md",
            subagent_type: "researcher",
          },
        },
      ],
    },
    {
      id: "tool-1",
      type: "tool",
      tool_call_id: "call-1",
      content: "Research findings saved",
    },
    {
      id: "ai-2",
      type: "ai",
      content: "",
      tool_calls: [
        {
          id: "call-2",
          name: "generate_cover",
          args: {
            prompt: "Isometric 3D illustration of AI agents",
            slug: "ai-agents",
          },
        },
      ],
    },
    {
      id: "tool-2",
      type: "tool",
      tool_call_id: "call-2",
      content: "Image saved to blogs/ai-agents/hero.png",
    },
    {
      id: "ai-3",
      type: "ai",
      content: "Your blog post about AI agents has been created.",
    },
  ];
});

describe("App", () => {
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

    expect(screen.getByText("Content plan")).toBeTruthy();
    expect(screen.getByText("1/3 completed")).toBeTruthy();
    expect(screen.getByText("33%")).toBeTruthy();
    expect(screen.getByText("Research AI agents topic")).toBeTruthy();
    expect(screen.getByText("Write blog post")).toBeTruthy();
    expect(screen.getByText("Generate cover image")).toBeTruthy();
  });

  it("renders sub-agent cards from streamed task tool calls", () => {
    render(<App />);

    expect(screen.getByText("Sub-agent: researcher")).toBeTruthy();
    expect(screen.getByText("Research findings saved")).toBeTruthy();
  });

  it("renders image tool cards with image label", () => {
    render(<App />);

    expect(screen.getByText("Image: generate_cover")).toBeTruthy();
  });

  it("displays generated images inline after image tool completes", () => {
    render(<App />);

    expect(screen.getByText("Generated image")).toBeTruthy();
    expect(screen.getByText("blogs/ai-agents/hero.png")).toBeTruthy();
    const img = screen.getByAltText("Generated: blogs/ai-agents/hero.png");
    expect(img).toBeTruthy();
  });

  it("renders an activity card while content generation is in progress", () => {
    streamState.isLoading = true;

    render(<App />);

    expect(screen.getByText("Content generation in progress")).toBeTruthy();
  });

  it("writes the created thread id into the URL and shows the session link", () => {
    render(<App />);

    act(() => {
      (capturedStreamOptions?.onThreadId as ((id: string) => void) | undefined)?.("thread-456");
    });

    expect(window.location.search).toBe("?thread=thread-456");
    expect(screen.getByText("Session link active")).toBeTruthy();
    expect(screen.getByText("Reopen this conversation later with the current URL.")).toBeTruthy();
    expect(screen.getByText("http://localhost:3000/?thread=thread-456")).toBeTruthy();
  });

  it("skips the todo panel when the backend has not emitted todos yet", () => {
    streamState.values = {};

    render(<App />);

    expect(screen.queryByText("Content plan")).toBeNull();
    expect(screen.getByText("Sub-agent: researcher")).toBeTruthy();
  });
});
{% endraw %}
