# Streaming Output Issues

## Issue 1: Choosing between streaming APIs (v3 vs stream_mode)

- **Symptom**: You see both `agent.stream(stream_mode=...)` and `agent.stream_events(version="v3")` in the docs and don't know which one to use.
- **Cause**: v1.3 introduced **Event Streaming** (`stream_events(version="v3")`), which is completely different from classic `stream(stream_mode=...)` in programming model:
  - Classic API: returns a generator that yields all events in time order, mixed together. The business side dispatches with if/elif based on `mode` / `type`.
  - Event Streaming: returns a **`Stream` object** that organizes events from the same run into multiple **typed projections** — each projection is an independently consumable iterator. The business side "reads whichever attribute holds the data it wants".

  Both share the same underlying LangGraph protocol, but the top-level API shape is completely different — mixing doc examples leads to mismatched output structures.

- **Solution**:
  - **Always use Event Streaming for new projects**. Minimum viable form:
  ```python
  from langchain.agents import create_agent

  def get_weather(city: str) -> str:
      """Get weather for a city."""
      return f"It's always sunny in {city}!"

  agent = create_agent(model="gpt-5-nano", tools=[get_weather])

  stream = agent.stream_events(
      {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
      version="v3",
  )

  for message in stream.messages:
      for delta in message.text:
          print(delta, end="", flush=True)

  final_state = stream.output
  ```

  Key intuition: `stream` is not a generator, it's an **object**. It holds all events from the run and splits them into independent projections by dimension:

  | Projection            | Use                                                                |
  | --------------------- | ------------------------------------------------------------------ |
  | `stream.messages`     | One `ChatModelStream` per LLM call (most commonly used)             |
  | `stream.tool_calls`   | Tool **execution-phase** lifecycle (input, output_deltas, output, error) |
  | `stream.subgraphs`    | Nested sub-agent / subgraph runs (see Issue 2)                      |
  | `stream.values`       | Agent state snapshots                                              |
  | `stream.output`       | Final Agent state (equivalent to `invoke`'s return value)           |
  | `stream.extensions`   | Custom transformer projections                                     |
  | `for event in stream` | Raw protocol events with full envelope (fallback / debug)           |

  - **`stream.messages` — the most commonly used projection**, one `ChatModelStream` per LLM call:
  ```python
  for message in stream.messages:
      print(f"[{message.node}] ", end="")   # the node name where this LLM call sits
      for delta in message.text:            # text delta
          print(delta, end="", flush=True)

      for delta in message.reasoning:       # reasoning delta (only if model has reasoning enabled)
          print(f"[thinking] {delta}", end="", flush=True)

      full_msg = message.output             # the complete AIMessage after the call ends
      if full_msg.usage_metadata:
          print(full_msg.usage_metadata)
  ```

  Key attributes of `ChatModelStream`:

  | Attribute             | Description                                                                       |
  | --------------------- | --------------------------------------------------------------------------------- |
  | `message.text`        | Text deltas; `str(message.text)` waits until end to get full text                   |
  | `message.reasoning`   | Reasoning deltas (only populated when model has reasoning on); same shape as `text` |
  | `message.tool_calls`  | Argument fragments while the model **is producing** a tool_call; `.get()` for the final structured result |
  | `message.output`      | The complete `AIMessage` after this call (with `usage_metadata` / `content_blocks`) |
  | `message.node`        | The graph node name where this call sits (use to distinguish sources across multiple LLM calls within one agent) |

  - **`stream.tool_calls` — tool execution lifecycle**. Note the difference from `message.tool_calls`:
    - `message.tool_calls`: argument fragments while the model is **still saying** "I want to call this tool".
    - `stream.tool_calls`: after the model is done, the process of the tool **actually being executed**, including input, streaming output, final result, and exceptions.

  ```python
  for call in stream.tool_calls:
      print(f"{call.tool_name}({call.input})")
      for delta in call.output_deltas:      # real-time output from streaming tools (e.g. retrieval/long operations)
          print(delta, end="", flush=True)
      print(call.output, call.error)
  ```

  - **Multi-projection concurrent consumption — Event Streaming's biggest convenience**. Multiple projections on the same stream can be consumed independently and in parallel, without writing select/dispatch yourself:
  ```python
  # async: use asyncio.gather to consume multiple projections concurrently
  import asyncio
  stream = await agent.astream_events(input, version="v3")

  async def consume_messages():
      async for message in stream.messages:
          print(await message.text)

  async def consume_tool_calls():
      async for call in stream.tool_calls:
          print(call.tool_name, call.input)

  await asyncio.gather(consume_messages(), consume_tool_calls())

  # sync: use stream.interleave to merge multiple projections into a single iterator in arrival order
  for name, item in stream.interleave("messages", "tool_calls", "values"):
      if name == "messages":
          print(item.text)
      elif name == "tool_calls":
          print(item.tool_name, item.input)
  ```

  - **Channels not covered by typed projections** (looking at the raw envelope, debugging an unexposed event), iterate the raw events directly:
  ```python
  for event in stream:
      print(event["method"], event["params"]["namespace"], event["params"]["data"])
  ```

  - **Legacy projects / strong dependency on Pregel-level capabilities**: keep `stream(stream_mode=...)`. Recommend upgrading to the v2 output format (`langgraph>=1.1`) for unified `StreamPart` dicts:
  ```python
  for chunk in agent.stream(
      {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
      stream_mode=["updates", "custom"],
      version="v2",  # unified StreamPart dict, no longer (mode, data) tuple
  ):
      print(chunk["type"])  # "updates" or "custom"
      print(chunk["data"])
  ```

- **Lessons learned**: The mental model for Event Streaming is "**subscribe to multi-channel streams by data type**", not "consume one generator over time". Once you grasp this, the rest is just looking up projections: chat UI defaults to `stream.messages` + `message.text`; multi-LLM defaults to `stream.subgraphs` + `message.node` (Issue 2); custom events use `get_stream_writer()` + `stream_mode="custom"` (Issue 4). Only fall back to `stream_mode` for legacy code or to leverage Pregel-level capabilities like `get_stream_writer()`.

## Issue 2: How to tell apart tokens from different LLMs when one Agent has multiple LLM calls

- **Symptom**: An Agent may have sub-agents, side LLMs inside middleware (safety review, structured output validation, etc.), or models called from within a tool — beyond the main model. `stream_mode="messages"` pushes all LLM tokens mixed together, leaving no way to tell which model produced a given token.
- **Cause**: `stream_mode="messages"` doesn't distinguish sources by default; in Event Streaming nested calls go through nested namespaces, so you either judge by `message.node` / metadata, or consume `stream.subgraphs` as a separate projection.
- **Solution**:
  - **Explicitly name all agents**: `create_agent(..., name="weather_agent")`. The name enters metadata and is also attached to the generated `AIMessage`.
  - **Event Streaming (recommended)**:
    - Different node LLM calls within the same Agent: distinguish via `message.node`.
    - Nested sub-Agent / Subgraph: consume separately via `stream.subgraphs` + `subagent.graph_name`:
    ```python
    from langchain.chat_models import init_chat_model

    weather_agent = create_agent(
        model=init_chat_model("openai:gpt-5.4"),
        tools=[get_weather],
        name="weather_agent",
    )

    def call_weather(query: str) -> str:
        """Query the weather agent."""
        result = weather_agent.invoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].text

    supervisor = create_agent(
        model=init_chat_model("openai:gpt-5.4"),
        tools=[call_weather],
        name="supervisor",
    )

    stream = supervisor.stream_events(
        {"messages": [{"role": "user", "content": "What's the weather in Boston?"}]},
        version="v3",
    )

    for subagent in stream.subgraphs:
        if subagent.graph_name != "weather_agent":
            continue
        for message in subagent.messages:
            for token in message.text:
                print(token, end="", flush=True)
    ```
  - **Classic mode**: you must pass `subgraphs=True`, and distinguish sources by `metadata["lc_agent_name"]` or `metadata["langgraph_node"]`:
  ```python
  for chunk in agent.stream(input, stream_mode=["messages", "updates"], subgraphs=True, version="v2"):
      if chunk["type"] == "messages":
          token, metadata = chunk["data"]
          agent_name = metadata.get("lc_agent_name")
          node_name = metadata.get("langgraph_node")
          # Use agent_name / node_name to distinguish sources
  ```
- **Lessons learned**: As long as there might be more than one LLM call in an Agent (even if not multi-agent, just a middleware that calls a model), think through how to distinguish token sources up front; always pass `name=` to agents explicitly, otherwise metadata has basically nothing usable.

## Issue 3: How to turn off streaming for certain models

- **Symptom**: In some cases you don't need streaming from certain models, but once `stream_mode` is set to "messages", all of them stream by default.
- **Cause**: Whether to stream depends on the model instance configuration; the Agent layer won't turn it off for you.
- **Solution**:
  - OpenAI and similar support the `streaming` field:
  ```python
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-5.4", streaming=False)
  ```
  - For models that don't support `streaming`, use the generic `disable_streaming=True` from the base class.
- **Lessons learned**: Streaming is a **model-instance-level** switch, not an Agent-level one — different LLM calls within the same Agent can mix streaming/non-streaming. Default intermediate-step models (safety review, structured output validation, sub-Agents) to non-streaming and let only the final user-facing model stream. This significantly reduces event noise and avoids leaking internal pipelines to the client.



## Issue 4: Custom events / in-tool progress reports not arriving

- **Symptom**: You want to push custom info like "download progress", "retrieval hit count", or "domain events" from tools or middleware, but the consumer side never receives them. Or after the code change, invoking the tool standalone errors out.
- **Cause**: The built-in `stream.messages` / `stream.tool_calls` only cover model tokens and the tool lifecycle — **they don't carry out custom data actively written from inside nodes/tools**. To let external consumers see this data, you must explicitly go through the "custom events channel" — i.e. `get_stream_writer()` + `stream_mode="custom"`. Another common side effect: once you call `get_stream_writer()` inside a tool, **that tool can only run in a LangGraph execution context**, and a standalone `invoke` outside the Agent will raise `RuntimeError`.
- **Solution**:
  - **Get the writer inside a node/tool and push custom events**:
  ```python
  from langgraph.config import get_stream_writer

  def get_weather(city: str) -> str:
      writer = get_stream_writer()
      writer(f"Looking up data for city: {city}")
      writer(f"Acquired data for city: {city}")
      return f"It's always sunny in {city}!"
  ```
  - **Consumer side subscribes with `stream_mode="custom"`** (also recommend upgrading to v2 output format for unified `StreamPart` dicts):
  ```python
  for chunk in agent.stream(
      {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
      stream_mode=["messages", "custom"],
      version="v2",
  ):
      if chunk["type"] == "custom":
          print(chunk["data"])
  ```
  - writer accepts any serializable object, not just strings — pass a dict directly to push structured data (e.g. `writer({"event": "progress", "pct": 30})`); consumer parses it from `chunk["data"]` per business convention.
- **Lessons learned**:
  - `stream.messages` / `stream.tool_calls` don't solve "business events" — when you need to actively push custom data, go back to `get_stream_writer()` + `stream_mode="custom"`.
  - Calling `get_stream_writer()` inside a tool "binds" the tool to a LangGraph context. Unit tests must either go through the Agent or add a conditional fallback for the writer (`try/except RuntimeError`). If the tool needs to remain independently testable, prefer keeping progress reporting in a wrapper layer or middleware layer, and have the tool itself just return structured results.
