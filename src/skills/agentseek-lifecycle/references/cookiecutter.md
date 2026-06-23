# Cookiecutter Reference

Sources:

- https://cookiecutter.readthedocs.io/en/stable/advanced/index.html
- https://pypi.org/project/cookiecutter/

## Role In AgentSeek Templates

AgentSeek-compatible templates use Cookiecutter to render editable projects from template variables.

Common shape:

```text
<template-root>/
  cookiecutter.json
  {{cookiecutter.project_slug}}/
    README.md
    .agentseek/lifecycle.toml
    ...
```

Some template collections also keep an index or registry file next to multiple templates. Update it only when the collection uses one.

## Template Variables

Put user-facing variables in `cookiecutter.json`:

```json
{
  "project_name": "My Agent App",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
  "author": "Your Name"
}
```

Prefer derived values for fields users should not answer manually. Cookiecutter evaluates templated context values, so slugs, package names, and display names can often be derived.

Use underscore-prefixed private variables for template-internal values that should not prompt the user. Preserve existing private variables unless you understand the template host that consumes them.

## Non-Interactive Rendering

`agentseek create <spec> --no-input` should render a useful project from defaults. Use it as the baseline template validation path.

When validating an unreleased template branch, pass it explicitly:

```bash
agentseek create <spec> --checkout <branch> --no-input
```

When adding a required variable:

- Give it a useful default in `cookiecutter.json`.
- Render with `--no-input`.
- Verify generated files contain the expected value.
- Avoid prompts for values that can be derived from existing context.

## Hooks

Cookiecutter supports pre-generation and post-generation hooks. Use hooks only for generation-time behavior that cannot be represented clearly with template files or variables.

Prefer normal template files when possible. Hooks are harder to test, can introduce platform assumptions, and run during project creation.

## Maintenance Checklist

- Keep `cookiecutter.json` defaults compatible with `--no-input`.
- Keep generated file names and directory names renderable from `cookiecutter` context.
- Keep generated README commands aligned with the generated lifecycle spec.
- Prefer explicit template variables over hidden string replacement in generated files.
- Render the template after changing variables, path names, hooks, or lifecycle specs.
