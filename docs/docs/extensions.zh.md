# 扩展

这份指南说明如何扩展 agentseek 项目。若你需要精确变量名和默认值，请配合 [配置](configuration.md) 一起看。

agentseek 继承 Bub 的扩展模型。agentseek 这一层主要增加命名约定、环境变量别名、打包默认值和内置 skill，并不会替换 Bub 的 hook 或 entry point。

## 选择合适的扩展点

优先选择满足需求的最小扩展点：

| Need | Use |
| --- | --- |
| 持久性的项目指令 | `AGENTS.md` |
| 任务级 agent 行为 | Agent Skills |
| 运行时 hook、channel、tool、store 或 scheduler | Bub-compatible plugins |
| 通过 MCP 暴露的外部工具或服务 | MCP server config |
| 更大、可维护的集成能力 | Contrib package README |

## 项目指令

使用 `AGENTS.md` 来告诉 agent 应该如何在你的项目里工作。

好的项目指令通常会包括：

- 启用了哪些 channel，比如 `$feishu` 或 `$telegram`
- agent 什么时候应该直接回复，什么时候应该调用 channel-specific send tool
- 仓库特定的编码、测试和文档规则
- 每个任务都应该遵守的运行时约束

`AGENTS.md` 应该聚焦于长期稳定的行为约束。不要把凭证、只在部署时使用的秘密信息，或一次性的任务笔记放进去。

## 增加插件

插件通过 Bub 的 hook system 增加运行时行为。当你需要新的 channel、模型提供商、store、tool package、scheduler 或其他运行时集成时，走这条路径。

### 从 Bub Hub 安装

插件会安装到与 agentseek **同一个 Python 环境** 中。你可以在 [Bub Hub](https://hub.bub.build/) 浏览整个生态：Hub 上会展示诸如 `bub install bub-feishu@main` 这样的安装规格。

Hub 条目通常使用 `bub install ...`。agentseek CLI 暴露了同一套 resolver：

```bash
uv run agentseek install bub-feishu@main
```

`install` 接受 help 文档里描述的包规格：git URL、`owner/repo`，或者 **通过 Bub contrib resolver 发布** 的包名（通常是 `name@branch`）。它 **不是** 面向任意发行包名的通用 PyPI 安装器。

默认情况下，agentseek 会把 `BUB_PROJECT` 设为 `{BUB_HOME}/agentseek-project`（因此可以用 `AGENTSEEK_PROJECT` 覆盖）。新沙箱会使用 `uv init --name agentseek-project`，而不是 `bub-project`。

如果你更想直接使用上游 Bub 入口，也可以执行 `bub install ...`；行为与 Hub 中的示例一致。

### 跳转到 agentseek Contrib Packages

Contrib packages 不在内置 `src/agentseek` 文档的覆盖范围里。它们各自的 README 才是安装命令、环境变量、插件 entry point 和示例的事实来源：

- [agentseek-observability](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-observability)
- [agentseek-tapestore-oceanbase](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase)
- [agentseek-langchain](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-langchain)
- [agentseek-schedule-sqlalchemy](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-schedule-sqlalchemy)

### 创建 agentseek 插件

如果用户没有特别要求其他位置，请把 agentseek 自己维护的插件放在 `contrib/agentseek-<feature>/`。

推荐遵循这些约定：

- distribution name: `agentseek-<feature>`
- Python package: `agentseek_<feature>`
- entry point group: `[project.entry-points.bub]`
- environment variables: 优先使用 `AGENTSEEK_*`，当设置映射到 Bub 运行时语义时也接受 `BUB_*`

当同一个设置同时支持两个前缀时，`BUB_*` 应该优先。这样既能保证插件在纯 Bub 场景下可用，也能让 agentseek 项目继续以 `AGENTSEEK_*` 作为文档中的主命名。

agentseek 内置了一个适配本仓库约定的 `plugin-creator` skill，用来帮助你按这些规则创建或更新 Bub-compatible plugin package。它沿用了上游 Bub contrib workflow 的整体形状，但针对本仓库里的 `contrib/agentseek-*`、内置 `src/skills` 以及 `AGENTSEEK_*` 别名行为做了专门化。

## 增加 Skills

Skills 用来教 agent 任务级行为。当扩展点只是操作流程、领域知识或 agent 应该调用的小脚本时，用 skill。只有当运行时本身需要新 hook、channel、store 或 tool 注册时，才改用 plugin。

### 安装项目级 Skills

项目级本地 skill 应安装在：

```text
.agents/skills/<skill-name>/SKILL.md
```

如果要从 registry 安装到 `.agents/skills`，可以使用和 [Bub Hub](https://hub.bub.build/) 一致的 `npx skills add`：

```bash
npx skills add psiace/skills --skill friendly-python
npx skills add bubbuild/bub-contrib --skill plugin-creator
```

这里适合放那些只属于当前仓库工作流、但不应该跟随 agentseek 包一起发布的能力。

本地 `agentseek` 运行可以立刻使用这条路径，因为 Bub 会自动从工作区发现项目级 skills。

在容器或 Compose 场景下，入口脚本也默认保留同样的 `.agents/skills` 约定，因此宿主机安装的 skills 可以直接复用。

### 内置发布级 Skills

如果某个 skill 应该随 agentseek 一起发布，请放在：

```text
src/skills/<skill-name>/SKILL.md
```

由于 `src/skills` 已经包含在构建输入里，内置 skills 会被打进 agentseek 包。

这类 skill 适合那些无论 agentseek 安装在哪里都应该可用的稳定通用行为，并且要和 agentseek 的扩展模型保持一致。

### 使用外部 Skill 源

构建系统也可以通过 `[tool.pdm.build].skills` 从外部仓库引入指定 skill。

这适合共享型上游 skill。若某个 skill 明显是 agentseek 定制能力，或已经按 agentseek 约定适配过，优先直接内置到 `src/skills`。

## 增加 MCP Servers

如果你想给运行时接入 MCP servers，`bub-mcp` 默认会从 `${BUB_HOME}/mcp.json` 读取 MCP 配置。在 agentseek 默认布局下，本地路径就是：

```text
.agentseek/mcp.json
```

如果你更想把 MCP 文件放在项目根目录，这种方式也可以直接工作：

```bash
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
uv run agentseek chat
```

在 Docker / Compose 里，入口脚本还多做了一层便利处理：它会自动从挂载工作区里发现 `.agents/mcp.json`，并把它链接到运行时 MCP 配置路径。如果你需要其他路径，请显式设置 `AGENTSEEK_MCP_CONFIG_PATH` 或 `BUB_MCP_CONFIG_PATH`。
