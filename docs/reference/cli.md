---
title: CLI reference
type: reference
audience: [A1, A2, A3, A4]
runs: yes
verified_on: 2026-05-29
sources:
  - src/agentseek/cli.py
  - src/agentseek/__main__.py
  - contrib/agentseek-cli/src/agentseek_cli/standalone.py
  - contrib/agentseek-cli/src/agentseek_cli/plugin.py
  - contrib/agentseek-cli/src/agentseek_cli/app.py
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
---

# CLI reference

Both PyPI packages register the same console script name `agentseek`. The
command surface you see depends on which one is active.

| Source package | `agentseek` resolves to | When you see it |
| --- | --- | --- |
| `agentseek-cli` (project lifecycle CLI) | `agentseek_cli.standalone:app` (`contrib/agentseek-cli/pyproject.toml:18`) | Path A — `uv tool install agentseek-cli` |
| `agentseek` (harness) | `agentseek.__main__:app` (`pyproject.toml:49`) | Path B — `git clone … && uv sync && uv run agentseek` |

`agentseek_cli.standalone:app` (`contrib/agentseek-cli/src/agentseek_cli/standalone.py:24-32`)
resolves lazily on each invocation:

- If the **harness** (`agentseek`) is **not** importable, it calls
  `agentseek_cli.app.build_app()` and exposes only the project lifecycle
  groups.
- If the harness **is** importable, it defers to
  `agentseek.__main__.create_cli_app()`. That function bootstraps `BubFramework`
  and loads every Bub plugin — including `agentseek_cli.plugin:main` — so the
  resulting CLI surface is identical whether you launched the script from
  `agentseek` or from `agentseek-cli`.

The Bub plugin in `contrib/agentseek-cli/src/agentseek_cli/plugin.py:28-42`
mounts every project lifecycle group onto the framework app and is allowed to
**override** the framework's builtin `run` (which is Bub's
single-message dispatch) with the project lifecycle CLI's `run` (which starts
the project locally). The override only happens when `agentseek-cli` is
present alongside the harness.

This page lists every subcommand and notes which surface owns it.

## Project lifecycle commands

These commands come from `agentseek-cli`
(`contrib/agentseek-cli/src/agentseek_cli/app.py:22-30`). They are available
on **Path A** out of the box, and on **Path B** whenever `agentseek-cli` is
installed in the harness env (e.g. via `agentseek install agentseek-cli`, or
because the generated project depends on it).

### `agentseek create [SPEC]`

:   Create a new agent project from a pre-built template (cookiecutter under
    `templates/`).

    | Argument / Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `spec` | TEXT | — | Framework type (`deepagents`, `langchain`, `bub`), `type/name`, git URL, or local path. |
    | `--template` | TEXT | — | Named template under the chosen type (e.g. `cli-remote`). |
    | `--checkout` | TEXT | — | Branch / tag / commit for remote fetches. |
    | `--list-templates` | flag | — | List templates available for the type and exit. |
    | `--no-input` | flag | off | Skip cookiecutter prompts. |

    See [Templates reference](templates.md) for the bundled template list.

### `agentseek run`

:   Start the project locally after completing `.env` configuration.

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--port` | INTEGER | `$PORT` in `.env`, else `3000` | Frontend port. |
    | `--host` | TEXT | `127.0.0.1` | Host to probe for readiness. |
    | `--no-browser` | flag | off | Skip opening the default browser. |
    | `--wait-timeout` | INTEGER | `30` | Seconds to wait for the frontend. |
    | `--mode` | `auto\|compose\|python` | `auto` | Launch mode override. |

    On **Path B with `agentseek-cli` absent**, the upstream Bub builtin
    `run MESSAGE` (single inbound message) is exposed under the same name
    instead. The plugin override (`CLI_OVERRIDE_NAMES = {"run"}`) only swaps
    them when `agentseek-cli` is present.

### `agentseek build`

:   Build the project into a container image (wraps `docker build` /
    `docker buildx build`). Top-level command — has no subcommands despite
    the `COMMAND [ARGS]...` line in `--help`.

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--tag`, `-t` | TEXT | `<cwd-slug>:latest` | Image tag. |
    | `--file`, `-f` | PATH | (resolved by `agentseek-cli`) | Path to the Dockerfile. |
    | `--context` | PATH | `.` | Build context directory. |
    | `--platform` | TEXT | — | Comma-separated target platforms. |
    | `--push` | flag | off | Push after a successful build. |
    | `--no-cache` | flag | off | Do not use cache when building. |
    | `--build-arg` | TEXT (repeatable) | — | `KEY=VALUE` build-time variable. |
    | `--dry-run` | flag | off | Print the resolved command(s) without executing. |

