---
name: bubseek-bootstrap
description: Bubseek distribution bootstrap skill. Use when you need to inspect bundled contrib packages and initialize a Bub workspace with bundled conventions.
---

# Bubseek Bootstrap

Use this skill when a task is about bootstrapping a Bubseek workspace.

## Bundle Layout

- Skills root: `skills/`
- Config: `bubseek.toml`
- Lock: `bubseek.lock`
- Source catalog: `https://github.com/bubbuild/bub-contrib`

## Minimal Workflow

1. Keep Bub runtime commands unchanged through wrapper forwarding (`bubseek chat`, `bubseek run`, `bubseek message`).
2. Edit contrib and skills sources in `bubseek.toml`.
3. Generate `bubseek.lock` via `bubseek lock`.
4. Apply lock to environment/workspace via `bubseek sync`.
