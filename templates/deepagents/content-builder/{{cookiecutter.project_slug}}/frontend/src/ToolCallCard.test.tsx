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
          args: { description: "Research AI agents" },
          result: null,
          status: "pending",
        }}
        apiUrl="http://localhost:2024"
      />,
    );

    const pendingDetails = screen
      .getByText("Sub-agent: researcher")
      .closest("details");
    expect(pendingDetails?.hasAttribute("open")).toBe(true);

    rerender(
      <ToolCallCard
        card={{
          callId: "call-1",
          name: "task",
          args: { description: "Research AI agents" },
          result: "Done",
          status: "done",
        }}
        apiUrl="http://localhost:2024"
      />,
    );

    const finishedDetails = screen
      .getByText("Sub-agent: researcher")
      .closest("details");
    expect(finishedDetails?.hasAttribute("open")).toBe(false);
  });

  it("renders image card inline when generate_cover completes", () => {
    render(
      <ToolCallCard
        card={{
          callId: "call-2",
          name: "generate_cover",
          args: { prompt: "Test image", slug: "test" },
          result: "Image saved to blogs/test/hero.png",
          status: "done",
        }}
        apiUrl="http://localhost:2024"
      />,
    );

    expect(screen.getByText("Image: generate_cover")).toBeTruthy();
    expect(screen.getByText("Generated image")).toBeTruthy();
    expect(screen.getByText("blogs/test/hero.png")).toBeTruthy();
    const img = screen.getByAltText("Generated: blogs/test/hero.png");
    expect(img.getAttribute("src")).toBe("http://localhost:2024/images/blogs/test/hero.png");
  });

  it("does not render image card for non-image tools", () => {
    render(
      <ToolCallCard
        card={{
          callId: "call-3",
          name: "web_search",
          args: { query: "test" },
          result: "Search results",
          status: "done",
        }}
        apiUrl="http://localhost:2024"
      />,
    );

    expect(screen.getByText("Tool: web_search")).toBeTruthy();
    expect(screen.queryByText("Generated image")).toBeNull();
  });
});
{% endraw %}
