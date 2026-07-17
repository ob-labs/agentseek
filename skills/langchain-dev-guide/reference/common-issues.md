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

## Issue 2: MCP tool can't access the agent's user_id / API key / current state

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

## Issue 3: Model always outputs `invalid_tool_calls` - tool never actually executes

- **Symptom**: The model is bound with tools and consistently "calls" them, but the tool function never fires. Inspecting the `AIMessage` shows `tool_calls` is empty while `invalid_tool_calls` is populated. The agent loop either silently skips the call or raises a parsing error. The weaker the model (small-parameter open-source, quantized, vLLM-served), the more frequent this becomes.
- **Cause**: When the model generates a tool call, the `arguments` field must be valid JSON conforming to the tool's schema. Weak models often produce malformed JSON — missing quotes, trailing commas, unescaped characters, truncated output, etc. LangChain's tool-call parser **cannot parse** the broken JSON, so instead of placing it in `tool_calls` it moves it to `invalid_tool_calls`. Since the agent executor only processes entries in `tool_calls`, the tool never runs — it looks like the model "called" it but nothing happened.
- **Solution**: Use `ToolCallRepairMiddleware` from `langchain-dev-utils` — it automatically detects entries in `invalid_tool_calls`, attempts to repair the malformed JSON via the `json-repair` library, and promotes successfully repaired calls back to `tool_calls` so the agent can execute them normally.

  ```python
  from langchain_dev_utils.agents.middleware import tool_call_repair

  agent = create_agent(
      model="openai:gpt-5-mini",
      tools=[run_python_code, get_current_time],
      middleware=[tool_call_repair],
  )
  ```

  `tool_call_repair` is a pre-instantiated global instance of `ToolCallRepairMiddleware` — zero configuration needed.

  If you prefer explicit instantiation:

  ```python
  from langchain_dev_utils.agents.middleware import ToolCallRepairMiddleware

  agent = create_agent(
      model="openai:gpt-5-mini",
      tools=[run_python_code, get_current_time],
      middleware=[ToolCallRepairMiddleware()],
  )
  ```

- **Lessons learned**:
  - When a tool "isn't being called", **check `invalid_tool_calls` on the AIMessage first** — the model likely did attempt a call, but the JSON was unparseable.
  - `ToolCallRepairMiddleware` cannot guarantee 100% repair — severely garbled output (e.g. half the JSON is natural language) will still fail. For those cases, consider simplifying the tool schema, splitting complex parameters into multiple smaller tools, or upgrading to a stronger model.
  - This middleware only acts on `invalid_tool_calls` — valid calls pass through untouched with zero overhead.

## Issue 4: How to use placeholders in system prompt that get dynamically replaced at runtime

- **Symptom**: You want the system prompt to include dynamic information — user name, role, current date, conversation context, etc. — that varies per request. Hardcoding these values means creating a new agent for every variation; concatenating strings manually is error-prone and hard to maintain.
- **Cause**: `create_agent` treats `system_prompt` as a static string by default — it does not perform any template interpolation. To get runtime substitution, you need an explicit formatting middleware that resolves placeholders against `state` and `context` before the prompt reaches the model.
- **Solution**: Add the `format_prompt` middleware (f-string style, covers most cases) or `FormatPromptMiddleware(template_format="jinja2")` (for conditionals / loops):

  ```python
  from langchain_dev_utils.agents.middleware import format_prompt
  from langchain.agents import AgentState
  from dataclasses import dataclass

  class AssistantState(AgentState):
      name: str

  @dataclass
  class UserContext:
      user: str

  agent = create_agent(
      model="openai:gpt-5",
      system_prompt="You are {name}, an assistant for {user}.",
      middleware=[format_prompt],
      state_schema=AssistantState,
      context_schema=UserContext,
  )

  # At runtime, {name} is resolved from state, {user} from context
  response = agent.invoke(
      {"messages": [HumanMessage(content="Hello")], "name": "Jarvis"},
      context=UserContext(user="Tony"),
  )
  # Model receives: "You are Jarvis, an assistant for Tony."
  ```

  Variables are resolved in priority order: **`state` first, then `context`** — a `state` field with the same name shadows the `context` field.

  For templates that need conditionals or loops, use Jinja2:

  ```python
  from langchain_dev_utils.agents.middleware import FormatPromptMiddleware
  from dataclasses import dataclass
  from typing import Optional

  @dataclass
  class Context:
      user_role: Optional[str] = None

  jinja2_formatter = FormatPromptMiddleware(template_format="jinja2")

  agent = create_agent(
      model="openai:gpt-5",
      system_prompt=(
          "You are an assistant.\n"
          "{% if user_role == 'VIP' %}Provide premium service.{% endif %}"
      ),
      middleware=[jinja2_formatter],
      context_schema=Context,
  )
  ```

- **Lessons learned**:
  - Template interpolation is **opt-in** via middleware — never assume it happens by default.
  - Use `format_prompt` (global instance, zero config) for simple `{variable}` substitution; only reach for Jinja2 when you need `{% if %}` / `{% for %}`.
  - If a placeholder has no matching field in either `state` or `context`, formatting will raise a `KeyError` — declare all variables in the corresponding schema.
  - Keep `system_prompt` hardcoded by the developer; pass only **data** through `state` / `context`. Never let end-user input become the template itself — this applies regardless of whether formatting middleware is enabled.