### `agentseek deploy`

:   Generate deployment manifests (docker-compose / k8s). Top-level command —
    has no subcommands despite the `COMMAND [ARGS]...` line in `--help`. In
    v1, `--dry-run` is required.

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--dry-run` | flag | required in v1 | Generate manifests without deploying. |
    | `--mode` | `docker-compose\|k8s\|both` | `both` | Deployment target. |
    | `--output` | DIRECTORY | `deploy` | Where to write manifests. |
    | `--image` | TEXT | `<project-slug>:latest` | Container image reference. |
    | `--slug` | TEXT | inferred from cwd | Project slug used in service / deployment names. |
    | `--port` | INTEGER | `8000` | Service port. |
    | `--replicas` | INTEGER (≥1) | `1` | k8s Deployment replicas. |
    | `--namespace` | TEXT | `default` | k8s namespace. |

### `agentseek api`

:   Forward API runtime commands to `agentseek-api` when it is installed.
    Without `agentseek-api` in the environment, every subcommand fails with:

    ```text title="output"
    The `agentseek api` commands require `agentseek-api` in the current environment.
    Install it first, for example: `uv pip install -e references/agentseek-api`.
    ```

    Subcommands (each forwards the same-name command to `agentseek-api`):
    `dev`, `serve`, `dockerfile`, `build`, `up`, `version`.

### `agentseek ctx`

:   ContextSeek — semantic context layer. Forwarded to the `contextseek` CLI.
    Available when `agentseek-contextseek` is on the path (e.g. on Path B via
    `agentseek install agentseek-contextseek`, or on Path A when the generated
    project pulls it in).

    Subcommands include `add`, `retrieve`, `expand`, `compact`, `forget`,
    `delete`, `overview`, `tools`, `metrics`, `dream`, `feedback`,
    `upstream`, `evidence-chain`, `chain-confidence`, `skill-tools`,
    `skill-context`, `skill-import`, `items`.

    See [How to use ContextSeek](../how-to/use-contextseek.md) and the
    [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)
    for usage.

### `agentseek skills`

:   Manage agent skills via the upstream `vercel-labs/skills` CLI (run with
    `npx`).

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--dir` | PATH | `$PWD` | Workspace directory to run `skills` in. |

    Subcommands (each forwards to `npx skills`): `add`, `list`, `find`,
    `update`, `remove`, `init`.

## Harness runtime commands

These commands come from the harness (`agentseek`) and are available only on
**Path B** (or inside a generated project after `uv sync`). `uv tool install
agentseek-cli` alone does not bring them in.

### Top-level options

```text
Usage: agentseek [OPTIONS] COMMAND [ARGS]...
```

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--workspace`, `-w` | TEXT | (unset) | Path to the workspace. |
| `--help` | flag | — | Show top-level help and exit. |

### `agentseek chat`

:   Bub-builtin chat over the CLI channel; agentseek adds lifecycle channels
    (`src/agentseek/cli.py:83`).

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--chat-id` | TEXT | `local` | Chat id. |
    | `--session-id` | TEXT | `None` | Optional session id. |

### `agentseek onboard`

:   Interactively collect plugin configuration and write it to Bub's config
    file. Uses the agentseek branding banner from `src/agentseek/cli.py:23`.

    Takes no flags beyond `--help`.

### `agentseek gateway`

