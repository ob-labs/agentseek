---
title: 如何添加 skill
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-12
sources:
  - pyproject.toml
  - entrypoint.sh
---

# 如何添加 skill

当你要用 `SKILL.md` 添加指令或工作流知识时使用本页。

## 添加项目 skill

1. 创建 skill 目录。

   ```bash
   mkdir -p .agents/skills/my-skill
   ```

2. 写入 skill 说明。

   ```markdown title=".agents/skills/my-skill/SKILL.md"
   # my-skill

   When to use: <describe trigger>.
   Steps:
   1. ...
   ```

3. 启动新的 runtime 进程。

   ```bash
   uv run agentseek chat
   ```

项目本地 skill 放在 `.agents/skills/<name>/`。只有需要随包发布时，才放在
`src/skills/<name>/`。

### CLI 快捷方式

已有 registry skill 时，可以直接安装：

```bash
agentseek skills add --all --global
agentseek skills add --skill langsmith-trace --global --yes
agentseek skills add langchain-ai/langsmith-skills --skill '*' --yes
```

## 捆绑发布版 skill

把 skill 放到 `src/skills/<name>/SKILL.md`，然后构建包。

```bash
uv build
```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| skill 从未运行 | 触发描述太模糊。 | 收紧 "When to use" 行。 |
| 发布版 skill 缺失 | 包没有重新构建。 | 再次运行 `uv build`。 |
| 容器内没有宿主机 skill | 容器指向了其他 skills 路径。 | 设置 `AGENTSEEK_SKILLS_HOME=/workspace/.agents/skills`。 |

## 回退

删除该 skill 目录。如果删除的是捆绑 skill，重新构建包。

## 相关

- 操作指南: [如何安装插件](install-a-plugin.zh.md), [如何编写 contrib 插件](author-a-contrib-plugin.zh.md)
- 参考: [包参考](../reference/packages.zh.md), [文件布局参考](../reference/file-layout.zh.md)
- 项目规约: [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md)
