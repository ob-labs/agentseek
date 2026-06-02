# Middleware Development Issues

## Issue 1: Middleware execution order is counter-intuitive

- **Symptom**: When multiple middlewares are composed, the actual execution order of `before_model` differs from what you expected, causing state to be unexpectedly overwritten or logic to fail.
- **Cause**: The execution order of the middleware list follows the onion model, with different rules for each of the three hook types:
  - `before_*` hooks: executed in list order (first → last)
  - `after_*` hooks: executed in **reverse** list order (last → first)
  - `wrap_*` hooks: nested wrapping (first wraps all others, innermost executes last)
- **Solution**:
  ```python
  agent = create_agent(
      model="gpt-5.4",
      middleware=[middleware1, middleware2, middleware3],
      tools=[...],
  )
  # Actual execution flow:
  # 1. middleware1.before_model()
  # 2. middleware2.before_model()
  # 3. middleware3.before_model()
  # 4. middleware1.wrap_model_call → middleware2.wrap_model_call → middleware3.wrap_model_call → model
  # 5. middleware3.after_model()  ← note the reverse order!
  # 6. middleware2.after_model()
  # 7. middleware1.after_model()
  ```
  - `before_agent` / `after_agent` follow the same rule: before in order, after in reverse
  - Key principle: things that need to intercept earliest go at the front of the list (rate limiting, permission checks); things that need to be the last fallback also go at the front (since wrap nesting puts them outermost)
- **Lessons learned**: The nesting nature of `wrap_model_call` means the first middleware in the list both sees the request first and the response last. Place retry logic at the front of the list (outermost), logging in the middle or back.

## Issue 2: state_schema merge behavior and input/output control

- **Symptom**: Multiple middlewares each declare a `state_schema`, and it's unclear how the final state is merged. Or some fields are intermediate state you don't want exposed to callers, some need to be input-only and not in output, some appear only in output.
- **Cause**: Internally `create_agent` merges all middleware `state_schema`s in registration order, finally merging the `create_agent`'s `state_schema` parameter (if any). The merge rule is: later declarations override earlier ones for the same field name (base_state is merged last, giving it the highest priority). After merging, `OmitFromSchema` annotations are used to generate the InputSchema and OutputSchema separately.
- **Solution**:
  - **Merge order**: `[middleware1.state_schema, middleware2.state_schema, ..., base_state]`, with later overriding earlier for same-named fields:
  ```python
  from langchain.agents import create_agent
  from langchain.agents.middleware import AgentState, AgentMiddleware
  from typing_extensions import NotRequired

  class MiddlewareAState(AgentState):
      counter: NotRequired[int]

  class MiddlewareBState(AgentState):
      trace_id: NotRequired[str]

  class MyState(AgentState):
      user_id: NotRequired[str]

  # Final merged state = messages + counter + trace_id + user_id
  # If there's a same-named field, MyState (base_state) takes priority
  agent = create_agent(
      model="gpt-5.4",
      middleware=[middleware_a, middleware_b],
      state_schema=MyState,
  )
  ```
  - **Control field input/output visibility** — use the `OmitFromSchema` annotation:
  ```python
  from typing import Annotated
  from langchain.agents.middleware import AgentState, OmitFromSchema
  from typing_extensions import NotRequired

  class MyState(AgentState):
      # Only appears in input, not in output (e.g. config parameters passed by the user)
      user_preference: NotRequired[Annotated[str, OmitFromSchema(output=True)]]

      # Only appears in output, no need for caller to pass in (e.g. result produced by the Agent)
      structured_response: NotRequired[Annotated[dict, OmitFromSchema(input=True)]]

      # Intermediate state: neither in input nor output (pure internal flow)
      internal_step_count: NotRequired[Annotated[int, OmitFromSchema(input=True, output=True)]]

      # Normal field: visible in both input and output
      messages: ...  # inherited from AgentState
  ```
  - **Actual behavior**:
    - `OmitFromSchema(output=True)`: caller passes it in via `invoke({"user_preference": "concise"})`, but the field is not in the returned result
    - `OmitFromSchema(input=True)`: caller doesn't need to pass it; produced during Agent execution, appears in the returned result
    - `OmitFromSchema(input=True, output=True)`: pure intermediate state, middlewares pass data via state, completely invisible to the outside
  - **Same-name field conflicts**: later merged overrides earlier merged. If two middlewares declare a same-named field with different types, no error is raised but behavior is unpredictable. Use field prefixes to avoid this:
  ```python
  class RateLimitState(AgentState):
      ratelimit_count: NotRequired[int]  # prefix isolation

  class AuditState(AgentState):
      audit_last_tool: NotRequired[str]  # prefix isolation
  ```
