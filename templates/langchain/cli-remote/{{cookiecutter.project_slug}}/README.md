# {{ cookiecutter.project_name }}

一个通过 `agentseek-langchain.LangGraphClientRunnable` 接入 Bub 的
LangGraph CLI remote agent 项目。

## Quickstart

```bash
cp .env.example .env
$EDITOR .env

uvx agentseek info
uvx agentseek doctor
uvx agentseek task sync
uvx agentseek dev
uvx agentseek task --list
```

`agentseek dev` 会按 `.agentseek/lifecycle.toml` 启动本地 LangGraph dev
server。运行中的服务检查也只由 lifecycle spec 声明；需要检查时运行：

```bash
uvx agentseek doctor --live
```

`.env` 中的 `BUB_MODEL` 和 `BUB_API_KEY` 供 remote graph 使用。
当模型以 `openai:` 开头时，项目会在缺省情况下把这些值桥接到
OpenAI-compatible 环境变量。`BUB_LANGCHAIN_SPEC` 指向本项目的
Bub binding，`LANGGRAPH_URL` 和 `LANGGRAPH_ASSISTANT_ID` 指向
LangGraph Agent Server。

Author: {{ cookiecutter.author }}
