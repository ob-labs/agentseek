# Contrib

This directory documents contrib-related examples for `bubseek`.

`bubseek` does not install contrib from this directory. Contrib packages remain standard Python packages and should be added through normal dependency management in `pyproject.toml`.

Typical example:

```toml
[project]
dependencies = [
    "bub==0.3.0a1",
    "bub-codex @ git+https://github.com/bubbuild/bub-contrib.git@main#subdirectory=packages/bub-codex",
]
```
