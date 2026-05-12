# agentseek-schedule-sqlalchemy

`agentseek-schedule-sqlalchemy` is an agentseek contrib package that exposes a Bub plugin for
persisting APScheduler jobs in a SQLAlchemy-backed store.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-schedule-sqlalchemy` |
| Python package | `agentseek_schedule_sqlalchemy` |
| Bub entry point | `schedule` |
| Config section / surface | `schedule` |
| Root install path | `uv sync` |
| Test target | `make test` |

## When To Use It

It targets the Bub runtime shape used by both plain Bub and the agentseek distribution, where:

- scheduled jobs must survive process restarts
- scheduling must work in `bub chat`
- the same scheduler may also be started by a gateway channel at runtime

The package exposes the Bub plugin entry point `schedule` and uses `BackgroundScheduler`, so
scheduler startup is not tied to a specific async event loop or to the `schedule` channel being
enabled.

## Install

The root `agentseek` workspace already includes this package as a workspace dependency. From the repository root, the normal sync is enough:

```bash
uv sync
```

Install from the monorepo package directory when you are adding this plugin to another local project:

```bash
uv add ./contrib/agentseek-schedule-sqlalchemy
```

Install directly from GitHub:

```bash
uv pip install "git+https://github.com/ob-labs/agentseek.git#subdirectory=contrib/agentseek-schedule-sqlalchemy"
```

When vendoring this package into another workspace, declare both the dependency and the source:

```toml
[project]
dependencies = [
    "agentseek-schedule-sqlalchemy",
]

[tool.uv.sources]
agentseek-schedule-sqlalchemy = { workspace = true }

[tool.uv.workspace]
members = [
    "contrib/agentseek-schedule-sqlalchemy",
]
```

## Configure

The runtime config surface follows Bub semantics: the plugin registers a Bub config section named
`schedule`, matching its Bub entry point. The package name stays `agentseek-schedule-sqlalchemy`
because it belongs to the agentseek distribution namespace.

`uv run agentseek onboard` can now collect this section interactively for agentseek-managed
setups. It writes `schedule.url` and `schedule.tablename` into `config.yml`.

`config.yml` example:

```yaml
schedule:
  url: sqlite+pysqlite:///./agentseek-schedule.db
  tablename: apscheduler_jobs
```

The same fields can also come from environment variables:

| agentseek variable | Bub variable | Purpose |
| --- | --- | --- |
| `AGENTSEEK_SCHEDULE_SQLALCHEMY_URL` | `BUB_SCHEDULE_SQLALCHEMY_URL` | Primary SQLAlchemy database URL for APScheduler jobs. |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `BUB_TAPESTORE_SQLALCHEMY_URL` | Fallback database URL when the schedule-specific URL is unset. |
| `AGENTSEEK_SCHEDULE_SQLALCHEMY_TABLENAME` | `BUB_SCHEDULE_SQLALCHEMY_TABLENAME` | Optional table name. Defaults to `apscheduler_jobs`. |

Resolution order:

1. use the schedule-specific URL from environment or `.env` when set
2. otherwise fall back to the shared tapestore SQLAlchemy URL from environment or `.env`
3. otherwise use `config.yml` `schedule.url` when present
4. otherwise scheduler creation may fail and the plugin will log a warning and stay disabled

Example:

```bash
export AGENTSEEK_SCHEDULE_SQLALCHEMY_URL=sqlite:////tmp/agentseek-schedule.sqlite
```

When both prefixes are present for the same setting, the `BUB_*` value wins. This keeps the plugin compatible with plain Bub while matching agentseek's global alias behavior.

## Run

Use a dedicated schedule database:

```bash
export AGENTSEEK_SCHEDULE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-schedule.db
uv run agentseek chat
```

Or reuse the same SQLAlchemy URL as a tape store plugin:

```bash
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-runtime.db
uv run agentseek chat
```

The second form only controls the scheduler fallback URL. A separate tape store plugin is still responsible for tape persistence.

## Runtime Behavior

`ScheduleImpl` starts the scheduler lazily from `load_state()`, which runs before tools on every
inbound message. This is the key behavior that keeps scheduling usable in Bub's CLI flow,
including `bub chat` and the agentseek distribution entry point built on the same runtime: even
when only the `cli` channel is active, the scheduler is started and jobs are persisted instead of
being left in APScheduler's in-memory pending queue.

When the `schedule` channel is enabled in a gateway runtime, `ScheduleChannel` also starts the same scheduler on channel startup and shuts it down cleanly on channel stop.

If scheduler construction fails, the plugin does not crash the framework:

- `load_state()` logs `Schedule plugin disabled: ...` and returns an empty state
- `provide_channels()` logs the same warning and returns no `schedule` channel

### Test-Covered Behavior

Current tests cover these behaviors:

- SQLAlchemy job store round-trip persistence with SQLite
- `ScheduleImpl.load_state()` starts the injected scheduler
- `onboard_config()` can write the `schedule` section
- registered `schedule` config resolves from `config.yml`
- environment variables override `config.yml` for registered settings
- settings resolution from `AGENTSEEK_SCHEDULE_SQLALCHEMY_URL`
- compatibility with `BUB_SCHEDULE_SQLALCHEMY_URL`
- fallback from `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL`
- `schedule.trigger` executes both sync and async jobs
- `schedule.trigger` does not shift an interval job's `next_run_time`

## Verify

From the repository root:

```bash
make test
```

Or run only this package's tests:

```bash
uv run python -m pytest contrib/agentseek-schedule-sqlalchemy/src/tests
```

## Limitations

- this package only provides scheduling infrastructure; actual reminder delivery still depends on the surrounding Bub runtime or agentseek distribution setup and enabled channels
- session scoping is based on the `session_id` stored in job kwargs
- persistence quality and locking semantics depend on the configured SQLAlchemy backend
