---
hide_sidebar: true
---

# agentseek

agentseek 是一个面向团队的数据库原生 Agent Harness，适合那些希望把 agent
运行时数据变成一等数据库工作负载的场景。

它把 agent 上下文、执行历史、工具调用、任务、反馈和观测数据放到同一个可持久、
可查询的数据库底座上。

## 快速开始

选一条路径即可：要项目生命周期命令就安装 `agentseek-cli`，要直接运行 harness
CLI 就克隆仓库并运行 `agentseek`。如果需要看两条路径的取舍，直接读
[选择一个入口](explanation/choosing-an-entry-point.zh.md)。

### 路径 A —— 安装项目生命周期 CLI

需要生成项目，或者不克隆仓库就调用生命周期命令时，走这条。

```bash
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync                     # 生成项目内部的 [tool.uv.sources] 会解析出完整 harness
```

### 路径 B —— 克隆仓库，运行 harness

需要直接运行 harness CLI 本体 —— `chat`、`gateway`、`install` 等 —— 时走这条。

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

然后配置模型并启动本地会话：

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

> 注意：`pip install agentseek` 与 `uv tool install agentseek` 都会解析失败，
> 因为它们不能正确解析 harness。请使用上面两条路径之一。

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
