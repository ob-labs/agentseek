---
title: AgentSeek 文档
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-06-12
hide_sidebar: true
sources:
  - README.zh.md
  - mkdocs.yml
  - pyproject.toml
  - src/agentseek/cli/runtime.py
---

# AgentSeek 文档

AgentSeek 帮团队把 agent 运行时数据变成数据库工作负载：turn、context、
工具调用、任务、反馈、checkpoint、memory 和观测数据都保持可查询，而不是散落在
日志和外围系统里。

## 最小命令组合

```bash
uvx agentseek create deepagents/default --no-input
cd my_deepagent
cp .env.example .env
uv sync
uv pip install -r requirements.txt
export PYTHONPATH=src
export AGENTSEEK_LANGCHAIN_SPEC=my_deepagent.demo_binding:build_spec
export AGENTSEEK_AG_UI_PORT=18088
uv run agentseek gateway --enable-channel ag-ui
```

如果你想先体验 harness，再创建项目，看[运行 CLI 快速演示](tutorials/01-quick-demo-cli.zh.md)。

## 项目生命周期

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="tutorials/02-first-harness-app/">创建</a></h3>
    <p>需要可编辑的 harness app 时，从模板开始。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/run-locally/">运行</a></h3>
    <p>配置模型凭证后，在本地运行生成项目。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="tutorials/03-add-a-skill-and-mcp/">扩展</a></h3>
    <p>在应用需要时加入 project-local skills、MCP tools、plugins 或 ContextSeek。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/build-and-deploy/">交付</a></h3>
    <p>在项目根目录构建镜像，并生成部署 manifests。</p>
  </div>
</div>

## 首次跑通之后

- 想要推荐的 AgentSeek harness app，从 `deepagents/default` 开始。
- 想要不带 LangChain 的最轻 harness app，从 `bub/default` 开始。
- 想让 LangChain app 进入 AgentSeek runtime，从 `langchain/default` 开始。
- 做 DeepAgents 形态的产品时，看 `deepagents/research` 或 `deepagents/content-builder`。
- memory 应该成为一等 runtime 能力时，接入 [ContextSeek](how-to/use-contextseek.zh.md)。
- 选择持久存储后端前，先读[运行时数据模型](explanation/runtime-data-model.zh.md)。
- 用 [Hub](hub.zh.md) 浏览 bundled 与 contrib integrations。
