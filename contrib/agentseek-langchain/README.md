# agentseek-langchain

`agentseek-langchain` is an optional Bub-compatible plugin that routes `run_model` through a LangChain `Runnable`.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-langchain` |
| Python package | `agentseek_langchain` |
| Bub entry point | `langchain` |
| Config section / surface | Environment variables only |
| Root install path | `uv sync --extra langchain` |
| Test target | `make check-langchain` |

## When To Use It

Use this package when you want to keep Bub/agentseek as the harness but delegate model execution to a LangChain runnable that you own.

The plugin does not own the LangChain agent implementation, remote service, or model credentials. It loads your factory, builds a request object, and invokes the returned `RunnableBinding`.

Current scope:

- only LangChain `Runnable` factories are supported
- Bub tools can be bridged into LangChain tools
- user-managed remote agent-protocol runnables can be wrapped through `langgraph-sdk`
- Bub tape recording still works for user / assistant turns and tool spans
- prompts starting with `,` still fall through to Bub built-in internal commands

## Install

From the repo root:

```bash
uv sync --extra langchain
```

Or install only the plugin package runtime:

```bash
uv pip install -e contrib/agentseek-langchain
```

That direct package install is mainly for plugin-only development outside the root extra flow.

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

## Configure

Set a factory reference:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=minimal_runnable:minimal_lc_agent
```

The plugin is active whenever `AGENTSEEK_LANGCHAIN_FACTORY` or `BUB_LANGCHAIN_FACTORY` is non-empty.

| agentseek variable | Bub variable | Default | Purpose |
| --- | --- | --- | --- |
| `AGENTSEEK_LANGCHAIN_FACTORY` | `BUB_LANGCHAIN_FACTORY` | unset | Callable reference in `module:attr` form. Enables the plugin when non-empty. |
| `AGENTSEEK_LANGCHAIN_INCLUDE_BUB_TOOLS` | `BUB_LANGCHAIN_INCLUDE_BUB_TOOLS` | `true` | Expose Bub tools to the runnable as LangChain tools. |
| `AGENTSEEK_LANGCHAIN_TAPE` | `BUB_LANGCHAIN_TAPE` | `true` | Record user, assistant, and tool spans to the session tape. |

`BUB_LANGCHAIN_*` remains valid and takes precedence when both prefixes are set.

### Factory Contract

`AGENTSEEK_LANGCHAIN_FACTORY` must point to a callable `module:attr`.
The callable must accept a single `request: LangchainFactoryRequest` keyword argument.
The factory must return `RunnableBinding`.

`RunnableBinding.invoke_input` is always explicit.
`RunnableBinding.output_parser` is optional; if omitted, the adapter uses the default LangChain output normalizer.
`RunnableBinding.stream_parser` is optional; if absent, streaming falls back to `ainvoke` for a stable final output.

The plugin does not own the runnable implementation.
If your factory uses DeepAgents, a remote agent-protocol service, or any other runtime, that runtime is managed by your factory and its own settings.

## Run

From the repository root:

```bash
uv sync --extra langchain
export PYTHONPATH="$(pwd)/contrib/agentseek-langchain/examples${PYTHONPATH:+:$PYTHONPATH}"
export AGENTSEEK_LANGCHAIN_FACTORY=minimal_runnable:minimal_lc_agent
uv run agentseek run "Summarize this workspace in one sentence."
```

If you also want Bub tools available to the runnable, keep `AGENTSEEK_LANGCHAIN_INCLUDE_BUB_TOOLS` unset or set it to `true`.

To disable tape recording for the adapter:

```bash
export AGENTSEEK_LANGCHAIN_TAPE=false
```

### Examples

Bundled examples are plain Python files under [`examples/`](examples/):

- [minimal_runnable.py](examples/minimal_runnable.py)
- [deepagents_dashscope.py](examples/deepagents_dashscope.py)
- [remote_agent_protocol.py](examples/remote_agent_protocol.py)
- [examples/README.md](examples/README.md)

Typical minimal run:

```bash
export PYTHONPATH="$(pwd)/contrib/agentseek-langchain/examples${PYTHONPATH:+:$PYTHONPATH}"
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

## Runtime Behavior

- `run_model` and `run_model_stream` are implemented with `tryfirst=True`, so this plugin gets the first chance to handle model calls when enabled.
- The plugin is skipped when `AGENTSEEK_LANGCHAIN_FACTORY` / `BUB_LANGCHAIN_FACTORY` is unset or blank.
- String prompts starting with `,` are skipped so Bub internal commands still work.
- When tape recording is enabled and a runtime agent is present, the adapter forks the session tape, writes user/assistant messages, records tool spans through callbacks, and merges back for normal session IDs.
- When Bub tool bridging is enabled, the adapter converts the Bub tool registry into LangChain tools with a `ToolContext`.

## Verify

From the repository root:

```bash
make check-langchain
```

Or run only this package's tests after syncing the extra:

```bash
uv sync --extra langchain
uv run python -m pytest contrib/agentseek-langchain/tests
```

## Limitations

- The plugin supports `Runnable` factories, not arbitrary LangChain object discovery.
- Runtime-specific settings for DeepAgents, remote agent-protocol services, or model providers belong to your factory or example code.
- Example dependencies used only for development are not part of the plugin runtime dependency set.
