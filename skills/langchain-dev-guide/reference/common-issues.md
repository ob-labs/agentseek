# Other Common Development Issues

A collection of standalone but high-frequency issues that span multiple categories or sit at the basic engineering layer.

## Issue 1: A tool needs to return extra data on top of the model-facing result

- **Symptom**: A tool needs to return both "text for the model to read" and "extra data for the application side to consume" — e.g. a retrieval tool needs to return a passage (for the model) and the source document ID + page number (for the frontend to highlight); an order lookup needs to return an order summary (for the model) and the full order object (for the next tool / main agent state). Concatenating everything into one string lets the model get distracted by irrelevant fields; returning only text loses the structured data.
- **Cause**: A tool's return value has three different semantics; mixing them causes problems:
  - For the **model** to see: must fit into `ToolMessage.content`; the model uses this to decide next steps.
  - For the **application layer / downstream business code** to see, but **not** into the LLM context: e.g. document ID, raw payload, render hints.
  - For writing back to **agent state**, to be read by subsequent tools / middleware: e.g. `customer_id`, `last_order`, `current_step`.

  These three categories should go through three different channels; jamming them into one string both adds noise for the model and loses structured data for the application.
- **Solution**: Choose the return style by data destination (three styles can be mixed):

  - **Model-only → return string or dict directly**: dicts get serialized into `ToolMessage.content`, and the model reads the fields itself.
  ```python
  from langchain.tools import tool

  @tool
  def get_weather_data(city: str) -> dict:
      """Get structured weather for a city."""
      return {"city": city, "temperature_c": 22, "conditions": "sunny"}
  ```

  - **One for the model + metadata for the app layer (not into LLM) → `ToolMessage(artifact=...)`**: `content` enters the model context, `artifact` doesn't enter the model but stays on the `ToolMessage` for downstream consumption (typical scenario: retrieval tool returning passage + document ID).
  ```python
  from langchain.messages import ToolMessage
  from langchain.tools import ToolRuntime, tool

  @tool
  def search_books(query: str, runtime: ToolRuntime) -> ToolMessage:
      """Retrieve a passage and attach source metadata."""
      passage = "It was the best of times, it was the worst of times."
      return ToolMessage(
          content=passage,                                  # enters model context
          tool_call_id=runtime.tool_call_id,
          name="search_books",
          artifact={"document_id": "doc_123", "page": 0},   # readable to app layer, not into LLM
      )
  ```
  Application code later reads structured data from `message.artifact`; the model sees only the `content` text.

  - **Write data back to agent state for subsequent tool / middleware / main agent reuse → return `Command(update=...)`**: in the update, place both business fields and a `ToolMessage` (must contain a ToolMessage paired with `tool_call_id`, otherwise the next LLM call will fail with invalid message sequence because "tool_call has no tool_response").
  ```python
  from langchain.messages import ToolMessage
  from langchain.tools import ToolRuntime, tool
  from langgraph.types import Command

  @tool
  def lookup_customer(customer_id: str, runtime: ToolRuntime) -> Command:
      """Look up customer and write profile into agent state."""
      profile = fetch_customer(customer_id)              # {"name": ..., "tier": ..., ...}
      return Command(update={
          "customer_profile": profile,                   # written into state, readable by subsequent tools
          "messages": [ToolMessage(
              content=f"Found customer {profile['name']} (tier: {profile['tier']})",
              tool_call_id=runtime.tool_call_id,         # required to pair with tool_call
          )],
      })
  ```
  State fields must first be declared in `state_schema` (or via an `AgentState` subclass), otherwise updates are ignored.

- **Lessons learned**:
  - Default to "return string/dict" — covers 80% of scenarios.
  - For fields the **application layer wants but would be noise in the LLM context** (document ID, raw payload, render metadata), use `ToolMessage(artifact=...)`.
  - For "cross-tool / cross-turn reusable business data" (user profile, looked-up order, current stage), use `Command(update=...)` — remember the paired `ToolMessage`, and declare fields in state schema first.
  - The three styles aren't mutually exclusive: a tool can simultaneously do `Command(update={"customer_profile": ..., "messages": [ToolMessage(content=..., artifact=...)]})`, using all three channels at once.

## Issue 2: Unstable structured output, often returns None

