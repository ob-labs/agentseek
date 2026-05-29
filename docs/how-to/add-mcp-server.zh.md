---
title: 如何添加 MCP server
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# 如何添加 MCP server

当你需要通过 MCP 向 agent 暴露外部工具或服务时使用本指南。本页讲解
**如何编写一条条目**；如果要选择文件 **放在哪里**，请参考
`configure-mcp.md`。

## 前置条件

- 已安装 agentseek (`bub-mcp` 是核心依赖，`pyproject.toml:21`)。
- MCP server 本身在你的机器上可运行 (二进制、`uvx`
  包、`npx` 包等)。

## 步骤

1. 选择 (或创建) `mcp.json` 的位置。默认是
   `${BUB_HOME}/mcp.json`，按照 agentseek 默认值就是
   `.agentseek/mcp.json`。

2. 在 `mcpServers` 下添加一条 server 条目。结构与标准 MCP
   客户端配置一致：

   ```json title=".agentseek/mcp.json"
   {
     "mcpServers": {
       "fs": {
         "command": "uvx",
         "args": ["mcp-server-filesystem", "--root", "/workspace"],
         "env": {
           "LOG_LEVEL": "info"
         }
       },
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_fake_replace_me"
         }
       }
     }
   }
   ```

3. 重启任何正在运行的 `agentseek chat` / `agentseek gateway`，让 `bub-mcp`
   重新读取该文件。

   ```bash title="not executed in this run"
   uv run agentseek chat
   ```

### CLI 快捷方式

`agentseek mcp add` 可以替你写入同样的条目，而不必打开文件：

```bash
# 远端 (http / sse) server：
uv run agentseek mcp add github https://example.com/mcp \
  --transport http --header "Authorization: Bearer $TOKEN"

# stdio server（用 `--` 把后面的命令和 agentseek 自己的参数分开）：
uv run agentseek mcp add fs --transport stdio --env LOG_LEVEL=info \
  -- uvx mcp-server-filesystem --root /workspace
```

`uv run agentseek mcp list` 列出当前已注册的 server；`remove` 按名删除。
参见 `../reference/cli.md#agentseek-mcp`。

## 字段参考

| 字段 | 是否必填 | 描述 |
| --- | --- | --- |
| `command` | 是 | `PATH` 上的二进制，或 `uvx` / `npx` 之类的启动器。 |
| `args` | 否 | 传给 `command` 的参数列表。 |
| `env` | 否 | server 启动时额外设置的环境变量。 |

完整字段集由 `bub-mcp` 维护。本页与该 plugin 源码冲突时，以
plugin 为准。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 来自 server 的工具缺失 | spawn 默默失败 | 在 agentseek 之外手动运行 `command args`，让错误浮现。 |
| server 启动但鉴权失败 | `env` 中缺少 token | 在该 server 的 `env` 对象下添加凭据。 |

## 回退

从 `mcp.json` 中移除该 server 条目。重启进程。

## 相关

- 操作指南: `configure-mcp.md`, `configure-docker-workspace.md`
- 参考: `../reference/environment.md`
