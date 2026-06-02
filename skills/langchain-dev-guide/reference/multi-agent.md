# Multi-Agent Orchestration Issues

## Issue 1: Choosing between subagents and handoffs

- **Symptom**: When building multi-agent systems, you see both the "subagent as tool" pattern and the `Command(goto=..., graph=Command.PARENT)` "handoff" pattern in the docs and don't know which to choose. Picking wrong leads to: the main agent can't get the sub-agent's output, or the sub-agent can't talk to the user directly.
- **Cause**: The two patterns solve completely different orchestration needs:
  - **Subagents (recommended default)**: a central supervisor treats sub-agents as **tool calls** — the main agent decides when to call, what query to send, and how to use the return value. Sub-agents **don't talk to the user directly**; each call starts from a clean context, and the result returns to the main agent.
  - **Handoffs**: a tool updates a state variable (e.g. `current_step` / `active_agent`), based on which the system switches "the currently active agent / config". The agent switched-to **directly takes over the conversation with the user**, with state persisting across turns.
- **Solution**: Use this decision table:

  | Need                                                          | Pick                  |
  | ------------------------------------------------------------- | --------------------- |
  | Main agent needs the sub-agent's result to decide next step    | Subagents (sync call) |
  | Sub-agent needs to run a task in a clean context, avoid polluting the main conversation | Subagents (context isolation) |
  | Multiple domains (calendar / email / CRM…) need centralized routing | Subagents             |
  | Customer service flow: first collect warranty id, then refund — must unlock in order | Handoffs              |
  | Different stages need different system prompts / tool sets, and need to interact with user directly | Handoffs              |
  | sales ↔ support transfer between each other, each agent talks to the user | Handoffs              |

- **Lessons learned**: Default to subagents — its semantics are simplest (just a tool call), and it has the fewest failure modes. **Only when an agent needs to converse with the user across multiple turns directly** (instead of returning results to the upper layer) should you use handoffs. The two can be mixed: the supervisor uses subagents to manage multiple sub-agents, and one sub-agent internally uses handoffs for multi-stage flow.

## Issue 2: tool-per-agent or single dispatch tool in subagent mode

- **Symptom**: Subagent mode has two ways to expose: "wrap each sub-agent as a separate tool" vs. "write a general `task(agent_name, description)` tool that routes by name to a sub-agent in the registry". You don't know which to choose, or you started with tool-per-agent and later found adding a new agent requires heavy changes to the supervisor.
- **Cause**: The two are inverse in "customizability" vs "extensibility":
  - **Tool per agent**: each sub-agent is wrapped as its own `@tool`, allowing per-sub-agent control over input/output/state passing. The cost: every new agent requires modifying the supervisor's `tools=[...]`.
  - **Single dispatch tool**: only one `task(agent_name, description)` tool; sub-agents are looked up in a registry dict; adding agents only modifies the registry, not the supervisor. The cost: all sub-agents share the same "query passed as user message, last message as return value" convention, no per-agent customization.
- **Solution**:
  - **Tool per agent** (few agents, each needs separate context engineering):
  ```python
  from langchain.tools import tool
  from langchain.agents import create_agent

  research_subagent = create_agent(model="...", tools=[...])

  @tool("research", description="Research a topic and return findings")
  def call_research(query: str) -> str:
      result = research_subagent.invoke({"messages": [{"role": "user", "content": query}]})
      return result["messages"][-1].content

  supervisor = create_agent(model="...", tools=[call_research])
  ```

  - **Single dispatch tool** (many agents, multi-team, prefer convention over configuration):
  ```python
  from langchain.tools import tool
  from langchain.agents import create_agent

  SUBAGENTS = {
      "research": create_agent(model="gpt-5.4", prompt="You are a research specialist..."),
      "writer":   create_agent(model="gpt-5.4", prompt="You are a writing specialist..."),
  }

  @tool
  def task(agent_name: str, description: str) -> str:
      """Launch an ephemeral subagent for a task.

      Available agents:
      - research: Research and fact-finding
      - writer:   Content creation and editing
      """
      agent = SUBAGENTS[agent_name]
      result = agent.invoke({"messages": [{"role": "user", "content": description}]})
      return result["messages"][-1].content

  supervisor = create_agent(
      model="gpt-5.4",
      tools=[task],
      system_prompt="You coordinate specialized sub-agents. Use the task tool to delegate work.",
  )
  ```

  - **Tell the main agent which sub-agents exist under single dispatch**, pick by scale:

  | Registry size / change rate           | Recommended approach                                                  |
  | ------------------------------------- | --------------------------------------------------------------------- |
  | <10, mostly static                    | List agent names + descriptions in the supervisor's system_prompt      |
  | <10, want type safety                 | Constrain `agent_name: AgentName` with an `Enum` as the tool param     |
  | >10, dynamically registered or maintained by multiple teams | Provide a separate `list_agents(query)` tool so the main agent looks them up on demand |

