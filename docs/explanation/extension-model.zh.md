---
title: 扩展模型
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - docs/how-to/install-a-plugin.md
  - AGENTS.md
  - contrib/README.md
  - pyproject.toml
  - src/agentseek/cli/runtime.py
---

# 扩展模型

> **简而言之：** 你可能想对 agentseek runtime 做的任何改动，都对应到五个地方之一 ——
> **项目 instructions**、**skill**、**plugin**、**MCP server**，或 **contrib 包**。
> 挑选适合的最小那个，让其他保持为空。

## 背景

人们很少只用一种方式扩展 agent。他们想教它一个事实、给它一个工具、换掉 model provider、给它一个
新 transport、把状态持久化到别处，并把一个长期维护的集成交付给同事 —— 全在同一个项目里。
没有清晰的矩阵，每次改动都会默认变成 "写一个 plugin"，这会过度构建简单情形；或变成 "改 prompt"，
这又会让 runtime 需求得不到充分服务。

agentseek 原封不动地继承了 Bub 的 extension 表面。本页就是那个决策矩阵，让你在打开对应操作指南前
做出选择。

## 工作原理

### 矩阵

使用与改动相匹配的最小 extension point。这是过去 `extensions.md` 一直开篇就摆的规则，
现在被提升为一篇纯概念解释页面，让操作指南得以保持简短。

| 需求 | 使用 | 编写形态 | 位于 | 何时升级 |
| --- | --- | --- | --- | --- |
| 持久性的项目 instructions（channel、约定、runtime 规则） | **项目 instructions** | 一个 Markdown 文件 | [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md) | 当规则依赖 runtime 状态或某次具体 tool call 时 —— 那就是一个 skill 或 plugin。 |
| 任务专属行为、工作流知识、agent 应该知道如何调用的小脚本 | **Agent Skill** | 一个文件夹里的 `SKILL.md`（外加可选脚本） | `.agents/skills/`（项目）、`src/skills/`（捆绑） | 当你需要一个新的 hook、channel、store 或 tool 注册时。 |
| Runtime hook、channel、tool、store、scheduler、model provider | **Bub 兼容的 plugin** | 带 `[project.entry-points.bub]` 的 Python 包 | 安装到与 agentseek 同一个 venv；sandbox 在 `.agentseek/agentseek-project` | 当集成大到足以拥有自己的文档、测试和可选依赖时 —— 那就是一个 contrib 包。 |
| 已经能说 MCP 的外部工具或服务 | **MCP server entry** | `mcp.json` 中的一条 JSON entry | `.agentseek/mcp.json`（默认）或 `.agents/mcp.json` | 当集成需要自己的 runtime hook 时 —— 写一个 plugin。 |
| 带有自己依赖、配置、示例的较大维护性集成 | **Contrib 包** | `contrib/agentseek-*/` 下的 Python 包 | Monorepo workspace 成员；`pyproject.toml:27-46` 中的可选 extra | 这是终点；contrib 包拥有自己的文档。 |

### 为什么是一行，而不是多行

如果你能用**项目 instructions** 解决改动，就这么做，然后停下来。如果一个事实需要 *行为* ——
调用这个脚本、遵循这个工作流 —— 把它提升为一个 **skill**。如果那个工作流需要让 runtime 知道
某些新东西 —— 一个新 channel、一个 tape store、一个 model 能直接调用的 tool —— 把它提升为一个
**plugin**。如果 runtime 改动是 "model 应该访问一个我不拥有的外部 server"，**MCP entry**
是更便宜的形式。任何带有自己依赖、配置段和测试的，都会成为一个 **contrib 包**，
也就是一个带 README 约定的 plugin。

这五行是按成本刻意排序的。文档其余部分强化这个排序：操作指南以最便宜的形式开头，参考页面列出
确切的旋钮，contrib monorepo（`contrib/README.md`）为最重的那一步设定标准。

### 矩阵所依赖的 Bub 约定

- Plugin 通过 `[project.entry-points.bub]` 注册（`contrib/README.md`）。
- Skill 从 workspace（`.agents/skills/`）和打包好的 distribution 中发现
  （捆绑的 `src/skills` 通过 `pyproject.toml:73-77` 被包含进 build）。
- MCP 配置路径遵循 [agentseek 与 Bub 的关系](bub-relationship.zh.md) 中的 alias 模型：默认是
  `${BUB_HOME}/mcp.json`，通过 `AGENTSEEK_MCP_CONFIG_PATH` override。
- 位于 `.agentseek/agentseek-project` 的 install sandbox 由 `src/agentseek/cli/runtime.py:115-140`
  按需创建。Plugin 落到那个 sandbox 的环境里，并非 runtime 隔离单元。

## 为什么是这样

- **便宜的东西应保持便宜。** 一个新事实不应该需要一个 Python 包；一个工作流不应该需要一个 plugin。
  矩阵的存在让正确答案通常也是最小答案。
- **Runtime 扩展是审慎的，而非偶然的。** hook、channel、store 都影响每一轮 turn。把它们放到打包
  步骤（plugin 或 contrib 包）背后，让这个选择变得可见、可审。
- **contrib README 是文档标准。** 一旦集成重到需要安装步骤、环境变量和 runtime 行为说明时，
  这些事实应该挨着代码。这就是为什么
  [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)
  定义了固定的小节顺序，而主文档只链接出去。
- **`AGENTSEEK_*` 环境变量** 是 distribution 范围设置的推荐前缀。
  详见[环境变量参考](../reference/environment.zh.md)。

## 如何选择

- 第一个要问的问题是 "这属于矩阵的哪一行？" —— 而不是 "我需要 plugin 吗？"。
- [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md) 中的项目 instructions
  对这个 repo 中的每一轮 turn 都生效；把它当作持久内容对待，不要当成草稿空间。
- 任何在你自己代码里本来会变成 `print` 语句的东西，可能都属于某个 skill 或 plugin hook；
  无论哪种情况，tape 都会捕获它。
- 你为别人维护的重量级集成应该落在 `contrib/agentseek-<feature>/` 下，并从一开始就遵循 README
  标准。捆绑的 `plugin-creator` skill（位于 `src/skills/plugin-creator/`）会脚手架出布局。
- 矩阵同时是 how-to 组的导航键：每一行都有一个 how-to 页面（对 skill 和 MCP，还有参考页面），
  当行被选中后你可以跳过去。

## 相关

- 操作指南：
  - 项目 instructions：直接编辑 [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md)。
  - [如何添加 skill](../how-to/add-skills.zh.md)
  - [如何安装插件](../how-to/install-a-plugin.zh.md)
  - [如何添加 MCP 服务器](../how-to/add-mcp-server.zh.md)
  - [如何编写一个 contrib plugin](../how-to/author-a-contrib-plugin.zh.md)
- 参考：[包参考](../reference/packages.zh.md),
  [文件布局参考](../reference/file-layout.zh.md)
- 概念解释：[运行时数据模型](runtime-data-model.zh.md),
  [agentseek 与 Bub 的关系](bub-relationship.zh.md)
- 外部：[Bub Hub](https://hub.bub.build),
  [Model Context Protocol](https://modelcontextprotocol.io/)
