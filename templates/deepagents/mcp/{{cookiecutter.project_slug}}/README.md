# {{ cookiecutter.project_name }}

This AgentSeek project runs a DeepAgents graph with MCP Tools from validated
`stdio` or Streamable HTTP connections. It includes the same local calculator
tools over both transports, a model-free smoke check, and a streamed React UI.

## Run the project for the first time

### Prerequisites

- Python 3.12 or newer with `uv`.
- `uvx`, included with `uv`, for isolated AgentSeek CLI commands.
- Node.js `^20.19.0 || ^22.13.0 || >=24.0.0` with `npm`.
- A model name and credential for OpenAI, Anthropic, or Google when you send chat.

Copy the two environment files:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Edit `.env`. Set `AGENTSEEK_MODEL_PROVIDER`, `AGENTSEEK_MODEL`, and
`AGENTSEEK_MODEL_API_KEY`. Then continue in this exact order:

```bash
uvx agentseek task sync
uvx agentseek task frontend
uvx agentseek task mcp-smoke
uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
```

The smoke task starts or reuses the local Streamable HTTP calculator, discovers
`calculator_add`, `calculator_multiply`, `calculator_http_add`, and
`calculator_http_multiply`, validates both invoked tool schemas, and checks
`37 + 58 = 95` over stdio plus `37 × 58 = 2146` over HTTP. It does not call a
model, and it stops the HTTP server when it started that process itself.
`agentseek info`, `agentseek doctor`, and the dry run inspect the lifecycle before
the last command starts the calculator HTTP server, LangGraph, and Vite.

### Verified workflow

This exact sequence was last verified on 2026-07-30 against a fresh render. The
run produced these checkpoints:

- `task sync` created `.venv` and installed the generated Python package.
- `task frontend` installed the React UI dependencies with no reported
  vulnerabilities.
- `task mcp-smoke` discovered both MCP connections, returned `95` over stdio,
  and returned `2146` over Streamable HTTP.
- `info` identified `deepagents/mcp`, all three services, and all three tasks.
- `doctor` reported every required tool, path, environment value, and process
  working directory as `ok`.
- `dev --dry-run` printed the three process commands and their loopback URLs.
- `dev` started LangGraph, Vite, and the calculator HTTP server. LangGraph
  `/docs`, the Vite root, and calculator `/health` returned HTTP `200`; `Ctrl-C`
  stopped all three processes.

The verification used a placeholder model credential because this sequence does
not send a chat message. It proves setup, lifecycle startup, and both real MCP
transports; it does not prove that a hosted model accepts your credential.

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` after all three
processes start. Sending a message invokes your configured hosted model. The
template's local verification covers lifecycle startup, both MCP transports,
and the calculator; it does not claim a hosted chat was executed without a real
provider key.

Stop `uvx agentseek dev` with `Ctrl-C`. The command only starts local development
processes, so no additional cleanup is required.

### Optional installed-CLI shortcut

If AgentSeek is already installed in your active environment, you can omit the
`uvx` prefix. Run `agentseek task sync`, `agentseek task frontend`, and
`agentseek task mcp-smoke`, then inspect with `agentseek doctor`.
Start all three development services with `agentseek dev`.

## Configure MCP servers

Edit `.mcp.json`. Its `mcpServers` object must contain at least one server. This
example shows the supported `stdio` and Streamable HTTP shapes together:

```json
{
  "mcpServers": {
    "calculator": {
      "transport": "stdio",
      "command": "${PYTHON_EXECUTABLE}",
      "args": ["-m", "{{ cookiecutter.project_slug }}.calculator_server"],
      "env": {"CALCULATOR_MODE": "${CALCULATOR_MODE}"}
    },
    "calculator_http": {
      "transport": "http",
      "url": "http://127.0.0.1:{{ cookiecutter.calculator_http_port }}/mcp"
    },
    "billing": {
      "transport": "http",
      "url": "${BILLING_MCP_URL}",
      "headers": {"Authorization": "Bearer ${BILLING_MCP_TOKEN}"}
    }
  }
}
```

`${ENV_VAR}` references are interpolated in commands, arguments, environment
values, URLs, and headers. Every reference must resolve.
`${PYTHON_EXECUTABLE}` is reserved and always resolves to the current Python
interpreter. An environment variable named `PYTHON_EXECUTABLE` cannot override
it.

Server names may contain letters, numbers, `_`, and `-`. Every configured server
must connect and expose at least one tool. If any server fails or returns no
tools, graph creation fails without a partial tool set.

`tool_name_prefix=True` publishes `<server>_<tool>` names. The local tools are
therefore `calculator_add`, `calculator_multiply`, `calculator_http_add`, and
`calculator_http_multiply`. The smoke task checks the complete discovered
tool-name tuple and performs a real invocation through each transport. Adding,
removing, or replacing any server changes the complete discovered tool-name
tuple, so update the calculator smoke contract at the same time.

The lifecycle starts `calculator_http_server` on loopback and checks its public
`/health` route. The MCP protocol remains at `/mcp`. To use a remote HTTP tool
service instead, replace `calculator_http` and use environment references for
its URL or headers, such as `${BILLING_MCP_URL}` and `${BILLING_MCP_TOKEN}`.

Final names must be unique and cannot replace the enabled DeepAgents built-ins:
`write_todos`, `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, or
`execute`. The `task` tool is disabled by this template's harness profile and
is not reserved.

