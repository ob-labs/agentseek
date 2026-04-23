# Contrib

This directory contains plugins for `bubseek`.

Contrib packages remain standard Python packages and should be added through normal dependency management in `pyproject.toml`.

A typical plugin should work with bub as well.

Typical example:

```toml
[project]
dependencies = [
    "bub==0.3.0a1",
    "bub-codex @ git+https://github.com/bubbuild/bub-contrib.git@main#subdirectory=packages/bub-codex",
]
```
