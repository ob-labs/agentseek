---
title: 运行时数据模型
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - pyproject.toml
  - contrib/README.md
  - blog/introducing-agentseek.md
---

# 运行时数据模型

> **简而言之：** 五样东西流经 harness —— **tape**、**skill**、**MCP** server、**plugin**
> 和 **channel**。第一个是持久底层基座；其余则塑造一轮 turn 的进出。理解谁是谁，
> 会让 [扩展模型](extension-model.zh.md) 中的决策矩阵变得显而易见。

## 背景

agentseek 打包了 Bub，而 Bub 有意保持小巧：一个跑 turn 的 kernel，加上一个供给其他一切的 plugin
系统（见 [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/)）。下面这五个概念是
Bub 的词汇；agentseek 原封不动地继承它们，并为它们在 workspace 中的位置添加默认值。

无论你是通过 CLI 还是通过 library 到达 agentseek，下面这五个概念都决定了一轮 turn 携带什么、
持久化到哪里、以及 agent 如何触达外部世界。本页给它们命名，让文档其余部分可以按名字引用。

## 工作原理

```text
                  ┌──────────────────────────────────────────┐
   user / app ──► │  channel  (cli, gateway, feishu, ag-ui…) │
                  └───────────────────┬──────────────────────┘
                                      │  turn
                  ┌───────────────────▼──────────────────────┐
                  │           framework (Bub kernel)         │
   plugins ─────► │   hooks: provide_tape_store, model,      │
                  │          tools, schedule, channels…      │
                  └──────┬─────────────┬─────────────┬───────┘
                         │             │             │
                  ┌──────▼───┐  ┌──────▼───┐  ┌──────▼──────┐
                  │  skills  │  │   MCP    │  │   tape      │
                  │ (advice) │  │ (tools)  │  │ (durable)   │
                  └──────────┘  └──────────┘  └─────────────┘
```

### Tape —— 持久底层基座

