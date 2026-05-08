# agentseek-langchain

`agentseek-langchain` is an optional Bub-compatible plugin that routes `run_model` through a LangChain `Runnable`.

Current scope:

- only LangChain `Runnable` factories are supported;
- Bub tools can be bridged into LangChain tools;
- user-managed remote agent-protocol runnables can be wrapped through `langgraph-sdk`;
- Bub tape recording still works for user / assistant turns and tool spans;
- prompts starting with `,` still fall through to Bub built-in internal commands.

## Install

From the repo root:

```bash
uv sync --all-packages
```

Or install only the plugin package runtime:

```bash
uv pip install -e contrib/agentseek-langchain
```

The bundled DeepAgents example uses repository development dependencies from the root workspace.
It is not part of the plugin runtime dependency set.

If you want to work on examples and tests from the repo:

```bash
uv sync --all-packages --group dev
```

If you want to run the repository examples directly, expose `examples/` on `PYTHONPATH`:

```bash
export PYTHONPATH="$(pwd)/contrib/agentseek-langchain/examples${PYTHONPATH:+:$PYTHONPATH}"
```

## Enable

Set:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=minimal_runnable:minimal_lc_agent
```

The plugin is active whenever `AGENTSEEK_LANGCHAIN_FACTORY` or `BUB_LANGCHAIN_FACTORY` is non-empty.

Optional flags:

- `AGENTSEEK_LANGCHAIN_INCLUDE_BUB_TOOLS=true|false` (default `true`)
- `AGENTSEEK_LANGCHAIN_TAPE=true|false` (default `true`)

`BUB_LANGCHAIN_*` remains valid and takes precedence when both prefixes are set.

## Factory Contract

`AGENTSEEK_LANGCHAIN_FACTORY` must point to a callable `module:attr`.
The callable must accept a single `request: LangchainFactoryRequest` keyword argument.
The factory must return `RunnableBinding`.

`RunnableBinding.invoke_input` is always explicit.
`RunnableBinding.output_parser` is optional; if omitted, the adapter uses the default LangChain output normalizer.

The plugin does not own the runnable implementation.
If your factory uses DeepAgents, a remote agent-protocol service, or any other runtime, that runtime is managed by your factory and its own settings.

## Examples

Bundled examples are plain Python files under [`examples/`](examples/):

- [minimal_runnable.py](examples/minimal_runnable.py)
- [deepagents_dashscope.py](examples/deepagents_dashscope.py)
- [remote_agent_protocol.py](examples/remote_agent_protocol.py)
- [examples/README.md](examples/README.md)

Typical minimal run:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=minimal_runnable:minimal_lc_agent
uv run agentseek run "Summarize this workspace in one sentence."
```

Typical remote agent-protocol run:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=remote_agent_protocol:remote_agent_protocol_agent
export AGENTSEEK_AGENT_PROTOCOL_URL=http://localhost:2024
export AGENTSEEK_AGENT_PROTOCOL_AGENT_ID=agent
uv run agentseek chat
```

Those `AGENTSEEK_AGENT_PROTOCOL_*` variables are consumed by the example factory, not by the plugin core.
That example wraps a user-managed remote runtime.
`agentseek-langchain` only loads the factory and executes the returned `RunnableBinding`.
