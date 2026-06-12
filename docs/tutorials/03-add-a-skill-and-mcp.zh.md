---
title: 03 — 添加一个 skill 和一个 MCP server
type: tutorial
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - .agents/skills/local-greeting/SKILL.md
  - .agents/mcp.json
---

# 添加一个 skill 和一个 MCP server

你会在[第一个 harness 应用教程](02-first-harness-app.zh.md)生成的项目中，
添加一个项目本地 skill 和一个 MCP server 声明。

Skill 给模型项目内的指令。MCP server 给 runtime 工具访问能力。

## 1. 添加本地 skill

在生成项目根目录运行：

```bash
mkdir -p .agents/skills/local-greeting
cat > .agents/skills/local-greeting/SKILL.md <<'EOF'
---
name: local-greeting
description: Return a short greeting for quick smoke tests of a custom Bub skill.
---

Return exactly one sentence.
If the workspace path is available, mention it briefly.
EOF
```

runtime 启动时会从 `.agents/skills/` 发现项目本地 skills。

## 2. 添加 MCP 配置

创建 `.agents/mcp.json`：

```bash
mkdir -p .agents
cat > .agents/mcp.json <<'EOF'
{
  "mcpServers": {
    "time": {
      "type": "streamable_http",
      "url": "https://mcp.api-inference.modelscope.net/<your-id>/mcp"
    }
  }
}
EOF
```

把 `<your-id>` 换成你的 MCP host 分配的路径。然后让 AgentSeek 读取这个文件：

```bash
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
```

runtime 还需要安装 MCP 支持。如果这个项目还没有包含它，按
[配置 MCP server](../how-to/configure-mcp.zh.md) 处理。

## 3. 重启 runtime

```bash
uv run agentseek gateway --enable-channel ag-ui
```

尝试会用到新能力的 prompt：

- `Greet me as the local-greeting skill.`
- `What time is it right now?`

如果 skill 没有被使用，确认 `.agents/skills/local-greeting/SKILL.md` 存在，
然后重启 runtime。如果 MCP tool 不可用，确认 `AGENTSEEK_MCP_CONFIG_PATH`
指向刚创建的文件。

## 你现在拥有

- `.agents/skills/` 下的项目本地 skill。
- `.agents/mcp.json` 中的 MCP server 声明。
- 一个可以先通过指令和工具增长、而不是先改应用代码的项目。

## 下一步

- 添加更多 skills：[如何添加 skills](../how-to/add-skills.zh.md)。
- 配置更多 MCP servers：[配置 MCP servers](../how-to/configure-mcp.zh.md)。
- 选择扩展类型：[扩展模型](../explanation/extension-model.zh.md)。
