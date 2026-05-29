---
hide_sidebar: true
---

# agentseek

一个由 OceanBase OSS Team 提供的数据库原生 Agent Harness。

agentseek 是一个面向团队的数据库原生 Agent Harness，适合那些希望把 agent
运行时数据变成一等数据库工作负载的场景。

它把数据库视为承载 agent 上下文、执行历史、工具调用、任务、反馈和观测数据的
自然位置。这样，同一份运行时数据就可以直接服务于调试、回放、轨迹对比、评估、
分析和训练工作流，而不需要复制到多个系统中，也不需要事后重新导入。

## 两个包，两条路径

agentseek 在 PyPI 上以两个互补的包提供，按职责拆分：

- **`agentseek-cli`** —— 项目生命周期 CLI：`create`、`run`、`build`、`deploy`、
  `api`、`ctx`、`skills`。自包含，使用 `uv tool install agentseek-cli` 安装。
- **`agentseek`** —— harness 本体：`chat`、`run`、`gateway`、`install`、
  `update`，以及嵌入到你应用里的库。harness 通过本仓库的 `[tool.uv.sources]`
  解析，不能直接 `pip install agentseek`。

两者都注册名为 `agentseek` 的命令。如果你需要先判断该走哪条路径，直接读
[选择一个入口](explanation/choosing-an-entry-point.zh.md)。

## 为什么存在

大多数 agent 的价值都体现在运行时，但它们的 runtime data 很快就会散落到
日志、笔记、本地数据库、tracing 系统、对象存储和离线流水线里。第一次交互
之后，重放、对比、评估和训练这些工作就会明显变贵。

agentseek 从相反的前提出发：context、memory、task、tool call、trace、
feedback 和评估材料，从一开始就应该共享同一个持久底座。

对 agent 系统来说，这让运行时数据具备复用价值；对数据库来说，这意味着它不再
只存放最终业务结果，而是可以直接承载智能应用的工作负载。

## 快速开始

两条入门路径都正式平等，按你的目的二选一。

### 路径 A —— 安装项目生命周期 CLI

需要生成项目、构建镜像、调用生命周期命令但不想把仓库克隆下来时，走这条。

```bash
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync                     # 生成项目内部的 [tool.uv.sources] 会解析出完整 harness
```

### 路径 B —— 克隆仓库，运行 harness

需要驱动 harness 本体 —— `chat`、`gateway`、`install` 等运行时命令 —— 时走这条。

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

先配置一个模型，再启动本地会话：

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

> 注意：`pip install agentseek` 与 `uv tool install agentseek` 都会解析失败，
> 因为 harness 依赖 `bub-feishu`、`bub-mcp` 和通过 `[tool.uv.sources]`
> 接入的 workspace contrib 包。请使用上面两条路径之一。

## 接下来读什么

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="docs/">文档</a></h3>
    <p>说明 agentseek 是什么、处在什么位置，以及整套文档的组织方式。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="tutorials/">教程</a></h3>
    <p>从这里开始：快速 CLI 演示、第一个 harness 应用、添加 skill 与 MCP。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">操作指南</a></h3>
    <p>以任务为中心的食谱，涵盖模型配置、插件安装、运行与部署。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">参考</a></h3>
    <p>环境变量、CLI 命令、包、文件布局、模板和 Docker。</p>
  </div>
</div>