- **Lessons learned**: When unsure, start with tool-per-agent; switch to single dispatch when the agent count exceeds 5 or you clearly need multi-team independent delivery. The "cheap" of single dispatch shows in "no supervisor code changes when adding agents", but you pay with "all agents must share the same behavior contract" — switching too early forces customization to take detours.

## Issue 3: Can't get the sub-agent's internal state, no way to review at interrupt time

- **Symptom**: You want to use `get_state(subgraphs=True)` at the supervisor level to see where the subagent is in its run and what its current state is — but the subagent state is never returned. Or you want the subagent to preserve conversation history across multiple calls (e.g. a long-memory research assistant), but every invoke starts with empty state.
- **Cause**: The subagent is invoked **inside a tool function**, and LangGraph can't statically discover this nested graph at compile time — `get_state(subgraphs=True)` can only find "subgraphs added with `add_node`" or "subgraphs invoked in a node function", but not subagents called inside tools. Separately, the subagent's `checkpointer` parameter controls three persistence modes; without explicit configuration it uses **per-invocation** (`checkpointer=None`, default), which doesn't preserve state across calls — this is what most subagents want, but it can mislead you into thinking "subagents can't use interrupt / can't see state at all".
- **Solution**: First understand the three `checkpointer` modes, then pick by need:

  | Mode             | `checkpointer=` | Cross-call memory | Interrupt within one call | State inspection                            | Parallel calls to the same subagent |
  | --------------- | --------------- | ----------------- | ------------------------- | -------------------------------------------- | ---------------------- |
  | per-invocation  | `None` (default) | ❌               | ✅                         | ⚠️ Only "during the current call/at interrupt" | ✅                       |
  | per-thread      | `True`          | ✅                | ✅                         | ✅                                            | ❌ (namespace conflict)  |
  | stateless       | `False`         | ❌               | ❌                         | ❌                                            | ✅                       |

  In all modes, **the parent graph must be compiled with a checkpointer**, otherwise interrupt / state inspection / per-thread memory all fail to work.

  - **Inspect nested state mid-subagent-run** (works in per-invocation too): the subagent must be "in the middle of a single call" (typical case: triggered `interrupt()` and waiting for resume). Then `graph.get_state(config, subgraphs=True).tasks[0].state` returns the nested state. Once that call ends, in per-invocation mode the state doesn't accumulate, and the next call is fresh.
  - **View the subagent's accumulated full state**: subagent must use `checkpointer=True`, and the parent graph must also have a checkpointer. Then `get_state(subgraphs=True)` returns the subagent state accumulated on that thread.
  - **Let the subagent preserve conversation history across calls** (continuations mode):
  ```python
  from langchain.agents import create_agent
  from langchain.agents.middleware import ToolCallLimitMiddleware
  from langgraph.checkpoint.memory import MemorySaver

  fruit_agent = create_agent(
      model="gpt-5.4-mini",
      tools=[fruit_info],
      prompt="You are a fruit expert. Respond in one sentence.",
      checkpointer=True,                     # per-thread persistence
  )

  @tool
  def ask_fruit_expert(question: str) -> str:
      """Ask the fruit expert. Use for ALL fruit questions."""
      resp = fruit_agent.invoke({"messages": [{"role": "user", "content": question}]})
      return resp["messages"][-1].content

  agent = create_agent(
      model="gpt-5.4-mini",
      tools=[ask_fruit_expert],
      prompt="ALWAYS delegate fruit questions to ask_fruit_expert.",
      middleware=[
          # Must forbid parallel calls, otherwise two calls write to the same namespace → checkpoint conflict
          ToolCallLimitMiddleware(tool_name="ask_fruit_expert", run_limit=1),
      ],
      checkpointer=MemorySaver(),            # Parent graph checkpointer is a hard requirement
  )
  ```
  Pitfall: per-thread subagents **don't support parallel LLM calls to the same tool** — e.g. "ask about apple and banana at the same time" causes the model to concurrently call `ask_fruit_expert` twice, both writing to the same namespace and conflicting. Use `ToolCallLimitMiddleware` to rate-limit, or disable parallel tool calls at the model layer.

  - **Multiple different per-thread subagents coexisting** (both fruit and veggie need memory): each subagent needs to be wrapped in a `StateGraph` with a unique node name, otherwise LangGraph assigns namespaces by "call order", and reordering calls scrambles state:
  ```python
  from langgraph.graph import MessagesState, StateGraph

  def create_sub_agent(model, *, name, **kwargs):
      """Wrap with a unique node name to get a stable namespace."""
      agent = create_agent(model=model, name=name, **kwargs)
      return (
          StateGraph(MessagesState)
          .add_node(name, agent)
          .add_edge("__start__", name)
          .compile()
      )

  fruit_agent  = create_sub_agent("gpt-5.4-mini", name="fruit_agent",  tools=[fruit_info],  prompt="...", checkpointer=True)
  veggie_agent = create_sub_agent("gpt-5.4-mini", name="veggie_agent", tools=[veggie_info], prompt="...", checkpointer=True)
  ```

  - **No checkpoint overhead needed for the subagent** (short tool-style calls, clearly no interrupt needed): use `checkpointer=False` to enter stateless mode. The subagent runs as an ordinary function with no durable execution — if it crashes, it runs again from scratch.

  - **Need to access nested state at the main graph layer for debugging** (not just at interrupt time): change the subagent from "invoked inside a tool" to "called inside a graph". Two options:
    - **Call subgraph inside a node**: use when parent/child schemas differ; write a wrapper in the node function to convert state;
    - **Add subgraph as a node**: use when parent/child share state keys (typical: both use `MessagesState`). Directly `add_node` the compiled subagent — no wrapper needed.

    Both forms are statically recognizable by LangGraph, and `get_state(subgraphs=True)` returns nested state. The cost is giving up the "subagent as tool" natural routing ability — you have to design the graph yourself.

  - **Just want to see what went wrong with the subagent**: enable LangSmith tracing. The subagent's run appears as a nested trace under the main agent's trace, far more intuitive than `get_state`.