- **Symptom**: Using `model.with_structured_output(schema)` or `create_agent(response_format=schema)` to get structured results occasionally returns `None`, an empty object, or missing fields. Same prompt run multiple times — sometimes good, sometimes bad. The weaker the model (small-parameter, open source, quantized), the worse it gets.
- **Cause**: `with_structured_output` has three underlying implementations (the method parameter). By default most models go through **`function_calling`** — essentially "bind a schema-shaped tool to the model and have the model output structured data via a tool_call". But after binding, the model **has freedom to choose whether to call the tool**, and weak models often just respond in natural language, producing no tool_call → the parsing stage can't get structured results and returns `None`.
- **Solution**: Upgrade tier by tier in this order (drop to the next tier when the previous doesn't work):

  - **First choice: enable the provider's native `json_schema`** — the provider enforces schema conformance at the decoding layer (OpenAI structured outputs, Gemini structured output all belong to this category) — the most reliable approach:
  ```python
  structured_model = model.with_structured_output(MySchema, method="json_schema")
  ```
  Which models support `json_schema` depends on the provider's integration docs; unsupported ones error out directly — fall back to the next two tiers.

  - **Second choice: keep using `function_calling`, but force the schema tool to be called** — `with_structured_output` defaults to `function_calling`; the problem is the model might not call. Manually `bind_tools(tool_choice=...)` to change tool calling from "free" to "forced":
  ```python
  # Option A: must call any of the bound tools
  model_with_tools = model.bind_tools([schema_tool], tool_choice="any")
  # Option B: must call this specific tool
  model_with_tools = model.bind_tools([schema_tool], tool_choice="schema_tool_name")
  ```
  This forces the model to return in tool_call form, avoiding the "free choice not to call" failure mode.

  - **Last resort: `json_mode` + prompt-level constraints** — when the provider supports neither `json_schema` nor stable force-tool-call, fall back to `json_mode`: it only guarantees "the output is valid JSON". **Field names, types, and constraints from the schema must be spelled out in the prompt**, and you should use Pydantic / JSON Schema for validation on the Python side as a safety net.
  ```python
  structured_model = model.with_structured_output(MySchema, method="json_mode")
  # The prompt must clearly tell the model each field's name, type, whether required, value range
  ```

- **Lessons learned**:
  - When structured output is missing, **suspect the model isn't calling the tool first** — not a schema error. `include_raw=True` returns both the raw `AIMessage` and the parsed object; check whether the raw message has a tool_call to locate the issue.
  - Reliability ranking of the three tiers from high to low: `json_schema` > `function_calling + tool_choice` > `json_mode + prompt`. Try the most reliable first in development; only fall back when the provider doesn't support it.
  - Weak model + complex schema is the most failure-prone combination — split the schema into multiple smaller schemas across multiple calls if possible, rather than forcing the model to output a large object in one go.

## Issue 3: MCP tool can't access the agent's user_id / API key / current state

- **Symptom**: You wire an MCP server in as a regular LangChain tool and want to read `runtime.context.user_id`, current agent state, or user preferences from `store` inside the tool — only to find the MCP tool can't access any of these and is limited to the args declared in the schema. Adding `user_id` directly to the tool schema makes the model fabricate one for every call, polluting context and being insecure.
- **Cause**: MCP servers run in a **separate process** (stdio subprocess or remote HTTP service), **completely process-isolated** from the LangGraph runtime — they can't see store, context, state, or tool_call_id. Importing LangGraph runtime APIs on the MCP server side is pointless because it's not running in that process.
- **Solution**: Bridge on the **client side** with `tool_interceptors` — interceptors run in the LangGraph process and can access the full `ToolRuntime`, injecting the needed fields into `args` / `headers` before forwarding to the MCP server.
  ```python
  from langchain_mcp_adapters.client import MultiServerMCPClient
  from langchain_mcp_adapters.interceptors import MCPToolCallRequest

  async def inject_user_context(request: MCPToolCallRequest, handler):
      runtime = request.runtime
      # 1) Business fields (user_id, tenant_id) injected into args; model can't see them and doesn't need them in schema
      args = {**request.args, "user_id": runtime.context.user_id}
      # 2) Auth / tracing info injected into headers, doesn't pollute schema at all
      headers = {"Authorization": f"Bearer {runtime.context.api_key}"}
      return await handler(request.override(args=args, headers=headers))

  client = MultiServerMCPClient({...}, tool_interceptors=[inject_user_context])
  ```
  For auth "short-circuit" scenarios, directly `return ToolMessage(...)` without calling `handler` — e.g. denying sensitive tool calls when unauthenticated:
  ```python
  from langchain.messages import ToolMessage

  async def require_auth(request: MCPToolCallRequest, handler):
      if request.name in {"delete_file", "export_data"} and not request.runtime.state.get("authenticated"):
          return ToolMessage(
              content="Authentication required.",
              tool_call_id=request.runtime.tool_call_id,
          )
      return await handler(request)
  ```
- **Lessons learned**:
  - **Business fields (user_id, tenant_id) → modify `args`**: interceptor injects them centrally; not in schema, so the model won't fabricate them.
  - **Auth / tracing info → modify `headers`**: not in schema at all, the cleanest.
  - **`structuredContent` returned by MCP server is invisible to the model by default** (placed only in `ToolMessage.artifact`) — to let the model read it, use the interceptor to serialize `structuredContent` and concatenate it back to `result.content`.
  - Multiple interceptors follow **onion order**: `[outer, inner]` → outer enters first / exits last. When composing "auth + rate limit + retry", put the outer concern in front, inner (closest to the tool call) in back.
  - `MultiServerMCPClient` is **stateless by default** — a new session opens for every tool call. When you need to reuse context across calls (e.g. server-side login state), use `async with client.session("server_name") as session:` to explicitly manage the lifecycle.