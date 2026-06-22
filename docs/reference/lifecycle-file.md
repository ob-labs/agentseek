---
title: Lifecycle File
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-22
sources:
  - src/agentseek/cli/lifecycle.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/duties.py"
---

# Lifecycle File

## File

`duties.py` — lifecycle file loaded from the generated project root.

## Metadata

| Name | Required | Description |
| --- | --- | --- |
| `AGENTSEEK` | yes | Lifecycle metadata dictionary. |
| `AGENTSEEK["version"]` | yes | Supported value: `1`. |

## Required tasks

| Task | Description |
| --- | --- |
| `dev` | Run local development. |
| `info` | Print project summary. |
| `doctor` | Check local readiness. |

## Optional tasks

Templates can define additional tasks. Run them with `agentseek task`.

## Errors

| Condition | Result |
| --- | --- |
| Missing `duties.py` | Exit code `2`. |
| Missing `AGENTSEEK` metadata | Exit code `2`. |
| Unsupported lifecycle version | Exit code `2`. |
| Missing required task | Exit code `2`. |