This template pins DeepAgents to `0.6.12` because the enabled built-in tool set
and harness profile APIs are characterized for that exact runtime. Before
upgrading DeepAgents, rerun and update the real built-in collision
characterization, reserved-name set, and profile regressions together.

Restart the AgentSeek development processes after changing `.mcp.json`, model
settings, or server credentials. MCP tool calls are stateless and do not retain
persistent MCP client sessions between calls.

## Configuration reference

### Model and tracing

Set `AGENTSEEK_MODEL_PROVIDER` and `AGENTSEEK_MODEL` for the DeepAgents graph.
`DEEPAGENTS_MODEL` and `BUB_MODEL` are model-name compatibility aliases.
`AGENTSEEK_MODEL_API_KEY` is required by `agentseek doctor` and is passed
explicitly to whichever provider adapter is selected. Provider-native API keys
remain fallbacks when the graph is invoked directly, but they do not satisfy
the lifecycle readiness check. Optional custom endpoints continue to use the
provider-native variables in `.env.example`.

Optional LangSmith tracing uses `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and
`LANGSMITH_PROJECT`.

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MODEL_PROVIDER` | Provider: `openai`, `anthropic`, or `google_genai`; aliases `google` and `gemini` are accepted. |
| `AGENTSEEK_MODEL` | Required model name. `DEEPAGENTS_MODEL` and `BUB_MODEL` are compatibility fallbacks. |
| `AGENTSEEK_MODEL_API_KEY` | Required lifecycle credential; passed to the selected provider adapter. |
| `OPENAI_API_KEY`, `OPENAI_API_BASE` | OpenAI direct-runtime key fallback and optional endpoint. |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_API_URL` | Anthropic direct-runtime key fallback and optional endpoint. |
| `GOOGLE_API_KEY`, `GOOGLE_API_BASE` | Google direct-runtime key fallback and optional endpoint. |
| `LANGSMITH_TRACING` | Set `true` to enable optional LangSmith tracing. |
| `LANGSMITH_API_KEY` | LangSmith credential when tracing is enabled. |
| `LANGSMITH_PROJECT` | Optional LangSmith project name. |

### Development hosts

All three development processes bind to loopback by default. For a one-run
remote or container bind of LangGraph and Vite, opt in from the launching shell:

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 uvx agentseek dev
```

`LANGGRAPH_HOST` controls LangGraph from the launching shell. `FRONTEND_HOST`
controls Vite from that shell or `frontend/.env`. The root `.env` configures the
application, model, MCP values, and tracing; it does not configure either server
bind address.

Binding to `0.0.0.0` makes the development services reachable from other hosts.
Add an authenticated reverse proxy, TLS, and network access controls before any
non-loopback use.

The frontend derives `http://<browser-host>:{{ cookiecutter.langgraph_port }}`
by default. If the frontend is served over HTTPS, or a reverse proxy changes
the backend's public scheme, port, or path, set `VITE_LANGGRAPH_API_URL` in
`frontend/.env` to the public LangGraph API URL. Leave it unset for the
browser-derived local default. Keep MCP URLs, headers, and credentials out of
Vite variables.

### Optional installed-CLI shortcut

If AgentSeek is already installed in your active environment, the equivalent
remote-bind command is:

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev
```

## Security and v1 boundaries

Treat every configured `stdio` command as trusted local code execution. Review
its command, arguments, environment, and package source before starting
AgentSeek.

Keep secrets in the process environment or the untracked `.env` file and
reference them from `.mcp.json` with `${ENV_VAR}`. The root `.env` file is loaded
by both `agentseek task mcp-smoke` and `agentseek dev`, while exported process
values take precedence. Never put secret literals in tracked `.mcp.json`,
commits, logs, error messages, shell output, or shared output, and never echo
them. Do not rely on the template to redact arbitrary MCP tool error content.

For Streamable HTTP, the loader accepts absolute `http` and `https` URLs. URL
validation is not transport security. TLS, network ACLs, and authentication or
OAuth must be enforced at the MCP server, gateway, or deployment boundary. This
template does not provide OAuth helpers.

MCP tool descriptions and annotations do not authorize calls. Enforce identity
and permissions in the tool service. If you add DeepAgents human-in-the-loop
policy for side effects, target the final prefixed name:

```python
interrupt_on={
    "billing_charge_card": {"allowed_decisions": ["approve", "reject"]},
}
```

This example does not enable automatic HITL. You must add and test that policy in
the graph assembly.

This v1 template exposes MCP Tools only. It does not expose MCP Resources or
Prompts, persistent MCP client sessions, interceptors, OAuth helpers, or a
browser-based MCP configuration editor.
