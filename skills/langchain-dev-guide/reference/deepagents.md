# Deep Agents Development Issues

## Issue 1: Model choice has a huge impact on Agent capability

- **Symptom**: With the same Agent code, swapping the model produces wildly different capability — some models handle tool calling fine, others can't complete the task at all.
- **Cause**: Deep Agents have high requirements on the model, which must have stable tool-calling ability. Different models perform very differently across dimensions like File Ops, Retrieval, Tool Use, Memory, Conversation, Summarization (see the Deep Agents eval suite).
- **Solution**:
  - Prefer high-scoring models: `google_genai:gemini-3.5-flash` (Overall 82%), `openai:gpt-5.5` (80%), `anthropic:claude-opus-4-7` (80%)
  - Among open-source models, `GLM-5.1` (via OpenRouter/Fireworks) performs best (89%)
  - Watch for per-dimension weaknesses: even with a high Overall, Conversation and Memory scores tend to be low (most models < 50%); long-conversation scenarios need extra validation
  - Use `init_chat_model` to fine-tune parameters (e.g. `thinking_level`) to improve some models
- **Lessons learned**: Don't pick by brand alone — you must run the eval. Different models from the same provider can vary widely (e.g. `gpt-5.4` Overall only 18%, while `gpt-5.5` hits 80%).

## Issue 2: Hard to pick a filesystem Backend

- **Symptom**: Deep Agents ships 6 filesystem backends (StateBackend, FilesystemBackend, StoreBackend, ContextHubBackend, LocalShellBackend, CompositeBackend), and it's unclear which one fits your scenario.
- **Cause**: Each backend has very different persistence scope, isolation level, and security model, and the docs don't give a clear decision path.
- **Solution**:
  - **Need cross-session persistence** → use `StoreBackend` (with a LangGraph store) or `ContextHubBackend` (LangSmith Hub)
  - **Need to operate on local project files** → use `CompositeBackend` to route: hand the project directory to `FilesystemBackend`, keep internal temporary data in `StateBackend`:
    ```python
    from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend

    backend = CompositeBackend(
        default=StateBackend(),  # Agent internal data (temporary)
        routes={
            "/workspace/": FilesystemBackend(root_dir="/path/to/project", virtual_mode=True),
        },
    )
    ```
  - **Multi-user isolation** → `StoreBackend` must be configured with a `namespace` factory function for data isolation:
    ```python
    from deepagents.backends import StoreBackend

    backend = StoreBackend(
        namespace=lambda rt: (rt.server_info.user.identity,),
    )
    ```
  - **Need to execute shell commands** → use `LocalShellBackend` (development only) or a Sandbox Backend (production). Note: `LocalShellBackend` has no isolation, so the Agent can run arbitrary commands
  - **Security** → `FilesystemBackend` must enable `virtual_mode=True` to block path traversal (`..`, `~`, absolute paths). The default `virtual_mode=False` provides no safety guarantees even with `root_dir` set
- **Lessons learned**: Most scenarios should use `CompositeBackend` to compose routes rather than a single Backend. Using `FilesystemBackend` or `StateBackend` alone each has obvious downsides — the former pollutes disk, the latter doesn't persist.

## Issue 3: How to disable the default general-purpose sub-agent

