---
name: agentseek-lifecycle
description: "Use when helping with AgentSeek-managed projects or AgentSeek-compatible templates: create projects, diagnose lifecycle issues, run doctor/dev/info/task commands, edit lifecycle specs, or maintain Cookiecutter template inputs. Prefer public AgentSeek CLI and template contracts."
---

# AgentSeek Lifecycle

## Core Workflow

1. Identify the workspace shape:
   - Generated project: look for `.agentseek/lifecycle.toml`, `.env.example`, `pyproject.toml`, frontend files, and project README.
   - Template project: look for `cookiecutter.json`, rendered `{{ cookiecutter... }}` paths, generated lifecycle specs, and template README.
2. Work through the public lifecycle surface:
   - `agentseek create`
   - `agentseek doctor`
   - `agentseek dev`
   - `agentseek info`
   - `agentseek task`
3. Treat `.agentseek/lifecycle.toml` as the compatibility contract between a generated project and AgentSeek.
4. Keep changes narrow:
   - Update generated instructions when lifecycle behavior changes.
   - Preserve non-interactive template rendering.
   - Use AgentSeek commands and project files as the validation surface.
5. Validate with public commands whenever possible.

## Load References

- For lifecycle specs, task expectations, and public validation commands, read `references/agentseek-lifecycle.md`.
- For template variables, rendering, `--no-input`, private variables, hooks, and template maintenance, read `references/cookiecutter.md`.

## Default Validation

For a generated project:

```bash
agentseek info
agentseek doctor
agentseek dev --dry-run
agentseek task --list
```

For a template project, render with defaults into a temporary directory, then run the generated project's lifecycle checks:

```bash
tmpdir="$(mktemp -d)"
cd "$tmpdir"
agentseek create <type>/<name> --no-input
cd <generated-project>
agentseek info
agentseek doctor
agentseek dev --dry-run
```

If the template lives on a branch that is not the template repository's default branch, pass the branch explicitly:

```bash
agentseek create <type>/<name> --checkout <branch> --no-input
```

If the repository provides its own test or lint commands, run the smallest relevant set after the public lifecycle check.
