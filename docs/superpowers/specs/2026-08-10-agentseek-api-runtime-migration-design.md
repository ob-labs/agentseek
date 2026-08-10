# AgentSeek API Runtime Migration Design

## Goal

将 AgentSeek 及其模板的本地 backend 运行时统一迁移到 `uv run agentseek-api dev`，保留现有 lifecycle 配置、工作目录、环境变量、端口、HTTP 检查和子进程监督行为。

## Current implementation findings

- AgentSeek 的 `agentseek dev` 入口最终进入 `src/agentseek/cli/lifecycle/core.py` 的 `dev()`。
- backend 命令来自生成项目的 `.agentseek/lifecycle.toml` 的 `[processes.backend].command`，不是 AgentSeek CLI 中硬编码的 `langgraph dev`。
- AgentSeek 的 dry-run、info、doctor 和 live doctor 均由 lifecycle spec 驱动；进程启动、等待、终止由 lifecycle process-group 实现。
- AgentSeek API 的 `dev` 命令在 `src/agentseek_api/cli.py` 中自行组装并运行 uvicorn，支持 `--host`、`--port`、`--config`、`--env-file`，reload 通过 `--no-reload` 控制。
- AgentSeek API 可读取 `agentseek.json` 和 `langgraph.json`，并设置 `AGENTSEEK_GRAPHS` 给运行时。

## Architecture

模板 lifecycle spec 是唯一的项目启动协议。每个 backend process 声明 `uv run agentseek-api dev` 及模板需要的参数；AgentSeek CLI 只负责解析、检查、启动、监督和停止声明的进程，不实现第二套 runtime。

模板继续使用兼容的 graph 配置结构，优先保留 `langgraph.json`；只有在 AgentSeek API 语义确实要求时才迁移为 `agentseek.json`。模板依赖显式加入 `agentseek-api`，并同步 lockfile。

## Component changes

### AgentSeek

- 增强 lifecycle backend/runtime 描述，使 `info`（包括 JSON 输出）显示 `agentseek-api`，且不泄露环境变量值。
- 让 doctor 静态检查确认 `agentseek-api` 可执行文件、graph 配置、必要路径和环境变量。
- 保持现有 cwd、env file、host/port、reload 参数、frontend/backend 关系以及进程失败和停止处理。
- 增加 dry-run、info、doctor、live doctor、端口/进程失败场景的回归测试。

### Templates

- 扫描所有模板和模板生成文件，替换 backend 启动命令及当前文档中的旧启动方式。
- 为每个实际运行 backend 的模板加入 `agentseek-api` 依赖并更新 lockfile。
- 验证 graph 配置、环境样例、frontend backend URL 和文档的一致性。
- 先验证一个最小模板，再批量处理其余模板。

### AgentSeek API

- 先使用现有 CLI 和配置加载能力验证最小模板。
- 只有当问题被证明属于 runtime 能力缺口时，才修改 CLI、配置加载、HTTP API 或集成测试；不得增加调用 `langgraph dev` 的兼容层。

## Error handling

- 缺少 `agentseek-api`、graph 配置、依赖路径或必需环境变量时，在启动前由 doctor/启动前检查给出明确修复提示。
- backend 进程启动失败、提前退出或端口冲突时保留现有进程监督错误路径，并明确指出 backend 命令和 URL。
- `doctor --live` 只通过 lifecycle 配置中的 HTTP endpoint 检查服务，不通过进程名判断。

## Verification

按顺序验证：AgentSeek CLI 单元测试；最小模板生成、info、doctor、dry-run 和真实启动；必要时 AgentSeek API CLI/配置/API 测试；全部模板扫描和逐模板生成检查；三个仓库最终搜索不得把 `langgraph dev` 或 `uv run langgraph dev` 作为当前启动方式。

## Scope decisions

- LangGraph Python 库和 SDK 只要仍被 graph 或 frontend 使用则保留。
- `langgraph.json` 作为 graph 配置文件不因名称本身删除；它与 runtime 启动命令分开处理。
- 文档中的历史迁移说明若保留，必须明确标为旧版本行为，不能作为当前操作方式。