- **Symptom**: After creating a Deep Agent, even without any configured `subagents`, the Agent still automatically has a sub-agent named `general-purpose` and a corresponding `task` tool. In some scenarios you don't want delegation capability, but can't find the off switch.
- **Cause**: Deep Agents injects a synchronous `general-purpose` sub-agent by default (inheriting the main Agent's tools, skills, and model). As long as at least one synchronous sub-agent exists, `SubAgentMiddleware` is attached and exposes the `task` tool.
- **Solution**:
  - Set `general_purpose_subagent.enabled = False` in the harness profile, while keeping custom sub-agents:
  ```python
  from deepagents import create_deep_agent
  from deepagents.profiles import HarnessProfile, GeneralPurposeSubagentProfile

  profile = HarnessProfile(
      general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
  )

  agent = create_deep_agent(
      model="anthropic:claude-sonnet-4-6",
      tools=[my_tool],
      harness_profile=profile,
      subagents=[research_subagent, code_subagent],  # Custom sub-agents still work
  )
  ```
  - Note: don't try to disable via `excluded_middleware=["SubAgentMiddleware"]` — this raises `ValueError` directly, and would also disable custom sub-agents
- **Lessons learned**: If you only want to replace default behavior rather than fully disable it, pass a custom sub-agent with `name="general-purpose"` to override the default config.

## Issue 4: How to set filesystem permissions

- **Symptom**: The Agent can use built-in filesystem tools to read/write any file. You need to restrict its scope but aren't sure how to configure it. Or you configured permission rules but the Agent can still access paths that should be blocked.
- **Cause**: Permissions are configured via the `permissions` parameter of `create_deep_agent`, not on the Backend. Rules use a **first-match-wins** strategy (matched top to bottom, stop at the first hit), and when no rule matches the default is **allow**. Wrong rule order or missing a catch-all deny rule will silently break permission enforcement.
- **Solution**:
  - **Restrict the Agent to a workspace and protect sensitive files**:
  ```python
  from deepagents import FilesystemPermission, create_deep_agent

  agent = create_deep_agent(
      model=model,
      backend=backend,
      permissions=[
          # First deny sensitive files (specific rules come first)
          FilesystemPermission(
              operations=["read", "write"],
              paths=["/workspace/.env", "/workspace/secrets/**"],
              mode="deny",
          ),
          # Then allow the workspace
          FilesystemPermission(
              operations=["read", "write"],
              paths=["/workspace/**"],
              mode="allow",
          ),
          # Catch-all: deny everything else
          FilesystemPermission(
              operations=["read", "write"],
              paths=["/**"],
              mode="deny",
          ),
      ],
  )
  ```
  - **Read-only Agent (block all writes)**:
  ```python
  agent = create_deep_agent(
      model=model,
      backend=backend,
      permissions=[
          FilesystemPermission(
              operations=["write"],
              paths=["/**"],
              mode="deny",
          ),
      ],
  )
  ```
  - **Sub-agent with different permissions** (sub-agents inherit parent permissions by default; setting `permissions` fully replaces rather than merges):
  ```python
  agent = create_deep_agent(
      model=model,
      backend=backend,
      permissions=[
          FilesystemPermission(operations=["read", "write"], paths=["/workspace/**"], mode="allow"),
          FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="deny"),
      ],
      subagents=[
          {
              "name": "auditor",
              "description": "Read-only code reviewer",
              "system_prompt": "Review the code for issues.",
              "permissions": [
                  # Fully replaces parent permissions: only allow reads in workspace
                  FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
                  FilesystemPermission(operations=["read"], paths=["/workspace/**"], mode="allow"),
                  FilesystemPermission(operations=["read"], paths=["/**"], mode="deny"),
              ],
          }
      ],
  )
  ```
  - **CompositeBackend + sandbox**: when default is sandbox, `paths` must fall under a known route prefix, otherwise `NotImplementedError` is raised:
  ```python
  from deepagents.backends import CompositeBackend

  composite = CompositeBackend(
      default=sandbox,
      routes={"/memories/": memories_backend},
  )

  # Correct: permission path is under a route prefix
  agent = create_deep_agent(
      model=model,
      backend=composite,
      permissions=[
          FilesystemPermission(operations=["write"], paths=["/memories/**"], mode="deny"),
      ],
  )

  # Wrong: /workspace/** hits the sandbox default and raises NotImplementedError
  # FilesystemPermission(operations=["write"], paths=["/workspace/**"], mode="deny")
  ```
  - Note: permissions only affect built-in filesystem tools (`ls`, `read_file`, `glob`, `grep`, `write_file`, `edit_file`). Custom tools and MCP tools are not constrained
- **Lessons learned**: The most common mistake is inverted rule order — putting a broad allow before deny means deny will never trigger. And since the default when no rule matches is allow, missing a catch-all deny is equivalent to having no permission control at all.

## Issue 5: How to configure long-term Agent memory

- **Symptom**: The Agent "forgets" between every conversation and can't remember user preferences or prior context. Or memory is configured, but memory leaks between multiple users.
- **Cause**: Deep Agents' long-term memory is built on the filesystem — the Agent specifies a memory file path via the `memory=` parameter and uses the Backend to control storage location and isolation scope. Without a persistent Backend (like `StoreBackend`), memory exists only in single-session State. If the namespace isn't isolated by user, all users share the same memory file.
- **Solution**:
  - **User-scoped isolated memory** (each user has independent, mutually invisible memory):
  ```python
  from deepagents import create_deep_agent
  from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

  agent = create_deep_agent(
      model="google_genai:gemini-3.5-flash",
      memory=["/memories/preferences.md"],
      backend=CompositeBackend(
          default=StateBackend(),
          routes={
              "/memories/": StoreBackend(
                  namespace=lambda rt: (rt.server_info.user.identity,),
              ),
          },
      ),
  )
  ```
  - **Agent-scoped shared memory** (all users share the same Agent knowledge):
  ```python
  agent = create_deep_agent(
      model="google_genai:gemini-3.5-flash",
      memory=["/memories/AGENTS.md"],
      backend=CompositeBackend(
          default=StateBackend(),
          routes={
              "/memories/": StoreBackend(
                  namespace=lambda rt: (rt.server_info.assistant_id,),
              ),
          },
      ),
  )
  ```
  - **Org-scoped read-only policy** (shared across users but not modifiable by the Agent, to prevent prompt injection from polluting shared state):
  ```python
  from deepagents import FilesystemPermission

  agent = create_deep_agent(
      model="google_genai:gemini-3.5-flash",
      memory=["/memories/preferences.md", "/policies/compliance.md"],
      backend=CompositeBackend(
          default=StateBackend(),
          routes={
              "/memories/": StoreBackend(
                  namespace=lambda rt: (rt.server_info.user.identity,),
              ),
              "/policies/": StoreBackend(
                  namespace=lambda rt: (rt.context.org_id,),
              ),
          },
      ),
      permissions=[
          FilesystemPermission(operations=["write"], paths=["/policies/**"], mode="deny"),
      ],
  )
  ```
- **Lessons learned**: The core design decision for memory is choosing the namespace — it determines "who can see what." User-scoped uses `user.identity`, Agent-scoped uses `assistant_id`, org-scoped uses `org_id`. Shared memory must be read-only, otherwise there's a cross-user prompt-injection risk.
