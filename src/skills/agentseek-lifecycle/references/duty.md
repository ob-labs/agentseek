# Duty Reference

Sources:

- https://pawamoy.github.io/duty/usage/
- https://pypi.org/project/duty/

## Role In AgentSeek Projects

AgentSeek-compatible projects define lifecycle tasks in `duties.py` using Duty. AgentSeek invokes those tasks through its public CLI.

Basic task shape:

```python
from duty import duty


@duty
def doctor(ctx, strict: bool = False):
    """Check local project readiness."""
    del ctx
```

## Task Authoring Rules

- Keep required lifecycle tasks named `doctor`, `dev`, and `info`.
- Use clear Python parameters for task options.
- Annotate boolean parameters as `bool` or give them boolean defaults.
- Raise `SystemExit(code)` when a lifecycle task must fail.
- Keep long-running or interactive tasks marked with `capture=False`.

Example:

```python
@duty(capture=False)
def dev(ctx, dry_run: bool = False):
    """Run the local app."""
    del ctx
```

## Argument Forwarding

Duty CLI task parameters use `param=value` style. AgentSeek follows that style for `agentseek task`.

Examples:

```bash
agentseek task --list
agentseek task doctor strict=true
agentseek task dev dry_run=true
```

Use conventional boolean strings:

- true values: `1`, `true`, `yes`, `on`
- false values: `0`, `false`, `no`, `off`

## Output Capture

Duty captures output by default. For tasks that launch servers, prompt users, or need live output, use `@duty(capture=False)`.

Use `ctx.run([...])` for subprocess commands when argument boundaries matter. Use shell strings only when shell behavior is intentional.

## Maintenance Checklist

- Keep generated `duties.py` importable without starting services.
- Keep readiness checks deterministic and fast.
- Keep `dev(dry_run=True)` side-effect free.
- Keep process cleanup explicit for long-running tasks.
- Keep task docstrings short because they can appear in task help.
