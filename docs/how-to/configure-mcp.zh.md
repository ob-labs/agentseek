---
title: 如何配置 MCP 服务器
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# 如何配置 MCP 服务器

当你希望 agent 通过 MCP 调用外部工具或服务时使用本指南。
agentseek 通过 `bub-mcp` 消费 MCP 配置，后者读取
`${BUB_MCP_CONFIG_PATH}` (默认: `${BUB_HOME}/mcp.json`) 处的文件。

## 前置条件

- 已安装 agentseek (`bub-mcp` 是核心依赖，`pyproject.toml:21`)。
- 至少有一个想注册的 MCP 服务器。

## 选择位置

| 你想要… | 把 `mcp.json` 放在 | 需要设置的变量 |
| --- | --- | --- |
| 将 MCP 放在 Bub 运行时状态旁 (默认) | `.agentseek/mcp.json` | 无 (默认) |
| 与项目的 `.agents/` skills 目录共置 | `.agents/mcp.json` | `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json` |
| 使用自定义位置 | 任意 | `AGENTSEEK_MCP_CONFIG_PATH=<path>` |

在 Docker 中，entrypoint 会自动发现 `${workspace}/.agents/mcp.json` 并
把它 symlink 到 `${AGENTSEEK_HOME}/mcp.json` (`entrypoint.sh:13`, `:37`)。

## 步骤

1. 编写 MCP server 文件。条目格式见 [如何添加 MCP 服务器](add-mcp-server.zh.md)。

   ```json title=".agentseek/mcp.json"
   {
     "mcpServers": {
       "echo": {
         "command": "uvx",
         "args": ["mcp-server-echo"]
       }
     }
   }
   ```

2. 如果选择了非默认位置，设置路径：

   ```bash title=".env"
   AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
   ```

3. 通过运行一次 chat session 验证文件被读取。

   ```bash title="not executed in this run"
   uv run agentseek chat
   ```

### CLI 快捷方式

`agentseek mcp` 子命令可以替你管理已解析到的 `mcp.json` 中的条目，
不必再手工编辑文件：

```bash
uv run agentseek mcp list
uv run agentseek mcp add <name> <target> --transport <http|sse|stdio>
uv run agentseek mcp remove <name>
```

完整的参数列表见 [CLI 参考](../reference/cli.zh.md)。文件路径仍由上文所述的
`AGENTSEEK_MCP_CONFIG_PATH` 控制，CLI 只是写穿该路径。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| MCP server 没出现在 `tools/list` 中 | `mcp.json` 在 Bub 不读取的路径上 | 把 `AGENTSEEK_MCP_CONFIG_PATH` 设为文件路径。 |
| 对 `mcp.json` 的修改没有生效 | 进程在编辑之前就启动了 | 重启 `agentseek chat` / `agentseek gateway`。 |

## 回退

删除 `mcp.json` 文件。如果设置过 `AGENTSEEK_MCP_CONFIG_PATH`，取消设置。

## 相关

- 操作指南: [如何添加 MCP 服务器](add-mcp-server.zh.md), [如何配置 Docker workspace](configure-docker-workspace.zh.md)
- 参考: [环境变量参考](../reference/environment.zh.md), [Docker 参考](../reference/docker.zh.md)
