# {{ cookiecutter.project_name }}

This AgentSeek project runs a DeepAgents graph with MCP Tools from validated
`stdio` or Streamable HTTP connections. It includes a local calculator server,
a model-free smoke check, and a streamed React UI.

## Run the project for the first time

### Prerequisites

- Python 3.12 or newer with `uv`.
- `uvx`, included with `uv`, for isolated AgentSeek CLI commands.
- Node.js `^20.19.0 || ^22.13.0 || >=24.0.0` with `npm`.
- A model name and credential for OpenAI, Anthropic, or Google when you send chat.

Run the first two copy commands, then edit `.env`. Set
`AGENTSEEK_MODEL_PROVIDER`, `AGENTSEEK_MODEL`, and one matching provider key.
Continue with the remaining commands in this exact order:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
uvx agentseek task sync
uvx agentseek task frontend
uvx agentseek task mcp-smoke
uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
```

The smoke task discovers `calculator_add` and `calculator_multiply`, validates
the add-tool schema, and checks `37 + 58 = 95`. It does not call a model.
`agentseek info`, `agentseek doctor`, and the dry run inspect the lifecycle before
the last command starts LangGraph and Vite.

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` after both services
start. Sending a message invokes your configured hosted model. The template's
local verification covers lifecycle startup, MCP discovery, and the calculator;
it does not claim a hosted chat was executed without a real provider key.

Stop `uvx agentseek dev` with `Ctrl-C`. The command only starts local development
processes, so no additional cleanup is required.

If AgentSeek is already installed in your active environment, you can omit the
`uvx` prefix. Run `agentseek task sync`, `agentseek task frontend`, and
`agentseek task mcp-smoke`, then inspect with `agentseek doctor` and start both
development services with `agentseek dev`.

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
    "billing": {
      "transport": "http",
      "url": "${BILLING_MCP_URL}",
      "headers": {"Authorization": "Bearer ${BILLING_MCP_TOKEN}"}
    }
  }
}
```

Define referenced values in the environment that starts AgentSeek. `${ENV_VAR}`
interpolation works in commands, arguments, `env`, URLs, and headers. Every
reference must resolve. `${PYTHON_EXECUTABLE}` is reserved and always resolves
to the current Python interpreter; an environment override is ignored.

Server names may contain letters, numbers, `_`, and `-`. The loader requires
every configured server to connect and return a nonempty tool list. A failure
stops graph creation instead of starting with a partial tool set.

`tool_name_prefix=True` publishes `<server>_<tool>` names. The local tools are
therefore `calculator_add` and `calculator_multiply`. Restart `agentseek dev`
after changing `.mcp.json`, credentials, or model settings. MCP tool connections
are stateless; this template does not keep persistent sessions between calls.

## Configuration reference

### Model and tracing

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MODEL_PROVIDER` | Provider: `openai`, `anthropic`, or `google_genai`; aliases `google` and `gemini` are accepted. |
| `AGENTSEEK_MODEL` | Required model name. `DEEPAGENTS_MODEL` and `BUB_MODEL` are compatibility fallbacks. |
| `OPENAI_API_KEY`, `OPENAI_API_BASE` | OpenAI credential and optional endpoint. |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_API_URL` | Anthropic credential and optional endpoint. |
| `GOOGLE_API_KEY`, `GOOGLE_API_BASE` | Google credential and optional endpoint. |
| `LANGSMITH_TRACING` | Set `true` to enable optional LangSmith tracing. |
| `LANGSMITH_API_KEY` | LangSmith credential when tracing is enabled. |
| `LANGSMITH_PROJECT` | Optional LangSmith project name. |

### Development hosts

Both services bind to `127.0.0.1` by default. For a one-run remote or container
bind, opt in from the launching shell:

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev
```

`LANGGRAPH_HOST` must be a shell export or inline assignment when AgentSeek
starts. `FRONTEND_HOST` may instead be stored in `frontend/.env`. The root `.env`
configures the application, model, MCP values, and tracing; it does not configure
either server bind address.

Binding to `0.0.0.0` makes the development services reachable from other hosts.
Add an authenticated reverse proxy, TLS, and network access controls before any
non-loopback use.

## Security and v1 boundaries

A configured `stdio` command is trusted local code execution. Review its command,
arguments, environment, and package source before starting AgentSeek.

For Streamable HTTP, the loader accepts absolute `http` and `https` URLs. URL
validation is not transport security. TLS, network ACLs, and authentication or
OAuth belong at the MCP server, gateway, or deployment boundary. This template
does not provide OAuth helpers.

MCP descriptions and annotations are model hints, not authorization. Enforce
identity and permissions in the tool service. If you add DeepAgents
human-in-the-loop policy for side effects, target the final prefixed name:

```python
interrupt_on={
    "billing_charge_card": {"allowed_decisions": ["approve", "reject"]},
}
```

The template does not configure automatic HITL. You must add and test that policy
in the graph assembly.

This v1 template exposes MCP Tools. It does not expose MCP Resources or Prompts.
It has no persistent sessions, interceptors, or OAuth helpers. It also has no
browser-based MCP configuration editor.
