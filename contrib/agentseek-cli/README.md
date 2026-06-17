# agentseek-cli

> Deprecated: `agentseek-cli` is kept only as a compatibility package.
> Install and use `agentseek>=0.0.3` instead.

## Migration

```bash
pip install -U 'agentseek>=0.0.3'
agentseek --help
```

For uv-managed tools:

```bash
uv tool install 'agentseek>=0.0.3'
agentseek --help
```

The CLI previously published as `agentseek-cli` now lives in the main
`agentseek` distribution. New projects and automation should depend on
`agentseek>=0.0.3`, not `agentseek-cli`.

## Package Details

| Field             | Value                                      |
| ----------------- | ------------------------------------------ |
| Distribution name | `agentseek-cli`                            |
| Python package    | `agentseek_cli`                            |
| Console script    | `agentseek` (`agentseek_cli.standalone:app`) |
| Status            | Deprecated compatibility package           |
| Replacement       | `agentseek>=0.0.3`                         |
| Test target       | `make check-cli`                           |

## Compatibility Behavior

`agentseek-cli` still exposes the legacy `agentseek` console script so old
install commands fail gently. On command execution it prints:

```text
agentseek-cli is deprecated. Install and use agentseek>=0.0.3 instead: pip install -U 'agentseek>=0.0.3'.
```

The package remains buildable for the `0.0.4` compatibility release, but it
should not be used as the documented entry point for AgentSeek.

## Maintainer Verification

```bash
uv lock --locked
make check-cli
uv build contrib/agentseek-cli
uvx twine check dist/*
uvx --from dist/agentseek_cli-0.0.4-py3-none-any.whl agentseek version
```