- **Lessons learned**: `OmitFromSchema` is the key mechanism that distinguishes "external interface" from "internal state". Fields without this annotation are visible in both InputSchema and OutputSchema by default. Counters, flags, and other middleware-produced fields should be marked `OmitFromSchema(input=True, output=True)` to avoid polluting the caller's interface.

## Issue 3: The resume value for the Human-in-the-loop middleware

- **Symptom**: After using `HumanInTheLoopMiddleware` the Agent interrupts successfully, but it's unclear what value to pass on resume; or after passing the value, the Agent behaves unexpectedly (e.g. still executes original args after edit, model doesn't receive feedback after reject).
- **Cause**: After `HumanInTheLoopMiddleware` interrupts, you need to resume execution via `Command(resume=...)`. The resume value has the structure `{"decisions": [...]}` (**plural, array**), where each element uses a `"type"` field to specify the decision type. Common mistakes include using the singular `{"decision": "approve"}` form, or forgetting `version="v2"` and losing access to interrupt info.
- **Solution**:
  - **Configure interrupt rules**: use `interrupt_on` to specify which tools require human approval. Values can be `True` (all decision types allowed), `False` (auto-approve), or an `InterruptOnConfig` object:
  ```python
  from langchain.agents import create_agent
  from langchain.agents.middleware import HumanInTheLoopMiddleware
  from langgraph.checkpoint.memory import InMemorySaver

  agent = create_agent(
      model="gpt-5.4",
      tools=[read_email_tool, send_email_tool, ask_user_tool],
      checkpointer=InMemorySaver(),  # checkpointer is required
      middleware=[
          HumanInTheLoopMiddleware(
              interrupt_on={
                  "send_email_tool": True,  # allow all decision types (approve/edit/reject/respond)
                  "ask_user_tool": {"allowed_decisions": ["respond"]},  # only allow respond
                  "read_email_tool": False,  # safe operation, no interrupt
              },
              description_prefix="Tool execution pending approval",
          ),
      ],
  )
  ```
  - **Get interrupt info**: invoke with `version="v2"`. The returned `GraphOutput` contains a `.interrupts` attribute with `action_requests` (details of pending tool calls) and `review_configs` (allowed decision types per tool):
  ```python
  config = {"configurable": {"thread_id": "thread-1"}}

  result = agent.invoke(
      {"messages": [{"role": "user", "content": "Send the report to the team"}]},
      config=config,
      version="v2",  # must specify v2 to access interrupts
  )

  # result.interrupts contains interrupt details
  # Interrupt(value={
  #     'action_requests': [
  #         {'name': 'send_email_tool', 'arguments': {...}, 'description': '...'}
  #     ],
  #     'review_configs': [
  #         {'action_name': 'send_email_tool', 'allowed_decisions': ['approve', 'edit', 'reject', 'respond']}
  #     ]
  # })
  ```
  - **Resume value format** (four decision types):
  ```python
  from langgraph.types import Command

  # approve: approve directly, execute the original tool call
  agent.invoke(
      Command(resume={"decisions": [{"type": "approve"}]}),
      config=config,
      version="v2",
  )

  # reject: reject execution; message becomes feedback to help the model re-plan
  agent.invoke(
      Command(resume={"decisions": [
          {"type": "reject", "message": "Don't delete data; archive to the history table instead"}
      ]}),
      config=config,
      version="v2",
  )

  # edit: modify tool call args before executing (use edited_action to specify new tool name and args)
  agent.invoke(
      Command(resume={"decisions": [
          {
              "type": "edit",
              "edited_action": {
                  "name": "send_email_tool",  # usually same as the original tool
                  "args": {"recipient": "boss@company.com", "subject": "Updated subject"},
              },
          }
      ]}),
      config=config,
      version="v2",
  )

  # respond: skip tool execution; human reply becomes the tool result directly (for ask_user-type tools)
  agent.invoke(
      Command(resume={"decisions": [{"type": "respond", "message": "Use a blue theme"}]}),
      config=config,
      version="v2",
  )
  ```
  - **Multiple tool calls interrupted simultaneously**: when the model returns multiple tool_calls needing approval in one go, the order in the decisions array must correspond one-to-one with the order in `action_requests`:
  ```python
  agent.invoke(
      Command(resume={"decisions": [
          {"type": "approve"},                            # first tool: approve
          {"type": "reject", "message": "Not allowed"},   # second tool: reject
      ]}),
      config=config,
      version="v2",
  )
  ```
  - **Checkpointer is required**: without a checkpointer, state can't be restored after interrupt. `InMemorySaver` is for development; production uses persistent storage like `AsyncPostgresSaver`
