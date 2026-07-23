---
title: Lifecycle v2 服务发现
type: reference
audience: [A2, A3, A5]
runs: no
verified_on: 2026-07-21
sources:
  - specs/lifecycle-v2-service-discovery.md
  - docs/adr/0001-versioned-template-catalog-boundary.md
---

# Lifecycle v2 服务发现

> **简述：** Lifecycle v2 是一份已接受的编写契约，用于描述服务、服务关系
> 和安全的用户操作。AgentSeek 将其投影为确定性的 JSON，供 Desktop 和其他
> 机器消费者使用。

规范性文档以
[Desktop Service Discovery and Lifecycle v2](https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md)
为准。它已被接受为 AgentSeek 0.1.0 的设计，AgentSeek 0.0.5 尚未提供这些行为。

## 契约范围

| 范围 | 提案规定的内容 |
| --- | --- |
| Lifecycle v2 编写格式 | 精简的服务标识、类型、展示提示、主服务、参考链接，以及显式的关系例外。 |
| 归一化项目模型 | 从相互独立的 lifecycle v1、v2 输入投影得到同一个安全内部模型。 |
| `agentseek info --json` | 确定性的项目、服务、检查、任务、参考链接和操作元数据。 |
| `agentseek doctor [--live] --json` | 带稳定标识和退出行为的类型化静态、实时诊断结果。 |
| 安全边界 | 公共 JSON 不包含命令、机密、环境变量值、不安全路径或不安全端点。 |
| 兼容性 | 现有 v1 项目仍可加载；v1 JSON 保持保守，并明确标记为不完整。 |

模板归属和发布兼容性另见
[ADR 0001（英文）](../adr/0001-versioned-template-catalog-boundary.md)。

## 设计讨论

问题和设计历史请记录在
[GitHub Discussion #133](https://github.com/ob-labs/agentseek/discussions/133)。
规范性变更必须同步到正式提案，不能只保留在讨论评论中。
