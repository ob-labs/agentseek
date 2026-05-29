---
title: 如何添加 skill
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-05-28
sources:
  - pyproject.toml
  - entrypoint.sh
---

# 如何添加 skill

当扩展属于 **指令或工作流知识** —— 一个 `SKILL.md` 文件加上可选脚本 ——
而不是新的运行时 hook 时使用本指南。如果你需要注册新的 channel、store 或
tool，请改用 [How to install a plugin](install-a-plugin.md)。

## 选择作用域

| 作用域 | 路径 | 何时使用 |
| --- | --- | --- |
| 项目本地 | `.agents/skills/<name>/SKILL.md` | 仓库专属行为。不随包发布。 |
| 随发布版本捆绑 | `src/skills/<name>/SKILL.md` | 任何安装了 `agentseek` 的地方都应该存在的行为。通过 `pyproject.toml:74` 进入 wheel。 |
| 外部 (构建时引入) | `pyproject.toml:78` 中的 `[tool.pdm.build].skills` | 构建时从其他仓库拉取选定的 skill。 |

Bub 从 `.agents/skills/` 发现项目本地 skill。Docker
entrypoint 默认遵循该约定，并把其他位置 symlink 到同一路径
(`entrypoint.sh:30`–`:35`)。

## 步骤 — 安装项目本地 skill

1. 创建 skill 目录与最小化 `SKILL.md`：

   ```bash
   mkdir -p .agents/skills/my-skill
   ```

   ```markdown title=".agents/skills/my-skill/SKILL.md"
   # my-skill

   When to use: <describe trigger>.
   Steps:
   1. ...
   ```

2. 该 skill 会在下一次 `agentseek chat` / `agentseek gateway` 时被加载。
   无需重启任何 sandbox。

### CLI 快捷方式 — 从 registry 安装

`agentseek skills` 封装了上游 `vercel-labs/skills` CLI (通过
`npx` 运行)。子命令: `add`, `list`, `find`, `update`, `remove`, `init`。

```bash title="not executed in this run"
uv run agentseek skills --dir . add psiace/skills --skill friendly-python
```

## 步骤 — 捆绑一个发布版 skill

1. 将 skill 放在 `src/skills/<name>/SKILL.md` 下。`pyproject.toml:74`
   已经把 `src/skills` 包含进 wheel。

2. 构建 wheel 并确认 skill 出现：

   ```bash title="not executed in this run"
   uv build
   ```

3. 此后任何安装了 `agentseek` 的地方都能使用该 skill。

## 步骤 — 在构建时引入外部 skill

编辑 `pyproject.toml:78` 中的 `[tool.pdm.build].skills`，指向源仓库、
子路径以及你想要的 skill 子集：

```toml title="pyproject.toml"
[tool.pdm.build]
skills = [
  { git = "https://github.com/PsiACE/skills.git", subpath = "skills", include = ["friendly-python", "piglet"] },
]
```

`pdm-build-skills` 后端会在构建时解析这些条目。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| skill 从未被调用 | `SKILL.md` 的触发描述与任务不匹配 | 收紧 "When to use" 行。 |
| 安装后看不到 `src/skills/` 中的 skill | 从源码安装但未重新构建 | 再次执行 `uv sync` 或 `uv build`。 |
| 容器忽略宿主机 skill | `AGENTSEEK_SKILLS_HOME` 指向非默认路径，而 Bub 在扫描 symlink | 确认 `${workspace}/.agents/skills` 存在 symlink (`entrypoint.sh:33`)。 |

## 回退

删除 `.agents/skills/` 或 `src/skills/` 下的 skill 目录。如果是捆绑的，
请重新构建。

## 相关

- 操作指南: [How to install a plugin](install-a-plugin.md), [How to author a contrib plugin](author-a-contrib-plugin.md)
- 参考: [Packages reference](../reference/packages.md), [File layout reference](../reference/file-layout.md)
- 项目规约: [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md)
