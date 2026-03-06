# bubseek

**bubseek** is an enterprise-oriented distribution of [Bub](https://github.com/bubbuild/bub) for agent-driven insight workflows in cloud-edge environments.

It turns fragmented data across operational systems, repositories, and agent runtime traces into **explainable, actionable, and shareable insights** without heavy ETL. The runtime stays Bub; bubseek adds distribution tooling: a declarative manifest (`bubseek.toml`), a lockfile (`bubseek.lock`), and commands to sync **contrib** packages and **skills** into your workspace.

## Documentation

| Section | Description |
|--------|--------------|
| [Getting started](getting-started.md) | Install, initialize config, lock, sync, and run Bub. |
| [Configuration](configuration.md) | `bubseek.toml` reference: project, bub, contrib, skills. |
| [Architecture](architecture.md) | Design boundaries, command model, locking and cache. |
| [Development](development.md) | Running tests, linting, and contributing. |
| [API reference](api-reference.md) | Python modules and public API. |

## Quick links

- [Repository](https://github.com/psiace/bubseek)
- [PyPI](https://pypi.org/project/bubseek/)
- [Bub](https://github.com/bubbuild/bub)
