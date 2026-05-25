# agentseek-cli

Project-lifecycle CLI for AgentSeek. Ships an `agentseek` console script
that can run on its own via `uvx`, **and** registers the same command groups
as a Bub plugin on the main `agentseek` framework CLI.

## At A Glance

| Field                | Value                                       |
| -------------------- | ------------------------------------------- |
| Distribution name    | `agentseek-cli`                             |
| Python package       | `agentseek_cli`                             |
| Bub entry point      | `cli` (`agentseek_cli.plugin:main`)         |
| Console script       | `agentseek` (`agentseek_cli.standalone:app`)|
| Install path         | `pip install agentseek-cli` / `uvx agentseek-cli` |
| Test target          | `make test-agentseek-cli`                   |

Top-level command groups: `create`, `run`, `build`, `deploy`, `api`,
`skills`.

## When To Use It

Use `agentseek-cli` when you want a single front door for AgentSeek project
work — scaffold a project, run it locally, build & deploy it, install
shared skill packs, and forward to the optional `agentseek-api` runtime —
without committing your environment to the full `agentseek` framework.

This package does **not** own:

- The `agentseek` framework runtime (lives in `src/agentseek`).
- The Bub plugin model itself.
- Skill content. Skills are pulled from the upstream
  `vercel-labs/skills` ecosystem through
  [`npx-skills`](https://pypi.org/project/npx-skills/).
- The `agentseek-api` runtime; `agentseek api` is a thin passthrough
  to it.

## Install

### Standalone (uvx)

```bash
uvx agentseek-cli --help
# or pin to this repo's working copy
uvx --from ./contrib/agentseek-cli agentseek --help
```

Under uvx the package is installed in an isolated environment, so its
`agentseek` console script does not collide with the main framework's
script.

### As part of the AgentSeek monorepo

The root `pyproject.toml` ships `agentseek-cli` as a workspace member and
as the optional `cli` extra:

```bash
uv sync                    # editable workspace install
uv pip install 'agentseek[cli]'   # explicit extra
```

When installed alongside the main `agentseek` package, the framework's
own `agentseek` script wins and this package's command groups are mounted
through the Bub `register_cli_commands` hook.

## Configure

`agentseek-cli` has no configuration of its own. The forwarded tools have
their own settings:

- `npx-skills` honors flags forwarded by `agentseek skills` (see
  [vercel-labs/skills](https://github.com/vercel-labs/skills)).
- `agentseek-api` reads its own environment / config when invoked through
  `agentseek api`.

The only CLI-level option exposed by this package is
`agentseek skills --dir <path>`, which `chdir`s before delegating.

## Run

```bash
# discover the surface
agentseek --help
agentseek skills --help
agentseek api --help

# skills (functional; requires uvx on PATH and a platform-supported
# npx-skills wheel)
agentseek skills add vercel-labs/agent-skills --list
agentseek skills add vercel-labs/agent-skills -s frontend-design -a claude-code -y
agentseek skills list
agentseek skills find typescript
agentseek skills update
agentseek skills remove frontend-design

# api passthrough (requires agentseek-api in the env)
agentseek api version
agentseek api dev --port 9911

# create — scaffold a project from a bundled cookiecutter template
agentseek create                                  # interactive type + template
agentseek create deepagents                       # default template (no prompt for type)
agentseek create langchain --list-templates       # list templates under a type
agentseek create --list-templates                 # list every bundled template
agentseek create bub --template default --no-input

# stubs (surface only in v1)
agentseek run
agentseek build
agentseek deploy --dry-run --mode docker-compose
```

## Runtime Behavior

- **Dual entrypoints.** Both the standalone `agentseek` console script
  (`agentseek_cli.standalone:app`) and the Bub plugin
  (`agentseek_cli.plugin:main`) call `agentseek_cli.app.build_app()`
  / `iter_command_groups()`, so the surface stays in lockstep.
- **Idempotent plugin mount.** `register_cli_commands` skips any group
  whose name is already attached to the root Typer, matching the existing
  pattern in `agentseek-langchain`. It additionally skips
  `FRAMEWORK_OWNED_NAMES` (currently `{"run"}`) because Typer silently
  overwrites duplicate group names and the framework's own built-in
  `run` (driven by `bub.builtin.cli`) is far more useful than this
  package's v1 stub. `agentseek run` therefore behaves like:
  - under `uvx agentseek-cli` (framework absent) — our v1 "coming soon" stub;
  - under monorepo / shared env (framework present) — the framework's
    `run` ("Run one inbound message through the framework pipeline").
- **`skills` is a thin pass-through.** It invokes
  `uvx npx-skills <subcommand> [...args]`. `npx-skills` ships its own
  Node runtime, so no global Node install is required, but `uvx`
  (shipped with `uv`) must be on `PATH`.
- **`api` migrated from `agentseek-langchain`.** The same Protocol-based
  duck-typing forwards `dev / serve / dockerfile / build / up / version`
  to `agentseek_api.cli.main(argv, prog, cwd)`. A missing dependency
  exits with `1` and a clear install hint instead of a traceback.
- **Stubs exit cleanly.** `run / build / deploy` accept
  the documented arguments and exit with code 0 (`deploy` exits with 2
  when called without `--dry-run`, since v1 only supports dry-run mode).

## Verify

```bash
# unit tests
make test-agentseek-cli
# direct
uv run pytest contrib/agentseek-cli/tests

# lint + types (auto-discovered targets, see repo Makefile)
make check-agentseek-cli
```

End-to-end smoke checks:

```bash
uv sync && uv run agentseek --help              # plugin mount
uv build contrib/agentseek-cli                  # build wheel
uvx --from contrib/agentseek-cli/dist/agentseek_cli-0.1.0-*.whl agentseek --help
```

## Limitations

- **`agentseek` console-script collision.** Both the main framework and
  this package declare a `[project.scripts] agentseek = ...` entry. Under
  `uvx`-isolated installs there is no conflict. In a shared environment
  where both packages are installed, the last installer wins; if you want
  the rich framework CLI, install `agentseek` last. The plugin path
  (which is how monorepo developers actually consume the new commands)
  is not affected.
- **`skills` install layout follows the upstream tool.** Project-scope
  skills land in `./<agent>/skills/` (e.g. `./.claude/skills/`,
  `./.codex/skills/`) and global skills in `~/<agent>/skills/`.
  AgentSeek does not rewrite those paths. `--dir <path>` only controls
  the working directory `uvx npx-skills` runs in.
- **`run / build / deploy` are surface-only in v1.** The
  flags and help text are stable; the implementations land in follow-up
  PRs (container build, manifest rendering).
- **`create` ships bundled templates.** Templates live under
  `agentseek_cli/templates/<type>/<name>/` and are listed by directory
  scan; add new templates by dropping a folder with a `cookiecutter.json`.
  Bundled today: `deepagents/default`, `langchain/default`,
  `langchain/cli-remote`, `bub/default`.
- **No Windows wheels for `npx-skills`** until upstream publishes them;
  see [npx-skills](https://pypi.org/project/npx-skills/) for current
  platform support.
