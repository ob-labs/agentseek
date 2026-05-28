---
title: CLI reference
type: reference
audience: [A1, A2, A3, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - src/agentseek/__main__.py
  - pyproject.toml
---

# CLI reference

This page mirrors the output of `uv run agentseek <subcommand> --help` for
every subcommand registered by `agentseek 0.1.0` at the verification date.

The CLI binary is registered as `agentseek = "agentseek.__main__:app"` in
`pyproject.toml:49`.

## Top-level options

```text
Usage: agentseek [OPTIONS] COMMAND [ARGS]...
```

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--workspace`, `-w` | TEXT | (unset) | Path to the workspace. |
| `--help` | flag | — | Show top-level help and exit. |

## Commands

### `agentseek run`

:   Start the project locally after completing `.env` configuration.

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--port` | INTEGER | `$PORT` in `.env`, else `3000` | Frontend port. |
    | `--host` | TEXT | `127.0.0.1` | Host to probe for readiness. |
    | `--no-browser` | flag | off | Skip opening the default browser. |
    | `--wait-timeout` | INTEGER | `30` | Seconds to wait for the frontend. |
    | `--mode` | `auto\|compose\|python` | `auto` | Launch mode override. |

    Provided by `agentseek-cli` (`contrib/agentseek-cli/README.md`).

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
    | `--enable-channel` | TEXT (repeatable) | all | Channels to enable. |

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

    See `reference/templates.md` for the bundled template list. Provided by
    `agentseek-cli`.

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
    Available when `agentseek[context]` (or `agentseek-contextseek`) is
    installed. Subcommands include `add`, `retrieve`, `expand`, `compact`,
    `forget`, `delete`, `overview`, `tools`, `metrics`, `dream`, `feedback`,
    `upstream`, `evidence-chain`, `chain-confidence`, `skill-tools`,
    `skill-context`, `skill-import`, `items`.

    See `../how-to/use-contextseek.md` and the [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)
    for usage.

### `agentseek skills`

:   Manage agent skills via the upstream `vercel-labs/skills` CLI (run with
    `npx`).

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--dir` | PATH | `$PWD` | Workspace directory to run `skills` in. |

    Subcommands (each forwards to `npx skills`): `add`, `list`, `find`,
    `update`, `remove`, `init`.

### `agentseek login`

:   Authentication commands.

    Subcommand: `openai` — Login with OpenAI OAuth.

    `agentseek login openai` flags:

    | Flag | Type | Default | Description |
    | --- | --- | --- | --- |
    | `--codex-home` | PATH | — | Directory to store Codex OAuth credentials. |
    | `--browser` / `--no-browser` | flag | `--browser` | Open the OAuth URL in a browser. |
    | `--manual` | flag | off | Paste the callback URL or code instead of running a local callback server. |
    | `--timeout` | FLOAT | `300.0` | OAuth wait timeout in seconds. |

## Help commands actually executed

The following commands were run from the repository root to populate this
page:

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
uv run agentseek login --help
uv run agentseek login openai --help
```

## See also

- How-to: `../how-to/install-a-plugin.md`, `../how-to/run-locally.md`,
  `../how-to/run-gateway.md`, `../how-to/build-and-deploy.md`
- Reference: `environment.md`, `packages.md`
