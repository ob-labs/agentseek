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
| Install path         | `pip install agentseek-cli` / `uv tool install agentseek-cli` |
| Test target          | `make test-agentseek-cli`                   |

Top-level command groups: `new`, `dev`, `build`, `deploy`, `api`, `ctx`,
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

### Standalone

```bash
uvx --from agentseek-cli agentseek --help
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
- `contextseek` settings can be passed with either native `STORAGE_*` / `OB_*`
  variables or `AGENTSEEK_CTX_*` aliases (when `agentseek-contextseek` is
  installed alongside this package).

The only CLI-level option exposed by this package is
`agentseek skills --dir <path>`, which `chdir`s before delegating.

## Run

```bash
# discover the surface
agentseek --help
agentseek skills --help
agentseek api --help
agentseek ctx --help

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

# contextseek surface (requires contextseek in the env)
agentseek ctx init --backend memory
agentseek ctx retrieve --scope acme/db/eng --query "distributed database"
agentseek ctx serve --port 8001 --mcp

# new — scaffold a project from a bundled cookiecutter template
agentseek new                                  # interactive type + template
agentseek new deepagents                       # default template (no prompt for type)
agentseek new langchain/cli-remote             # type/name shorthand
agentseek new --template                       # list every bundled template
agentseek new langchain --template             # list templates under a type
agentseek new langchain --list-templates       # same as above (legacy flag)
agentseek new bub --template default --no-input

# dev — start the project locally and open the frontend
agentseek dev                                     # auto-detect compose / python entry
agentseek dev --no-browser                        # skip opening a browser tab
agentseek dev --mode compose --port 8080          # explicit mode override
agentseek dev --wait-timeout 60                   # extend readiness budget

# build — package the project into a Docker image
agentseek build                                   # default tag: <cwd-slug>:latest
agentseek build --tag myproj:1.0 --no-cache
agentseek build --platform linux/amd64,linux/arm64 --tag myproj:multi  # uses buildx
agentseek build --build-arg PYTHON_VERSION=3.12 --push
agentseek build --dry-run                         # print resolved docker command

# deploy — render docker-compose / k8s manifests (dry-run only in v1)
agentseek deploy --dry-run                                # both, ./deploy/
agentseek deploy --dry-run --mode docker-compose --output ./deploy --image myproj:1.0
agentseek deploy --dry-run --mode k8s --replicas 3 --namespace platform
agentseek deploy --dry-run --mode both --slug myproj --port 9000
```

## Runtime Behavior

- **Dual entrypoints.** Both the standalone `agentseek` console script
  (`agentseek_cli.standalone:app`) and the Bub plugin
  (`agentseek_cli.plugin:main`) call `agentseek_cli.app.build_app()`
  / `iter_command_groups()`, so the surface stays in lockstep.
- **Plugin mount without framework overrides.** `register_cli_commands` skips
  any group whose name is already attached to the root Typer. `agentseek dev`
  therefore behaves like:
  - under `uvx --from agentseek-cli agentseek` (framework absent) — the
    project lifecycle runner;
  - under monorepo / shared env (framework present) — the same project
    lifecycle runner mounted through the Bub plugin.
- **`skills` is a thin pass-through.** It invokes
  `npx-skills <subcommand> [...args]`. `npx-skills` ships as a Python
  dependency of this package and provides the executable on `PATH`.
- **`api` migrated from `agentseek-langchain`.** The same Protocol-based
  duck-typing forwards `dev / serve / dockerfile / build / up / version`
  to `agentseek_api.cli.main(argv, prog, cwd)`. A missing dependency
  exits with `1` and a clear install hint instead of a traceback.
- **`ctx` migrated from `agentseek-contextseek`.** `agentseek-cli` now owns the
  whole `agentseek ctx` group (passthrough + `init` / `serve` / `sync`) so
  command discovery is centralized in one CLI plugin.
- **Stubs exit cleanly.** All commands accept the documented arguments;
  `deploy` exits with 2 when called without `--dry-run`, since v1 only
  supports dry-run mode.
- **`deploy` renders inline templates.** v1 emits
  `docker-compose.yaml` and/or `k8s/deployment.yaml` + `k8s/service.yaml`
  under `--output` (default `./deploy`). The slug defaults to a
  docker-friendly form of the cwd directory name; `--image` overrides
  the default `<slug>:latest`. Existing files are listed before they are
  overwritten so manual edits are not lost silently. Real cluster /
  registry interaction lands in a follow-up PR.
- **`build` wraps docker.** `agentseek build` shells out to
  `docker build` (single platform / no `--platform`) or
  `docker buildx build` (multi-platform). The default tag is
  `<cwd-slug>:latest`; `--push` runs `docker push <tag>` after a
  successful build; `--dry-run` prints the resolved command(s) without
  invoking docker. Missing `docker` exits with `1` and a clear install
  hint; a missing `Dockerfile` exits with `2` and points at
  `agentseek new`.
- **`dev` auto-detects launch mode.** The presence of
  `docker-compose.yml` / `compose.yaml` selects compose mode; otherwise
  the command looks for `pyproject.toml` plus an `app.py` / `main.py`
  entry or a `serve` / `dev` script. `--mode compose|python` overrides
  detection. The frontend URL is built from `--host` (default
  `127.0.0.1`) and `--port` (defaults to `PORT` from `.env`, then
  `3000`); `agentseek dev` polls it once per second until the readiness
  timeout (`--wait-timeout`, default `30s`) and then opens the default
  browser unless `--no-browser` is passed. On exit (Ctrl-C or child
  termination) the spawned process is `terminate()`d with a
  5-second grace period before `kill()`, and compose mode runs
  `docker compose down` for cleanup.

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
uvx --from contrib/agentseek-cli/dist/agentseek_cli-0.0.2-*.whl agentseek --help
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
  the working directory `npx-skills` runs in.
- **`deploy` is dry-run only in v1.** The flags and rendered manifest
  shape are stable; future versions will add `--apply` (kubectl apply /
  docker compose up) and registry interaction. For now, generate the
  YAML, review/commit it, and apply it with your existing toolchain.
- **`new` ships bundled templates.** Templates live under
  `templates/<type>/<name>/` and are listed by directory
  scan; add new templates by dropping a folder with a `cookiecutter.json`.
  Run `agentseek new --template` to see all available templates with
  descriptions.
- **No Windows wheels for `npx-skills`** until upstream publishes them;
  see [npx-skills](https://pypi.org/project/npx-skills/) for current
  platform support.
