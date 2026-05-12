# agentseek-tapestore-oceanbase

OceanBase compatibility and vector enhancement plugin for `agentseek` and `bub`.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-tapestore-oceanbase` |
| Python package | `agentseek_tapestore_oceanbase` |
| Bub entry point | `tapestore-oceanbase` |
| Config section / surface | `tapestore-oceanbase` |
| Root install path | `uv sync --extra oceanbase` |
| Test target | `make check-oceanbase` |

## When To Use It

Use this package when you want Bub/agentseek tape data in a SQLAlchemy-backed store and may later move the same runtime data to OceanBase.

For local development, SQLite is enough. For OceanBase deployments, use `mysql+oceanbase://...` and optionally enable vector retrieval with an embedding model.

What it provides:

- depends on `bub-tapestore-sqlalchemy` instead of reimplementing its base store
- installs `pyobvector` and `any-llm-sdk`, while keeping vector retrieval runtime-optional
- registers `mysql+oceanbase://...` compatibility behavior for dialect/savepoint handling
- adds OceanBase vector search powered by `pyobvector` and `any-llm-sdk`
- leaves normal SQLAlchemy tape storage behavior to `bub-tapestore-sqlalchemy`

## Install

Inside this repository:

```bash
uv sync --extra oceanbase
```

If you only want this plugin package outside the root extra flow, install it directly.

From Git:

```bash
uv pip install "git+https://github.com/ob-labs/agentseek.git#subdirectory=contrib/agentseek-tapestore-oceanbase"
```

From a local checkout:

```bash
uv pip install -e contrib/agentseek-tapestore-oceanbase
```

## Configure

The plugin reuses the base SQLAlchemy tape store URL variables from `bub-tapestore-sqlalchemy`:

| agentseek variable | Bub variable | Purpose |
| --- | --- | --- |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `BUB_TAPESTORE_SQLALCHEMY_URL` | SQLAlchemy URL for tape storage. |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_ECHO` | `BUB_TAPESTORE_SQLALCHEMY_ECHO` | Enables SQLAlchemy SQL logging. |

OceanBase-specific vector controls:

| agentseek variable | Bub variable | Purpose |
| --- | --- | --- |
| `AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL` | `BUB_TAPESTORE_OCEANBASE_EMBEDDING_MODEL` | Embedding model used for lazy message indexing on OceanBase. |
| `AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC` | `BUB_TAPESTORE_OCEANBASE_VECTOR_METRIC` | Vector distance metric. Supported values: `cosine`, `l2`. Defaults to `cosine`. |

Compatibility aliases remain accepted:

| Compatibility alias | Preferred variable |
| --- | --- |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_EMBEDDING_MODEL` | `AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL` |
| `BUB_TAPESTORE_SQLALCHEMY_EMBEDDING_MODEL` | `BUB_TAPESTORE_OCEANBASE_EMBEDDING_MODEL` |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_VECTOR_METRIC` | `AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC` |
| `BUB_TAPESTORE_SQLALCHEMY_VECTOR_METRIC` | `BUB_TAPESTORE_OCEANBASE_VECTOR_METRIC` |

When both `AGENTSEEK_*` and `BUB_*` names are set for the same value, the `BUB_*` value wins through agentseek's global alias behavior.

### Onboarding

When this plugin is installed, `uv run agentseek onboard` can prompt for the `tapestore-oceanbase` config section:

```yaml
tapestore-oceanbase:
  embedding_model: openai:text-embedding-3-small
  vector_metric: cosine
```

The SQLAlchemy URL itself still comes from the base tape store settings.

## Run

### Local SQLite

Install the extra and point the tape store at a local SQLite file:

```bash
uv sync --extra oceanbase
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-tapes.db
uv run agentseek chat
```

This uses the same plugin entry point but does not activate OceanBase vector retrieval.

### OceanBase Vector

```bash
uv sync --extra oceanbase
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=mysql+oceanbase://user:password@127.0.0.1:2881/agentseek
export AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL=openai:text-embedding-3-small
export AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC=cosine
uv run agentseek chat
```

Vector retrieval is active only when:

- the SQLAlchemy URL driver contains `oceanbase`
- an embedding model is configured

## Runtime Behavior

- Base tape schema, append/read/reset, and normal text search still come from `bub-tapestore-sqlalchemy`.
- This package guards Bub's plugin registration so its OceanBase provider stays active even when `bub-tapestore-sqlalchemy` is installed as a dependency.
- The returned store is still a subclass wrapper around `bub-tapestore-sqlalchemy`, not a forked reimplementation.
- Message entries are embedded lazily on query into plugin-owned side tables.
- If vector mode is inactive, queries fall back to the original `bub-tapestore-sqlalchemy` behavior.

Plugin-owned vector tables include metadata for embedding dimensions and `tape_entry_embeddings` for message embeddings.

## Verify

From the repository root:

```bash
make check-oceanbase
```

Or run only this package's tests after syncing the extra:

```bash
uv sync --extra oceanbase
uv run python -m pytest contrib/agentseek-tapestore-oceanbase/tests
```

## Limitations

- Vector retrieval is OceanBase-specific; SQLite and other SQLAlchemy URLs use the base tape store query behavior.
- Embedding dimensions are fixed after the first vector schema is created. Changing embedding models may require a new database or manual migration.
- Embedding calls are made lazily during query, so the first vector query may perform indexing work.