- **Lessons learned**:
  - The default per-invocation mode for subagents is the right choice for most scenarios — it supports interrupt, supports state inspection within a single call, and supports parallel calls; it just doesn't have cross-call memory. Treat it as a "side-effect-free pure function".
  - Before upgrading to `checkpointer=True` (per-thread), confirm two things: ① the parent graph has a checkpointer; ② the main agent won't concurrently call the same per-thread subagent (middleware or model config handles this).
  - "Main graph needs nested state" and "subagent as tool" are mutually exclusive — for nested visibility, accept "writing a custom graph"; don't try to invoke in a tool and then expect the supervisor to `get_state(subgraphs=True)`.

## Issue 4: Too much subagent wrapping boilerplate / need per-agent input-output customization

- **Symptom**: Following Issue 2's approach to wrap subagents as tools, every agent has to repeatedly write "`@tool` → `agent.invoke({"messages": [...]})` → `result["messages"][-1].content`". When you need to add input preprocessing to a subagent (passing the main agent context along) or output post-processing (returning structured results back to main agent state), you either write nested lambdas or jam in `Command(update=...)` — repetitive and error-prone.
- **Cause**: LangChain natively only exposes low-level mechanisms like `Command` / `ToolRuntime`, without abstracting "wrap agent as tool" and "intercept input/output" into a separate interface. Every new subagent requires writing the boilerplate from scratch.
- **Solution**: Use `wrap_agent_as_tool` / `wrap_all_agents_as_tool` from the third-party `langchain-dev-utils`, combined with `pre_input_hooks` / `post_output_hooks` for context engineering.

  - **Wrap a single subagent** (replacing the hand-written tool-per-agent boilerplate):
  ```python
  from langchain_dev_utils.agents import wrap_agent_as_tool

  schedule_event = wrap_agent_as_tool(
      calendar_agent,
      tool_name="schedule_event",
      tool_description=(
          "Schedule a calendar event using natural language."
          "Input: natural language calendar scheduling request (e.g. 'meeting with design team next Tuesday 2pm')"
      ),
  )
  manage_email = wrap_agent_as_tool(email_agent, tool_name="manage_email", tool_description="...")

  supervisor = create_agent(model="...", tools=[schedule_event, manage_email])
  ```
  Both `tool_name` and `tool_description` are optional, but **strongly recommended to set explicitly** — the default name is `transfer_to_{agent_name}` and the default description is `This tool transforms input to {agent_name}`. The main agent has almost no useful information to base tool selection on.

  - **Wrap multiple subagents as a single dispatch tool** (replacing the hand-written single dispatch registry):
  ```python
  from langchain_dev_utils.agents import wrap_all_agents_as_tool

  call_subagent = wrap_all_agents_as_tool(
      [calendar_agent, email_agent],
      tool_name="call_subagent",
      tool_description=(
          "Call a sub-agent to execute a task. Available agents: "
          "- calendar_agent: for scheduling calendar events\n"
          "- email_agent: for sending emails"
      ),
  )

  main_agent = create_agent(model="...", tools=[call_subagent])
  ```

  - **Use `pre_input_hooks` to inject context into the subagent** (pass the main agent state / original user message through to the sub-agent):
  ```python
  from langchain.tools import ToolRuntime

  def process_input(request: str, runtime: ToolRuntime) -> str:
      original = next(m for m in runtime.state["messages"] if m.type == "human")
      return (
          "You are helping handle the following user query:\n\n"
          f"{original.text}\n\n"
          "You've been assigned the following sub-task:\n\n"
          f"{request}"
      )

  call_agent = wrap_agent_as_tool(agent, pre_input_hooks=process_input)
  ```
  When the hook returns `str`, it's auto-wrapped as a `HumanMessage` as subagent input; when it returns `dict`, it's used directly as input (for scenarios needing extra state fields). Pass a `(sync_fn, async_fn)` tuple to handle sync/async paths separately.

  - **Use `post_output_hooks` to feed structured results back to the main agent** (replacing hand-written `Command(update=...)`):
  ```python
  import json

  def process_output(request, response, runtime):
      return json.dumps({
          "status": "success",
          "event_id": "evt_123",
          "summary": response["messages"][-1].text,
      })

  call_agent = wrap_agent_as_tool(agent, post_output_hooks=process_output)
  ```
  The hook return value can be a string (used directly as tool result) or a `Command` object (also updates main agent state).

  - **Handle hooks per-subagent-name under `wrap_all_agents_as_tool`**:
  ```python
  from langchain_dev_utils.agents.wrap import get_subagent_name

  def process_input(request: str, runtime: ToolRuntime):
      if get_subagent_name(runtime) == "weather_agent":
          city = runtime.state.get("city", "Unknown city")
          return f"Current city is: {city}. Please complete the task based on the above. " + request
      return request
  ```

