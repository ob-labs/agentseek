# Development

This page describes how to run tests, linting, and type-checking locally. For contribution workflow and guidelines, see [CONTRIBUTING.md](https://github.com/psiace/bubseek/blob/main/CONTRIBUTING.md) in the repository.

## Setup

From the repository root:

```bash
uv sync
make install
```

`make install` creates the virtual environment, installs dependencies, and installs pre-commit hooks. Ensure you have **uv** and **Python 3.12+** installed.

## Commands

| Command       | Description |
|---------------|-------------|
| `make install` | Create venv, install deps, install pre-commit hooks. |
| `make check`   | Verify lock consistency, run pre-commit (lint/format), run type checker. |
| `make test`   | Run pytest (including doctests). |
| `make docs`   | Serve MkDocs documentation locally. |
| `make docs-test` | Build docs (fail on warnings). |
| `make help`   | List all make targets. |

## Lock and index

- **Update lockfile (PyPI):** `make lock` or `uv lock --default-index https://pypi.org/simple`  
  Use this so the lockfile stays resolved against the official index.
- **Install with a mirror (e.g. Tsinghua):**  
  `UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple uv sync`

## Pre-commit

After `make install`, pre-commit runs on commit. To run manually:

```bash
uv run pre-commit run -a
```

## Testing

```bash
make test
# or
uv run pytest tests
```

## Type checking

```bash
uv run ty check
```

## Linting and formatting

Ruff is used for linting and formatting, via pre-commit or directly:

```bash
uv run ruff check .
uv run ruff format .
```

## Building docs

```bash
make docs        # Serve at http://127.0.0.1:8000
make docs-test   # Build and fail on warnings
```

Documentation is built with MkDocs and the Material theme; API docs are generated with mkdocstrings from the `bubseek` package.
