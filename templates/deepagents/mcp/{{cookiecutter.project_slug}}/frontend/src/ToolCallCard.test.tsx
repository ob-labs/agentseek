{% raw %}
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import ToolCallCard from "./ToolCallCard";

afterEach(() => {
  cleanup();
});

describe("ToolCallCard", () => {
  it("auto-collapses when a pending call finishes", () => {
    const { rerender } = render(
      <ToolCallCard
        card={{
          callId: "call-1",
          name: "calculator_add",
          args: { a: 19, b: 23 },
          result: null,
          status: "pending",
        }}
      />,
    );

    const pendingDetails = screen.getByText("mcp/calculator_add").closest("details");
    expect(pendingDetails?.hasAttribute("open")).toBe(true);

    rerender(
      <ToolCallCard
        card={{
          callId: "call-1",
          name: "calculator_add",
          args: { a: 19, b: 23 },
          result: "42",
          status: "done",
        }}
      />,
    );

    const finishedDetails = screen.getByText("mcp/calculator_add").closest("details");
    expect(finishedDetails?.hasAttribute("open")).toBe(false);
  });

  it("keeps an error open and names the failed prefixed MCP tool", () => {
    render(
      <ToolCallCard
        card={{
          callId: "call-2",
          name: "calculator_divide",
          args: { a: 1, b: 0 },
          result: "Division by zero",
          status: "error",
        }}
      />,
    );

    const failedDetails = screen.getByText("mcp/calculator_divide").closest("details");
    expect(failedDetails?.hasAttribute("open")).toBe(true);
    expect(screen.getByText("error")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Tool calculator_divide failed.");
    expect(screen.getByRole("alert").textContent).toContain("Division by zero");
  });
});
{% endraw %}