:   Start message listeners (e.g. telegram).

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--enable-channel` | TEXT (repeatable) | all | Channels to enable for CLI (default: all). |

### `agentseek install [SPECS]...`

:   Install a plugin into Bub's environment, or sync the environment if no
    specifications are provided. agentseek replaces the install sandbox with
    `DEFAULT_PLUGIN_SANDBOX = "agentseek-project"`
    (`src/agentseek/cli.py:115`, `src/agentseek/env.py:22`).

    | Argument / Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `SPECS` | TEXT… | `[]` | Git URL, `owner/repo`, or `name@branch` in bub-contrib. |
    | `--project` | PATH | `${BUB_PROJECT}` (defaults to `${BUB_HOME}/agentseek-project`) | Path to the project directory. |

    The help text still prints the upstream default `~/.bub/bub-project`. The
    runtime default is the agentseek sandbox because
    `apply_agentseek_env_aliases` sets `BUB_PROJECT` before Typer reads the
    default (`src/agentseek/env.py:73`).

### `agentseek uninstall PACKAGES...`

:   Uninstall a plugin from Bub's environment. `PACKAGES` is required.

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--project` | PATH | `${BUB_PROJECT}` | Path to the project directory. |

### `agentseek update [PACKAGES]...`

:   Update selected packages, or all packages in Bub's environment when no
    arguments are given.

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--project` | PATH | `${BUB_PROJECT}` | Path to the project directory. |

### `agentseek mcp`

:   Manage MCP servers in the resolved `mcp.json` (path resolved by
    `bub-mcp` from `${BUB_MCP_CONFIG_PATH}` / `${AGENTSEEK_MCP_CONFIG_PATH}`,
    default `${BUB_HOME}/mcp.json`).

    Subcommands: `list`, `add`, `remove`.

    `agentseek mcp list` — list registered MCP tools. No flags beyond
    `--help`.

    `agentseek mcp add NAME TARGET...` flags:

    | Argument / Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `NAME` | TEXT | — | Server name (required). |
    | `TARGET` | TARGET… | — | URL for remote servers, or `-- <command>` for stdio (required). |
    | `--transport` | `http\|sse\|stdio` | — | MCP transport (required). |
    | `--env` | TEXT (repeatable) | — | `KEY=VALUE` env var for stdio servers. |
    | `--header` | TEXT (repeatable) | — | `Name: Value` header for http or sse servers. |

    `agentseek mcp remove NAME` — remove a server by name. `NAME` is
    required; no other flags.

    See [How to configure MCP servers](../how-to/configure-mcp.md) and
    [How to add an MCP server](../how-to/add-mcp-server.md) for end-to-end
    recipes.

### `agentseek login`

:   Authentication commands.

    Subcommand: `openai` — Login with OpenAI OAuth.

    `agentseek login openai` flags:

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--codex-home` | PATH | — | Directory to store Codex OAuth credentials. |
    | `--browser` / `--no-browser` | flag | `--browser` | Open the OAuth URL in a browser. |
    | `--manual` | flag | off | Paste the callback URL or code instead of waiting for a local callback server. |
    | `--timeout` | FLOAT | `300.0` | OAuth wait timeout in seconds. |

## Help commands actually executed

The following commands were run from the repository root (Path B, with all
extras) to populate this page:

```bash
uv run agentseek --help
uv run agentseek run --help
uv run agentseek chat --help
uv run agentseek onboard --help
uv run agentseek gateway --help
uv run agentseek install --help
uv run agentseek uninstall --help
uv run agentseek update --help
uv run agentseek create --help
uv run agentseek build --help
uv run agentseek deploy --help
uv run agentseek api --help
uv run agentseek api dev --help
uv run agentseek ctx --help
uv run agentseek skills --help
uv run agentseek skills add --help
uv run agentseek mcp --help
uv run agentseek mcp list --help
uv run agentseek mcp add --help
uv run agentseek mcp remove --help
uv run agentseek login --help
uv run agentseek login openai --help
```

## See also

- Overview: [agentseek](../index.md)
- Explanation: [Choosing an entry point](../explanation/choosing-an-entry-point.md)
- How-to: [How to install a plugin](../how-to/install-a-plugin.md), [How to run agentseek locally](../how-to/run-locally.md),
  [How to run the gateway](../how-to/run-gateway.md), [How to build and deploy](../how-to/build-and-deploy.md)
- Reference: [Environment variables reference](environment.md), [Packages reference](packages.md)
