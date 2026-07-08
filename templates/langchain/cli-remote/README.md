# LangChain — cli-remote template

生成一个通过 `langgraph dev` 运行 remote graph，并用
`LangGraphClientRunnable` 接入 Bub 的项目。

## Architecture

```text
uvx agentseek dev
  -> .agentseek/lifecycle.toml
    -> uv run langgraph dev
      -> create_agent(...)

Bub runtime
  -> BUB_LANGCHAIN_SPEC
    -> agentseek-langchain
    -> LangGraphClientRunnable
      -> langgraph_sdk client
        -> LangGraph Agent Server
```

bridge 会向 remote graph 发送只包含 messages 的 state dict：

```python
{"messages": [...]}
```

这样可以避免把本地 Bub runtime 对象写入 JSON request，同时保持
remote `create_agent(...)` 期望的输入形状。

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `default_model` | Default `BUB_MODEL`. |
| `langgraph_url` | Default LangGraph Agent Server URL. |
| `assistant_id` | Graph / assistant id (matches `langgraph.json`). |

## Generated layout

```text
{{ project_slug }}/
  .agentseek/
    lifecycle.toml
  README.md
  pyproject.toml
  requirements.txt
  .env.example
  Dockerfile
  langgraph.json
  src/{{ project_slug }}/
    __init__.py
    remote_graph.py
    gateway_binding.py
    settings.py
```

## Key code patterns

binding 会构造一个 `RunnableSpec`，并用自定义 input adapter 从 Bub state
里只提取 messages：

```python
from agentseek_langchain import LangGraphClientRunnable, RunnableSpec

def build_spec():
    runnable = LangGraphClientRunnable(client, assistant_id="agent")
    return RunnableSpec(
        runnable=runnable,
        build_input=_build_remote_input,
        parse_output=parse_messages_output,
        build_config=default_runnable_config,
    )
```
