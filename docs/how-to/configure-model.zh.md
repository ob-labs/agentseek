---
title: 如何配置模型 provider
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - README.md
  - docs/index.md
---

# 如何配置模型 provider

当你需要让 agentseek 指向特定 LLM (OpenRouter、OpenAI、
OpenAI 兼容 gateway、本地 server 等) 时使用本指南。agentseek 不
内置默认凭据；任何 chat turn 运行前都必须设置模型与密钥。

## 前置条件

- 一个可用的 **harness** 环境：要么是本仓库里 `uv sync` 之后的环境，
  要么是生成项目里各自 `uv sync` 之后的环境。单独安装 `agentseek-cli`
  并不提供 `chat`。
- 所选 provider 的有效 API key。

## 步骤

1. 选一个 Bub any-llm 层接受的模型标识。常见形式：
   `openrouter:<model>`、`openai:gpt-4o-mini`、`openai:<model>@<base_url>`。

2. 把配置写入项目根目录的 `.env`。agentseek 从当前工作目录
   加载 `.env` (`src/agentseek/env.py:38`)。

   ```bash title=".env"
   AGENTSEEK_MODEL=openrouter:moonshotai/kimi-k2:free
   AGENTSEEK_API_KEY=sk-or-v1-replace-me   # fake placeholder
   # Optional — only when your provider is not the model's default endpoint
   # AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
   ```

   `AGENTSEEK_*` 在启动时被别名映射为 `BUB_*` (`src/agentseek/env.py:56`)。
   如果进程环境里已经设置了 `BUB_*`，它会优先生效 —— 便于一次性
   覆盖。

3. 通过查看解析后的 help 验证别名映射生效 (这会读取
   `.env`)：

   ```bash
   uv run agentseek chat --help
   ```

   ```text title="output"
   Usage: agentseek chat [OPTIONS]
   ```

   没有 traceback 表示 `.env` 解析正常。

### CLI 快捷方式

不修改 `.env` 而按次覆盖：

```bash title="not executed in this run"
AGENTSEEK_MODEL=openai:gpt-4o-mini \
AGENTSEEK_API_KEY=sk-replace-me \
uv run agentseek chat
```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| provider 返回 `401 Unauthorized` | `AGENTSEEK_API_KEY` 缺失或失效 | 重新签发 key 并更新 `.env`；重启进程。 |
| 请求打到错误的端点 | 用 OpenAI 兼容 gateway 但未设置 `AGENTSEEK_API_BASE` | 把 `AGENTSEEK_API_BASE` 设为 gateway 的 `…/v1` URL。 |
| 设置被忽略 | shell 中已存在同名 `BUB_*` 变量 | `BUB_*` 通过 `setdefault` 优先 —— 取消或更新它。 |

## 回退

从 `.env` 删除相关行，或在 shell 中 `unset AGENTSEEK_MODEL AGENTSEEK_API_KEY`。
没有需要清理的磁盘状态。

## 相关

- 参考: `../reference/environment.md`
- 概念解释: `../explanation/bub-relationship.md`