**tape** 是一条 append-only 的事实流，记录一轮 turn 的内容：输入消息、model call、tool call
及其结果、anchor，以及任何派生视图。这个模型在 [Tape Systems](https://tape.systems/) 中有描述；
agentseek 把它当作权威的 runtime 数据形态，这就是 "database-native" 在实践中的含义
（见 [认识 agentseek](../blog/introducing-agentseek.zh.md)）。

Bub 通过 `provide_tape_store` hook 暴露持久化。实现该 hook 的 plugin 决定 tape entry 落到哪里：

- 默认的 Bub tape store 写到 `BUB_HOME` 内的一个本地 SQLite 文件
  （在 agentseek 默认下是 `.agentseek/` —— 关于这个默认值如何设定，
  见 [agentseek 与 Bub 的关系](bub-relationship.zh.md)）。
- `agentseek-tapestore-oceanbase` 替换为 SQLAlchemy 存储，兼容 OceanBase，可选向量检索。
  完整配置在它自己的 README 中
  （[contrib/agentseek-tapestore-oceanbase/](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase)）。

因为 tape 把 input + 步骤 + output 作为一条流捕获，同一份数据为 debug、replay、轨迹比较、评估和
训练供给数据，无需通过旁路 channel 复制。

### Skill —— 任务专属行为

**skill** 是一个小型 Markdown 包（一个包含 `SKILL.md` 的文件夹），教 agent 如何做一项任务。
Bub 从 workspace 和包中发现 skill。在本 repository 中：

- **Project-local skills** 位于 `.agents/skills/<skill-name>/SKILL.md`。它们在本地运行期间生效，
  因为 Bub 从 workspace 中发现它们；Docker entrypoint 在容器内保留相同路径
  （`entrypoint.sh:7-8,30-35`）。
- **Bundled skills** 位于 `src/skills/<skill-name>/SKILL.md`，随 `agentseek` distribution
  一起发布，因为 `pyproject.toml:73-77` 将 `src/skills` 包含进 build。
- **External skills** 可以通过 `[tool.pdm.build].skills` 在 build 时被导入
  （`pyproject.toml:78-80`），这就是今天 `friendly-python` 和 `piglet` 被捆绑进来的方式。

skill 是建议性的：它们塑造 model 做什么，但不注册新 tool 或 hook。当一个改动 *本身就是* runtime
行为 —— 一个新的 model provider、一个新 channel、一个 tape store、一个 tool 集成 —— 就改写
plugin。决策矩阵在 [扩展模型](extension-model.zh.md)。

### MCP —— 在配置中声明的外部 tool

**Model Context Protocol** 是 agent 调用 Python 进程外 tool 的标准方式。`bub-mcp` plugin
读取一个 MCP 配置文件，并把每个声明的 server 暴露为 model 可调用的一组 tool。

默认路径来自 alias 层：

- `bub-mcp` 默认读取 `${BUB_HOME}/mcp.json`，在 agentseek 默认下是 `.agentseek/mcp.json`。
- 你可以通过设置 `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json` 把文件移到项目根目录。
  在容器内，entrypoint 会自动发现 `.agents/mcp.json` 并把它 link 到 runtime 路径
  （`entrypoint.sh:11-15, 37-39`）。

MCP server 适合那些应该被 **声明而非编码** 的 tool 集成 —— issue tracker、搜索后端、内部服务。
当一个 tool 集成需要自己的 runtime hook 时，伸手去拿 plugin。

### Plugin —— runtime 扩展表面

**plugin** 是一个通过 `[project.entry-points.bub]` group 注册自己、并提供一个或多个 hook 实现
的 Python 包。plugin 是 Bub 获得 channel、model provider、tape store、scheduler 和 tool 包的
方式。

agentseek 包含 Feishu、MCP、tape-store OpenTelemetry 与 SQLAlchemy-backed scheduling
这些常用运行时 plugins。其余 plugin 通过 `agentseek plugin install` 按需安装：

| 命令 | 添加 |
| --- | --- |
| `agentseek plugin install agentseek-ag-ui` | AG-UI channel 适配器 |
| `agentseek plugin install agentseek-langchain` | LangChain model 路由 |
| `agentseek plugin install bub-tapestore-otel@main` | Tape-first OpenTelemetry tracing |
| `agentseek plugin install agentseek-tapestore-oceanbase` | OceanBase tape 存储 |
| `agentseek plugin install agentseek-contextseek` | ContextSeek 语义 context 层 |

Plugin 被安装到与 agentseek **相同的 Python 环境** 中；它们不是 sandbox runtime 单元。
位于 `.agentseek/agentseek-project` 的 `agentseek plugin install` sandbox
（见 [agentseek 与 Bub 的关系](bub-relationship.zh.md)）是一个用于解析和添加 plugin 的 uv 项目，
不是 runtime 边界。

### Channel —— 一轮 turn 如何进出

**channel** 是接受消息进入并流式输出响应的表面。CLI（`cli`）是一种；gateway / HTTP transport
是另一种；像 Feishu、Telegram 这样的聊天平台是 plugin 提供的 channel。`agentseek-ag-ui`
plugin 为 CopilotKit 等前端添加一个 AG-UI SSE channel 适配器。

agentseek 的 CLI override 让 **所有 Bub 支持通道（`*.lifecycle`）** 与你请求的主 channel 一同启用
（`src/agentseek/cli/runtime.py:51-57, 83-112`）。这就是让 MCP 和其他 helper 能在交互式
`agentseek chat` 会话内启动的机制 —— 它们在某个 Bub 支持通道上注册自己，manager 会在第一
轮 turn 之前把它们唤醒。

## 为什么是这样

- **一个底层基座，多种消费者。** 把 tape 放在中心位置意味着 debug、replay、评估、训练都从同一个
  地方读取；新消费者不需要新流水线。这就是
  [认识 agentseek](../blog/introducing-agentseek.zh.md) 中描述的赌注。
- **小 kernel，多 plugin。** Bub 让 kernel 保持小巧，所以失败面也保持小巧；其他一切都是 plugin，
  你可以替换、版本化或移除。agentseek 继承这种形态，而不是把存储和 channel 烧进 distribution 本身。
- **Skill 在 model 之上，MCP 和 plugin 在它周围。** Skill 塑造 model 说什么；MCP 和 plugin
  塑造它能做什么。把这两个表面分开能让 authoring 保持便宜（放一个 Markdown 文件），让 runtime
  扩展保持审慎（发布一个 Python 包）。

## 选择正确的扩展点

- 如果你想**读取或查询 runtime 数据**，瞄准 tape store。通过 `provide_tape_store` plugin
  挑选后端；不要发明一条 sidecar 日志。
- 如果你想**改变 model 如何思考一项任务**，写一个 skill。
- 如果你想**添加一个 model 能调用的 tool** 且它已经能说 MCP，在 MCP 配置中声明它；否则写一个
  plugin。
- 如果你想要一个**新地点让 agent 能被触达**，写或安装一个 channel plugin。
- 常用运行时能力随 harness 环境提供；其他能力通过 plugin 按需安装。

## 相关

- 教程：[添加一个 skill 和一个 MCP server](../tutorials/03-add-a-skill-and-mcp.zh.md)
- 操作指南：[如何添加 skill](../how-to/add-skills.zh.md),
  [如何添加 MCP 服务器](../how-to/add-mcp-server.zh.md),
  [如何安装插件](../how-to/install-a-plugin.zh.md)
- 参考：[包参考](../reference/packages.zh.md),
  [文件布局参考](../reference/file-layout.zh.md)
- 概念解释：[扩展模型](extension-model.zh.md),
  [agentseek 与 Bub 的关系](bub-relationship.zh.md)
- 外部：[Tape Systems](https://tape.systems/),
  [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/),
  [Model Context Protocol](https://modelcontextprotocol.io/)