- **Lessons learned**: Native `Command + ToolRuntime` are more flexible, but most subagent wrapping just needs "change the name / inject context / wrap return value" — those three things. Use `wrap_agent_as_tool` directly to skip the boilerplate. To preserve single dispatch tool's extensibility (Issue 2), use `wrap_all_agents_as_tool` + `get_subagent_name` for per-name hook handling — much cleaner than maintaining a registry dict with if/elif.

## Issue 5: How to quickly build a handoff-capable multi-Agent system

- **Symptom**: Building multi-agent handoff with 4 agents transferring between each other requires writing 12 `transfer_to_xxx` tools — each repeating "get last_ai_message from state + construct a paired ToolMessage + wrap with `Command(goto=..., graph=Command.PARENT)`". Missing the ToolMessage pairing causes the receiving agent to see an illegal history of "tool_call without tool_response", directly reporting invalid message sequence. If you switch to "single agent + middleware" to dodge message pairing, you have to write `wrap_model_call` to swap prompts and tools based on `active_agent` / `current_step` — still not lightweight.
- **Cause**: Handoffs are essentially a state machine — "switch the currently available prompt / tools based on active_agent". LangChain only provides low-level components like `Command` / `ToolRuntime`; it doesn't abstract "declare which agents exist and who can transfer to whom" into a high-level interface.
- **Solution**: Use `HandoffAgentMiddleware` from the third-party `langchain-dev-utils` for declarative configuration — write each agent's prompt / tools / transfer targets as a dict, and the middleware auto-generates corresponding transfer tools. Message pairing, Command construction, and dynamic prompt/tool switching are all built in.

  ```python
  from langchain.agents import create_agent
  from langchain_dev_utils.agents.middleware import HandoffAgentMiddleware
  from langchain_dev_utils.agents.middleware.handoffs import AgentConfig

  agent_config: dict[str, AgentConfig] = {
      "time_agent": {
          "prompt": "You are a time assistant",
          "tools": [get_current_time],
          "handoffs": ["default_agent"],          # can only hand off back to default
      },
      "weather_agent": {
          "prompt": "You are a weather assistant",
          "tools": [get_current_weather, get_current_city],
          "handoffs": ["default_agent"],
      },
      "code_agent": {
          "model": "openai:gpt-5.4",              # can specify model individually, overriding the fallback model
          "prompt": "You are a code assistant",
          "tools": [run_code],
          "handoffs": ["default_agent"],
      },
      "default_agent": {
          "prompt": "You are an assistant",
          "default": True,                        # globally there must be exactly one default
          "handoffs": "all",                      # can hand off to any agent
      },
  }

  agent = create_agent(
      model="openai:gpt-5.4",                     # fallback model (reused when agents_config doesn't declare model)
      middleware=[HandoffAgentMiddleware(agents_config=agent_config)],
  )
  ```
  When using this middleware, `create_agent`'s own `tools` and `system_prompt` are ignored — all prompts/tools come from `agents_config`.

  - To customize the **description** of the transfer tool (without changing the implementation), pass `custom_handoffs_tool_descriptions`:
  ```python
  HandoffAgentMiddleware(
      agents_config=agent_config,
      custom_handoffs_tool_descriptions={
          "code_agent": "This tool is for handing off to the code assistant for code questions",
          ...
      },
  )
  ```

  - To **fully customize the transfer tool implementation** (e.g. log / audit during handoff), pass `handoffs_tool_overrides`. Custom tools must return `Command`, with `update.messages` containing the tool response and `update.active_agent` pointing to the target agent name:
  ```python
  @tool
  def transfer_to_code_agent(runtime: ToolRuntime) -> Command:
      """This tool helps you hand off to the code assistant"""
      # ... your custom logic (logging, auditing, etc.) ...
      return Command(update={
          "messages": [ToolMessage(content="transfer to code agent", tool_call_id=runtime.tool_call_id)],
          "active_agent": "code_agent",
      })

  HandoffAgentMiddleware(agents_config=agent_config, handoffs_tool_overrides={"code_agent": transfer_to_code_agent})
  ```

- **Lessons learned**: The core mental model for handoffs is "switch prompt + tools by active_agent" — a declarative configuration. Use `HandoffAgentMiddleware` to drop the mental load from "write N transfer tools + handle message pairing" to "fill in a dict". Also, **checkpointer is a hard requirement** — `active_agent` is cross-turn state; without a checkpointer the next conversation restarts from the default agent.