- **Lessons learned**: The most common mistake is getting the resume structure wrong — remember it's `{"decisions": [{"type": "..."}]}` (plural + array + type field), not `{"decision": "..."}`. The `edit` args go in `edited_action`, not at the top level. `respond` fits "ask user"-style tools: the human reply becomes a ToolMessage returned to the model, and the tool itself doesn't execute.

## Issue 4: Dynamically modifying state inside wrap_model_call

- **Symptom**: You need to update state in `wrap_model_call` based on the model response (e.g. record token usage, trigger summarization), but returning `ModelResponse` directly can't carry state updates.
- **Cause**: The return type of `wrap_model_call` is `ModelResponse` (i.e. the model's AIMessage) by default. Unlike node-style hooks, you can't directly return a dict that merges into state. To inject state updates from the wrap layer, you need to return `ExtendedModelResponse`.
- **Solution**:
  ```python
  from typing import Callable
  from langchain.agents.middleware import (
      wrap_model_call,
      AgentState,
      ModelRequest,
      ModelResponse,
      ExtendedModelResponse,
  )
  from langgraph.types import Command
  from typing_extensions import NotRequired

  class UsageState(AgentState):
      last_model_tokens: NotRequired[int]

  @wrap_model_call(state_schema=UsageState)
  def track_usage(
      request: ModelRequest,
      handler: Callable[[ModelRequest], ModelResponse],
  ) -> ExtendedModelResponse:
      response = handler(request)
      # Inject state updates via Command(update=...)
      return ExtendedModelResponse(
          model_response=response,
          command=Command(update={"last_model_tokens": 150}),
      )
  ```
  - **Command composition rules across multiple middlewares**:
    - Commands are applied via graph reducers — the messages field is append-style
    - Non-reducer fields (regular int/str): inner is applied first, outer last, **outer overrides inner**
    - If the outer layer has retry logic (calling `handler()` multiple times), commands from earlier calls are discarded
  - **Dynamically modify the system prompt** (the most common use of wrap_model_call):
  ```python
  from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
  from langchain.messages import SystemMessage
  from typing import Callable

  @wrap_model_call
  def inject_context(
      request: ModelRequest,
      handler: Callable[[ModelRequest], ModelResponse],
  ) -> ModelResponse:
      # request.system_message is always a SystemMessage object
      new_content = list(request.system_message.content_blocks) + [
          {"type": "text", "text": "Current user preference: concise answers"}
      ]
      return handler(request.override(system_message=SystemMessage(content=new_content)))
  ```
  - **Dynamically switch models**:
  ```python
  from langchain.chat_models import init_chat_model

  complex_model = init_chat_model("claude-sonnet-4-6")
  simple_model = init_chat_model("claude-haiku-4-5-20251001")

  @wrap_model_call
  def dynamic_model(
      request: ModelRequest,
      handler: Callable[[ModelRequest], ModelResponse],
  ) -> ModelResponse:
      model = complex_model if len(request.messages) > 10 else simple_model
      return handler(request.override(model=model))
  ```
  - **Dynamically filter tools**:
  ```python
  @wrap_model_call
  def filter_tools(
      request: ModelRequest,
      handler: Callable[[ModelRequest], ModelResponse],
  ) -> ModelResponse:
      relevant = [t for t in request.tools if t.name in ["search", "calculator"]]
      return handler(request.override(tools=relevant))
  ```
- **Lessons learned**: `request.override()` is the most important API in wrap_model_call — it can modify `system_message`, `model`, `tools`, `messages`. Use `ExtendedModelResponse + Command` when you need to modify state; use `request.override()` when you only need to modify request parameters. The two can be combined.
