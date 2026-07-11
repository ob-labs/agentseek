import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

type MockStreamState = {
  messages: unknown[];
  values: Record<string, unknown>;
  isLoading: boolean;
  error: string | null;
  submit: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
};

const mockStream: MockStreamState = {
  messages: [],
  values: {},
  isLoading: false,
  error: null,
  submit: vi.fn(),
  stop: vi.fn(),
};

vi.mock("@langchain/react", () => ({
  useStream: () => mockStream,
}));

import App from "./App";

afterEach(() => {
  cleanup();
  mockStream.messages = [];
  mockStream.isLoading = false;
  mockStream.error = null;
});

describe("App", () => {
  it("renders the heading", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toBeDefined();
  });

  it("renders the hint text when no messages", () => {
    render(<App />);
    expect(screen.getByText(/Create a Python hello-world/i)).toBeDefined();
  });

  it("renders a human message", () => {
    mockStream.messages = [
      { id: "h1", type: "human", content: "Run echo hello" },
    ];
    render(<App />);
    expect(screen.getByText("Run echo hello")).toBeDefined();
    expect(screen.getByText("human")).toBeDefined();
  });

  it("renders tool call cards for AI tool calls with matching tool results", () => {
    mockStream.messages = [
      { id: "h1", type: "human", content: "Run echo hello" },
      {
        id: "a1",
        type: "ai",
        content: "",
        tool_calls: [{ id: "tc1", name: "execute", args: { command: "echo hello" } }],
      },
      {
        id: "t1",
        type: "tool",
        content: "hello\n\n[Command succeeded with exit code 0]",
        tool_call_id: "tc1",
      },
      { id: "a2", type: "ai", content: 'The output is "hello".' },
    ];
    render(<App />);
    expect(screen.getByText("Shell: execute")).toBeDefined();
    expect(screen.getByText("done")).toBeDefined();
    expect(screen.getByText(/The output is/)).toBeDefined();
  });

  it("shows activity card when loading", () => {
    mockStream.isLoading = true;
    render(<App />);
    expect(screen.getByText("Sandbox running")).toBeDefined();
  });

  it("hides hint text when messages exist", () => {
    mockStream.messages = [
      { id: "h1", type: "human", content: "Hello" },
    ];
    render(<App />);
    expect(screen.queryByText(/Create a Python hello-world/i)).toBeNull();
  });

  it("shows session link ready before first message", () => {
    render(<App />);
    expect(screen.getByText("Session link ready")).toBeDefined();
  });

  it("shows error message when stream has error", () => {
    mockStream.error = "Connection failed";
    render(<App />);
    expect(screen.getByText("Connection failed")).toBeDefined();
  });
});
