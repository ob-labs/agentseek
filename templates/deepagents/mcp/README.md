# DeepAgents MCP template

This template scaffolds a DeepAgents application around a strict MCP Tools
boundary. It includes a local calculator MCP server, model-free smoke coverage,
a streamed React UI, and an AgentSeek lifecycle specification.

## Architecture

The generated application keeps four responsibilities separate:

- `.mcp.json` declares the MCP servers and transport settings.
- `config.py` validates the complete file before interpolating environment values.
- `mcp_tools.py` discovers every server and adds stable server-name prefixes.
- `agent.py` builds and caches one DeepAgents graph for the process lifetime.

The frontend renders streamed messages, tool calls, results, and errors. It is a
chat client, not a browser-based MCP configuration editor.

### Connection contract

The `mcpServers` object must contain at least one server. Server names may use
letters, numbers, `_`, and `-`. They become the prefix for exposed tool names.

A `stdio` server has this shape:

```json
{
  "mcpServers": {
    "calculator": {
      "transport": "stdio",
      "command": "${PYTHON_EXECUTABLE}",
      "args": ["-m", "mcp_deepagent.calculator_server"],
      "env": {"SERVICE_TOKEN": "${SERVICE_TOKEN}"}
    }
  }
}
```

A Streamable HTTP server uses the adapter's `http` transport value:

```json
{
  "mcpServers": {
    "billing": {
      "transport": "http",
      "url": "${BILLING_MCP_URL}",
      "headers": {"Authorization": "Bearer ${BILLING_MCP_TOKEN}"}
    }
  }
}
```

`${ENV_VAR}` references work in commands, arguments, environment values, URLs,
and headers. Every reference must resolve. `${PYTHON_EXECUTABLE}` is reserved:
it always resolves to the interpreter running the application and ignores an
environment variable with that name.

Configuration and discovery are all-or-nothing. Every configured server must
connect and expose a nonempty tool list. One failure prevents graph creation.
`tool_name_prefix=True` exposes tools as `<server>_<tool>`, such as
`calculator_add` or `billing_charge_card`.

The graph is cached after the first successful build. Restart the AgentSeek
development processes after changing `.mcp.json`, model settings, or server
credentials. Connections are stateless; this v1 template does not retain
persistent sessions between tool calls.

## Adapt the template

Keep the local calculator while adding a server so `agentseek task mcp-smoke`
remains a model-free transport and schema check. If you replace the calculator,
replace the smoke contract in `mcp_smoke.py` at the same time.

Set `AGENTSEEK_MODEL_PROVIDER` and `AGENTSEEK_MODEL` for the DeepAgents graph.
`DEEPAGENTS_MODEL` and `BUB_MODEL` remain model-name compatibility aliases.
Provider credentials and custom endpoints use the provider-native variables in
`.env.example`. Optional LangSmith tracing uses `LANGSMITH_TRACING`,
`LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`.

LangGraph and Vite bind to loopback by default. `LANGGRAPH_HOST` must be present
in the shell that starts `agentseek dev`. `FRONTEND_HOST` may be set in that
shell or in `frontend/.env`. Do not add these controls to the root `.env`; it is
reserved for application, model, MCP, and tracing settings.

This v1 boundary exposes MCP Tools only. It does not expose MCP Resources or
Prompts. It also omits persistent sessions, interceptors, OAuth helpers, and a
browser-based MCP configuration editor.

## Security boundary

Treat every configured `stdio` command as trusted local code execution. Review
the executable, arguments, working environment, and package source before use.

For Streamable HTTP, the template validates configuration shape and absolute
`http` or `https` URLs. A deployment must provide TLS, network ACLs, and
authentication or OAuth at the MCP server, gateway, or platform boundary. This
template does not create that boundary.

MCP tool descriptions and annotations are model hints. They do not authorize a
call. Enforce authorization in the tool service. For explicit DeepAgents
human-in-the-loop policy, use the final prefixed tool name, for example:

```python
interrupt_on={
    "billing_charge_card": {"allowed_decisions": ["approve", "reject"]},
}
```

This naming rule does not enable automatic HITL. An application contributor must
add and test the policy when assembling the graph.
