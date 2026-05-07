# agentseek-schedule-sqlalchemy

`agentseek-schedule-sqlalchemy` is an agentseek contrib package that exposes a Bub plugin for
persisting APScheduler jobs in a SQLAlchemy-backed store.

The naming split is intentional:

- `agentseek-schedule-sqlalchemy` is the Python distribution/package name used in dependency management
- `schedule` is the Bub plugin entry point and config section name used at runtime

It targets the Bub runtime shape used by both plain Bub and the agentseek distribution, where:

- scheduled jobs must survive process restarts
- scheduling must work in `bub chat`
- the same scheduler may also be started by a gateway channel at runtime

The package exposes the Bub plugin entry point `schedule` and uses `BackgroundScheduler`, so
scheduler startup is not tied to a specific async event loop or to the `schedule` channel being
enabled.

## Installation

Install from the monorepo package directory during local development:

```bash
uv add ./contrib/agentseek-schedule-sqlalchemy
```

Install directly from GitHub:

```bash
uv pip install "git+https://github.com/ob-labs/agentseek.git#subdirectory=contrib/agentseek-schedule-sqlalchemy"
```

## Configuration

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

- `AGENTSEEK_SCHEDULE_SQLALCHEMY_URL` or `BUB_SCHEDULE_SQLALCHEMY_URL`: primary SQLAlchemy database URL for APScheduler jobs
- `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` or `BUB_TAPESTORE_SQLALCHEMY_URL`: fallback database URL when the schedule-specific URL is unset
- `AGENTSEEK_SCHEDULE_SQLALCHEMY_TABLENAME` or `BUB_SCHEDULE_SQLALCHEMY_TABLENAME`: optional table name
- table name defaults to `apscheduler_jobs`

Resolution order:

1. use the schedule-specific URL from environment or `.env` when set
2. otherwise fall back to the shared tapestore SQLAlchemy URL from environment or `.env`
3. otherwise use `config.yml` `schedule.url` when present
4. otherwise scheduler creation may fail and the plugin will log a warning and stay disabled

When both prefixes are present for the same setting, the `BUB_*` value wins. This keeps the plugin
compatible with plain Bub while matching agentseek's global alias behavior.

Example:

```bash
export AGENTSEEK_SCHEDULE_SQLALCHEMY_URL=sqlite:////tmp/agentseek-schedule.sqlite
```

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

## Test-Covered Behavior

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

## Limitations

- this package only provides scheduling infrastructure; actual reminder delivery still depends on the surrounding Bub runtime or agentseek distribution setup and enabled channels
- session scoping is based on the `session_id` stored in job kwargs
- persistence quality and locking semantics depend on the configured SQLAlchemy backend
