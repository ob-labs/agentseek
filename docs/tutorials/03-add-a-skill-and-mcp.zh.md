---
title: 03 —— 添加一个 skill 和一个 MCP server
type: tutorial
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - .agents/skills/local-greeting/SKILL.md
  - .agents/mcp.json
---

# 添加一个 skill 和一个 MCP server

> **你将完成：** 把一个项目本地的 skill 放进 `.agents/skills/<name>/SKILL.md`，在 `.agents/mcp.json` 里声明一个 MCP server，并确认 agent 把两者都识别了。
> **你需要：** [02 —— 构建你的第一个 harness 应用](02-first-harness-app.zh.md) 生成的项目（或任意一个 agentseek workspace）和 `uv`。`bub-mcp` 已包含在 `agentseek` 中，无需额外安装。

本教程涵盖的是每个 harness app 最终都会长出来的运维形态：*这个 workspace 里有些东西，agent 应该感知到，而我不想手工把它们写进 Python 代码*。Skill 处理指令/playbook 这一类；MCP server 处理工具和实时数据源。

## 1. 写一个项目本地的 skill

项目本地的 skill 位于 `.agents/skills/<skill-name>/SKILL.md`。Bub 会自动从 workspace 发现它们 —— 不需要装 plugin，也不用跑 CLI 命令。最小形态是一个 front-matter 块加一段正文，从本 checkout 的 `.agents/skills/local-greeting/SKILL.md` 复制如下：

```markdown
---
name: local-greeting
description: Return a short greeting for quick smoke tests of a custom Bub skill.
---

Return exactly one sentence.
If the workspace path is available, mention it briefly.
```

在项目根目录创建该目录和文件：

```bash
mkdir -p .agents/skills/local-greeting
$EDITOR .agents/skills/local-greeting/SKILL.md
```

把上面的片段粘进文件保存。`name` 字段是 agent 用来调用该 skill 的名字；`description` 是模型在决定是否使用时看到的描述。

确认 skill 可见：

```bash
uv run agentseek skills list
```

```text title="expected output"
Project Skills

documentation-writer ~/oceanbase/agentseek/.agents/skills/documentation-writer
  Agents: Codex, Cursor
local-greeting ~/oceanbase/agentseek/.agents/skills/local-greeting
  Agents: Codex, Cursor
github-repo-cards ~/oceanbase/agentseek/skills/github-repo-cards
  Agents: OpenClaw
langchain-cn-models ~/oceanbase/agentseek/skills/langchain-cn-models
  Agents: OpenClaw
```

你那条 `local-greeting` 应当出现在 **Project Skills** 下。`Agents:` 列显示哪些客户端已经接好该 skill —— 你生成的 app 不需要额外接线，因为 Bub 直接读取 workspace 中的 skill。

> **自带 vs 项目本地。** `src/skills/` 随 agentseek 发行版一起提供（上面下两行就是）。`.agents/skills/` 是你编写自己 skill 的位置。请在那里编写，不要修改 `src/skills/`。完整分类见[如何添加 skill](../how-to/add-skills.zh.md)。

## 2. 声明一个 MCP server

`bub-mcp` 默认读取 `${BUB_HOME}/mcp.json`。按 agentseek 的默认设置，它会解析到 `.agentseek/mcp.json`。如果你更喜欢项目根目录的约定（`.agents/mcp.json`），请在启动 runtime 前设置 `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json`。

两个文件结构相同。本 checkout 中的（`.agents/mcp.json`）是规范的最小示例：

```json
{
  "mcpServers": {
    "time": {
      "type": "streamable_http",
      "url": "https://mcp.api-inference.modelscope.net/<your-id>/mcp"
    }
  }
}
```

把 `<your-id>` 换成你的 MCP host 分配给你的路径。对于基于 stdio 的 server（例如本地脚本），使用：

```json
{
  "mcpServers": {
    "my-tools": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "my_package.mcp_server"]
    }
  }
}
```

把文件放到你这套配置对应的路径：

```bash
# project-root style (recommended for harness apps)
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json

# or accept the agentseek default
mkdir -p .agentseek && $EDITOR .agentseek/mcp.json
```

完整的 MCP 相关变量清单在 [环境变量参考](../reference/environment.zh.md)；两个位置之间的取舍见 [如何配置 MCP 服务器](../how-to/configure-mcp.zh.md)。

## 3. 看 agent 把它们识别出来

从你的项目重启 gateway，让新的 skill 和 MCP 条目被加载：

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel ag-ui
```

启动时 gateway 会把它发现的每个 skill 和它连上的每个 MCP server 都记到日志里。通过你的前端（或在项目根目录用 `uv run agentseek chat`）发一条应当触发其中之一的 prompt：

- *"Greet me as the local-greeting skill"* —— 模型应当调用 `local-greeting`，返回一句话回复，并提到 workspace 路径。
- *"What time is it right now?"* —— 如果 `time` MCP server 可达，模型应当调用它的工具并返回结果。

如果某个 skill 没被识别，再跑一次 `uv run agentseek skills list`，确认你那一行出现了。如果某个 MCP server 没被识别，确认文件路径与 `AGENTSEEK_MCP_CONFIG_PATH` 完全一致。

## 你现在拥有什么

- 在 `.agents/skills/local-greeting/SKILL.md` 一个项目本地 skill，能被 `agentseek skills list` 列在 **Project Skills** 之下。
- 在 `.agents/mcp.json`（或 `.agentseek/mcp.json`）一份 MCP 配置文件，至少声明了一个 server；如果你选了项目根路径，还设置了 `AGENTSEEK_MCP_CONFIG_PATH`。
- 脑子里清楚地分开了 **skill**（模型可以读的指令）和 **MCP server**（模型可以调用的实时工具）。

## 接下来去哪

- 想用 Bub 兼容的 Python plugin（而不是 skill 或 MCP），看 [如何安装插件](../how-to/install-a-plugin.zh.md)。
- 决策矩阵 —— 什么时候选 skill、MCP server 还是 contrib plugin —— 见 [扩展模型](../explanation/extension-model.zh.md)。
- `agentseek skills` 透传给 `npx-skills` 的全部内容，见 [CLI 参考](../reference/cli.zh.md)。
- `AGENTSEEK_*` 变量及其 `BUB_*` 别名的完整清单，见 [环境变量参考](../reference/environment.zh.md)。
