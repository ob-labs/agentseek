---
hide_sidebar: true
---

# AgentSeek

AgentSeek 是一个数据库原生的 Agent Harness，适合那些希望把 agent 运行时数据变成
一等数据库工作负载的团队。LangChain 是我们推荐的上手方式。

> **前置条件：** Python 3.12+、[uv](https://docs.astral.sh/uv/)、一个模型 API key。就这些。

**AgentSeek 是一个套件**，由多个可独立使用的组件组成：

| 组件 | 做什么 | 文档 |
| --- | --- | --- |
| **agentseek-cli** | 生成项目、管理生命周期（`create / run / build / deploy`） | [ob-labs/agentseek](https://github.com/ob-labs/agentseek) |
| **agentseek-api** | Agent Protocol 服务——把你的 LangGraph 零改动送上生产 | [ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api) |
| **ContextSeek** | 语义上下文层——记忆、检索、演进、渐进式披露 | [ob-labs/contextseek](https://github.com/ob-labs/contextseek) |
| **langchain-oceanbase** | 数据底座——checkpoint + store + 向量 + hybrid search，基于 OceanBase / seekdb / MySQL | [oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) |

---

## 快速开始 — 面向 LangChain 开发者

**该选哪个模板？**

- **刚入门 / 想试试？** → `langchain/markdown-messages`（最小化，5 分钟）
- **已有 graph，要交付产品？** → `langchain/default`（前端 + 飞书 IM + 完整运行时）
- **做深度研究、需要 sub-agent？** → `deepagents/research`（Tavily + 报告生成）
- **graph 跑在远程（agentseek-api / LangSmith）？** → `langchain/cli-remote`

```bash
# 选一个跑：
uvx --from agentseek-cli agentseek create langchain --template markdown-messages
# 或者: langchain --template default
# 或者: deepagents --template research
```

然后：`cd <项目> && uv sync && uv run langgraph dev`（最小化）或
`uv run agentseek run`（完整交付）。

> **LangSmith tracing 已预配置。** 每个模板都自带 `.env.example`，里面
> `LANGSMITH_TRACING=true` 和 `LANGSMITH_API_KEY` 已经写好，填入你的 key 就能
> 在 LangSmith 里立刻看到完整的 run 观测。

**Agent 跑起来之后的下一步：**

- 加持久记忆 → [ContextSeek 文档](https://github.com/ob-labs/contextseek)
- 服务化上生产 → [agentseek-api 文档](https://github.com/ob-labs/agentseek-api)
- 换成持久数据库 → [langchain-oceanbase 文档](https://github.com/oceanbase/langchain-oceanbase)
- 安装开发 Skills 获得引导 → 见下方[开发 Skills](#开发-skills)
- 系统学习 DeepAgents → 见下方[开源课程](#开源课程)
- 了解整体关系 → [agentseek 与 LangChain 的关系](explanation/langchain-relationship.zh.md)

---

## 面向 OceanBase / seekdb / MySQL 开发者

已经在跑 OceanBase、seekdb 或 MySQL？AgentSeek 把你的数据库变成 AI agent 的
**数据底座**——checkpoint、持久记忆、向量搜索和混合检索全部跑在你已有的 DB 上。

```bash
pip install langchain-oceanbase[pyseekdb]   # OceanBase / seekdb
pip install langchain-oceanbase             # MySQL（checkpoint + store）
```

你会得到：

- **LangGraph Checkpoint** —— 长程 agent 的持久执行状态
- **Store** —— 跨会话持久记忆（namespace 化键值）
- **VectorStore + Hybrid Search** —— embedding 检索融合 BM25（OceanBase / seekdb）

MySQL 用户开箱可用 checkpoint 和 store；向量搜索需要 OceanBase 或 seekdb。
无论哪种，运行时数据从第一天起就是可查 SQL。

**开始使用：**

1. 安装：`pip install langchain-oceanbase[pyseekdb]`
2. 阅读集成指南：[langchain-oceanbase README](https://github.com/oceanbase/langchain-oceanbase#readme)
3. 选一个模板跑完整 agent：`agentseek create langchain --template default`
4. harness tape store 插件：见 [agentseek-tapestore-oceanbase](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase)

---

## 新手？从这里开始

没做过 AI agent？没关系。

1. 确认你安装了 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)
2. 拿一个模型 API key（OpenRouter 免费额度就够：[openrouter.ai](https://openrouter.ai)）
3. 跑：

```bash
uvx --from agentseek-cli agentseek create langchain --template markdown-messages
cd markdown_messages_agent
cp .env.example .env   # 填入你的 API key
uv sync && uv run langgraph dev
```

你现在有一个本地运行的聊天机器人了。打开终端打印的 URL 就能用。

**接下来去哪：**

- [快速演示教程](tutorials/01-quick-demo-cli.zh.md) —— 5 分钟完整演练
- [构建你的第一个 harness 应用](tutorials/02-first-harness-app.zh.md) —— 包含前端的完整教程

---

## 套件各组件速览

### agentseek-api — 把你的 graph 送上生产

```bash
uv run agentseek-api dev
curl http://127.0.0.1:2024/info
```

实现 [Agent Protocol](https://github.com/langchain-ai/agent-protocol)
（threads、runs、streaming、Store API、MCP、A2A）。你的 LangGraph 代码不用改，
直接跑在标准 HTTP 接口后面。

完整文档：[github.com/ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api)

### ContextSeek — 语义上下文层

```python
from contextseek import ContextSeek

ctx = ContextSeek.from_settings()
ctx.add("OceanBase 是金融级分布式数据库",
        scope="acme/db", source="wiki")

for hit in ctx.retrieve("分布式数据库", scope="acme/db", k=5):
    print(hit.item.stage, hit.score, hit.item.summary[:60])
```

统一 `ContextItem` 对象模型，自带溯源（Provenance）、L0/L1/L2 渐进式披露、
EvolutionEngine、DreamEngine。支持 HTTP、MCP 和 Python SDK 三种接入方式。自带
**LangChain middleware**（每轮自动注入上下文）和 **LangSmith `@traceable` 支持**
（完整可观测）。

完整文档：[github.com/ob-labs/contextseek](https://github.com/ob-labs/contextseek)

### langchain-oceanbase — 数据底座

```bash
pip install langchain-oceanbase[pyseekdb]
```

LangGraph Checkpoint + Store + VectorStore + Hybrid Search——全部跑在一个数据库上
（OceanBase、seekdb 或 MySQL）。运行时数据从第一天起就是可查的 SQL。

完整文档：[github.com/oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)

---

## 开源课程

**《Deep Agents 实战》**——免费课程，用 LangChain / DeepAgents 构建生产级 AI Agent。后续所有动手实验基于 AgentSeek。

[课程网站](https://webup.github.io/deepagents-course) · [源码仓库](https://github.com/webup/deepagents-site)

课程覆盖：Agent Harness 概念、虚拟文件系统、任务规划、sub-agent、异步委派、
长期记忆、Human-in-the-Loop、Skills、沙箱执行、流式前端、生产部署。

---

## 开发 Skills

AgentSeek 提供一组**开发 Skills**——可以安装到你的 AI 编程助手（Claude Code、
Cursor 等）中的引导指南，帮你在编辑器里直接解决 LangChain 开发问题。

| Skill | 做什么 |
| --- | --- |
| **langchain-dev-guide** | LangChain / LangGraph 工程踩坑与验证过的修复方案。覆盖 DeepAgents、middleware、streaming、multi-agent 编排等常见问题——每条都是 症状 → 原因 → 解法。 |
| **langchain-cn-models** | 把国内大模型（DeepSeek、通义 Qwen、智谱 GLM、Moonshot 等）接入 LangChain 的分步食谱，走 OpenAI 兼容接口。 |

一键安装所有 skills：

```bash
npx skills add ob-labs/agentseek --all
```

或者选装：

```bash
npx skills add ob-labs/agentseek --skill langchain-dev-guide --agent claude-code
npx skills add ob-labs/agentseek --skill langchain-cn-models --agent claude-code
```

安装后，你的编程助手在你碰到 LangChain 问题时可以直接引用这些指南——不用手动翻文档。

完整说明：[skills/](https://github.com/ob-labs/agentseek/tree/main/skills)
| 如何添加 skills：[添加 skill 指南](how-to/add-skills.zh.md)

---

## 其他路径

**已经在用 [Bub](https://github.com/bubbuild/bub)？** AgentSeek 是 Bub 的发行版，
带有开箱即用的默认配置。试试 `agentseek create bub --template default`，不引入
LangChain 也能跑 CopilotKit + 飞书。详见
[agentseek 与 Bub 的关系](explanation/bub-relationship.zh.md)。

**想用 harness CLI？** 见
[选择一个入口](explanation/choosing-an-entry-point.zh.md)。

## 接下来读什么

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="docs/">文档</a></h3>
    <p>架构、设计动机，以及整套文档的组织方式。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="tutorials/">教程</a></h3>
    <p>引导式演练：快速演示、第一个应用、添加 skill 与 MCP。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">操作指南</a></h3>
    <p>任务式食谱：配置模型、部署、运行 gateway、使用 ContextSeek。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">参考</a></h3>
    <p>环境变量、CLI、包、模板、文件布局、Docker。</p>
  </div>
</div>
