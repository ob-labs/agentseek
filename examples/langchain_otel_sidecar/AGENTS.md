# LangChain OTEL Sidecar Instructions

- When the user asks to inspect the demo runtime, use the `mcp.otel_*` tools first.
- Prefer `mcp.otel_list_services`, `mcp.otel_search_traces`, `mcp.otel_get_trace`, `mcp.otel_find_errors`, and `mcp.otel_get_llm_usage`.
- Focus on latency, tool usage, model usage, token usage, and failure patterns.
- If traces are missing, explain which service name, backend URL, or time range should be checked next.
