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
          name: "task",
          args: { description: "Search policies", subagent_type: "knowledge-researcher" },
          result: null,
          status: "pending",
        }}
      />,
    );

    const pendingDetails = screen
      .getByText("Sub-agent: knowledge-researcher")
      .closest("details");
    expect(pendingDetails?.hasAttribute("open")).toBe(true);

    rerender(
      <ToolCallCard
        card={{
          callId: "call-1",
          name: "task",
          args: { description: "Search policies", subagent_type: "knowledge-researcher" },
          result: "Done",
          status: "done",
        }}
      />,
    );

    const finishedDetails = screen
      .getByText("Sub-agent: knowledge-researcher")
      .closest("details");
    expect(finishedDetails?.hasAttribute("open")).toBe(false);
  });
});
{% endraw %}
