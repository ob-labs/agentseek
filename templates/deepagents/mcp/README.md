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

`${ENV_VAR}` references are interpolated in commands, arguments, environment
values, URLs, and headers. Every reference must resolve.
`${PYTHON_EXECUTABLE}` is reserved and always resolves to the current Python
interpreter. An environment variable named `PYTHON_EXECUTABLE` cannot override
it.

Configuration and discovery are all-or-nothing. Every configured server must
connect and expose at least one tool. If any server fails or returns no tools,
graph creation fails without a partial tool set. `tool_name_prefix=True`
exposes tools as `<server>_<tool>`, such as `calculator_add` or
`billing_charge_card`.

The graph is cached after the first successful build. Restart the AgentSeek
development processes after changing `.mcp.json`, model settings, or server
credentials. MCP tool calls are stateless and do not retain persistent MCP
client sessions between calls.

## Adapt the template

The smoke task checks the complete discovered tool-name tuple, schema, and
calculation. Adding, removing, or replacing any server changes the complete
discovered tool-name tuple, so update the calculator smoke contract at the same
time.

Set `AGENTSEEK_MODEL_PROVIDER` and `AGENTSEEK_MODEL` for the DeepAgents graph.
`DEEPAGENTS_MODEL` and `BUB_MODEL` are model-name compatibility aliases.
Provider credentials and optional custom endpoints use the provider-native
variables in `.env.example`. Optional LangSmith tracing uses `LANGSMITH_TRACING`,
`LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`.

Both development services bind to loopback by default. `LANGGRAPH_HOST` controls
LangGraph from the launching shell. `FRONTEND_HOST` controls Vite from that
shell or `frontend/.env`. Do not add these controls to the root `.env`; it is
reserved for application, model, MCP, and tracing settings.

This v1 template exposes MCP Tools only. It does not expose MCP Resources or
Prompts, persistent MCP client sessions, interceptors, OAuth helpers, or a
browser-based MCP configuration editor.

## Security boundary

Treat every configured `stdio` command as trusted local code execution. Review
the executable, arguments, working environment, and package source before use.

Keep secrets in the process environment or the untracked `.env` file and
reference them from `.mcp.json` with `${ENV_VAR}`. Never put secret literals in
tracked `.mcp.json`, commits, logs, error messages, shell output, or shared
output, and never echo them. Do not rely on the template to redact arbitrary MCP
tool error content.

For Streamable HTTP, the template validates configuration shape and absolute
`http` or `https` URLs. TLS, network ACLs, and authentication or OAuth must be
enforced at the MCP server, gateway, or deployment boundary. This template does
not create that boundary.

MCP tool descriptions and annotations do not authorize calls. Enforce
authorization in the tool service. For explicit DeepAgents human-in-the-loop
policy, use the final prefixed tool name, for example:

```python
interrupt_on={
    "billing_charge_card": {"allowed_decisions": ["approve", "reject"]},
}
```

This example does not enable automatic HITL. An application contributor must add
and test the policy when assembling the graph.
