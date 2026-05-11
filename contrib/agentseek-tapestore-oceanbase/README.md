# agentseek-tapestore-oceanbase

OceanBase compatibility and vector enhancement plugin for `agentseek` and `bub`.

## What It Provides

- Bub plugin entry point: `tapestore-oceanbase`
- Depends on `bub-tapestore-sqlalchemy` instead of reimplementing its base store
- Installs `pyobvector` and `any-llm-sdk`, while keeping vector retrieval runtime-optional
- Registers `mysql+oceanbase://...` compatibility behavior for dialect/savepoint handling
- Adds OceanBase vector search powered by `pyobvector` and `any-llm-sdk`
- Leaves normal SQLAlchemy tape storage behavior to `bub-tapestore-sqlalchemy`

## Installation

Inside this repository:

```bash
uv sync --extra oceanbase
```

If you only want the plugin package itself outside the root extra flow, install it directly:

From Git:

```bash
uv pip install "git+https://github.com/ob-labs/agentseek.git#subdirectory=contrib/agentseek-tapestore-oceanbase"
```

## Configuration

The plugin reuses the base SQLAlchemy tape store URL variables from `bub-tapestore-sqlalchemy`:

- `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` / `BUB_TAPESTORE_SQLALCHEMY_URL`
- `AGENTSEEK_TAPESTORE_SQLALCHEMY_ECHO` / `BUB_TAPESTORE_SQLALCHEMY_ECHO`

OceanBase-specific vector controls:

- `AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL` / `BUB_TAPESTORE_OCEANBASE_EMBEDDING_MODEL`
- `AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC` / `BUB_TAPESTORE_OCEANBASE_VECTOR_METRIC`
- Compatibility aliases remain accepted:
  - `AGENTSEEK_TAPESTORE_SQLALCHEMY_EMBEDDING_MODEL` / `BUB_TAPESTORE_SQLALCHEMY_EMBEDDING_MODEL`
  - `AGENTSEEK_TAPESTORE_SQLALCHEMY_VECTOR_METRIC` / `BUB_TAPESTORE_SQLALCHEMY_VECTOR_METRIC`

Example SQLite fallback:

```bash
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-tapes.db
```

Example OceanBase vector mode:

```bash
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=mysql+oceanbase://user:password@127.0.0.1:2881/agentseek
export AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL=openai:text-embedding-3-small
export AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC=cosine
```

## Runtime Behavior

- Base tape schema, append/read/reset, and normal text search still come from `bub-tapestore-sqlalchemy`.
- This package guards Bub's plugin registration so its OceanBase provider stays active even when `bub-tapestore-sqlalchemy` is installed as a dependency.
- The returned store is still a subclass wrapper around `bub-tapestore-sqlalchemy`, not a forked reimplementation.
- Vector search is activated only when:
  - the tape store URL uses `mysql+oceanbase`
  - `embedding_model` is configured
- Message entries are embedded lazily on query into plugin-owned side tables.
- If vector mode is inactive, queries fall back to the original `bub-tapestore-sqlalchemy` behavior.
