"""Tests for agentseek-schedule-sqlalchemy."""

import asyncio
import importlib
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import yaml
from agentseek_schedule_sqlalchemy import tools
from agentseek_schedule_sqlalchemy.config import (
    ScheduleSQLAlchemySettings,
    get_schedule_settings,
    onboard_config,
)
from agentseek_schedule_sqlalchemy.job_store import build_sqlalchemy_jobstore
from agentseek_schedule_sqlalchemy.plugin import ScheduleImpl, _default_scheduler, build_scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from republic import ToolContext


def _test_table_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _sqlite_url(tmp_path, filename: str) -> str:
    return f"sqlite:///{tmp_path / filename}"


def _trigger_result(value: object) -> str:
    result = asyncio.run(value) if asyncio.iscoroutine(value) else value
    assert isinstance(result, str)
    return result


def _trigger(job_id: str, context: ToolContext) -> str:
    handler = tools.schedule_trigger.handler
    if handler is None:
        raise RuntimeError("schedule.trigger handler is not registered")

    return _trigger_result(handler(job_id, context=context))


def _load_bub_config(config_path) -> None:
    configure = importlib.import_module("bub.configure")
    configure.load(config_path)


@pytest.fixture(autouse=True)
def _reset_bub_config(tmp_path, monkeypatch) -> Iterator[None]:
    # Isolate from os.environ pollution (e.g. tests/test_env.py applies AGENTSEEK_* → BUB_* via setdefault).
    monkeypatch.chdir(tmp_path)
    for key in (
        "BUB_SCHEDULE_SQLALCHEMY_URL",
        "AGENTSEEK_SCHEDULE_SQLALCHEMY_URL",
        "BUB_TAPESTORE_SQLALCHEMY_URL",
        "AGENTSEEK_TAPESTORE_SQLALCHEMY_URL",
        "BUB_SCHEDULE_SQLALCHEMY_TABLENAME",
        "AGENTSEEK_SCHEDULE_SQLALCHEMY_TABLENAME",
    ):
        monkeypatch.delenv(key, raising=False)
    config_path = tmp_path / "empty-config.yml"
    _load_bub_config(config_path)
    yield
    _load_bub_config(config_path)


def test_jobstore_roundtrip_with_sqlite(tmp_path) -> None:
    """Built-in SQLAlchemyJobStore should persist jobs without agentseek helpers."""
    settings = ScheduleSQLAlchemySettings(
        url=_sqlite_url(tmp_path, "roundtrip.sqlite"),
        tablename=_test_table_name("apscheduler_jobs_test_roundtrip"),
    )
    store = build_sqlalchemy_jobstore(settings=settings)
    scheduler = build_scheduler(jobstore=store)
    scheduler.start()

    scheduler.add_job(
        "agentseek_schedule_sqlalchemy.jobs:_noop",
        "date",
        run_date=datetime.now(UTC) + timedelta(minutes=1),
        id="test-1",
    )
    assert store.lookup_job("test-1") is not None
    jobs = store.get_all_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "test-1"

    scheduler.remove_job("test-1")
    assert store.lookup_job("test-1") is None
    scheduler.shutdown()


def test_schedule_impl_uses_injected_scheduler(tmp_path) -> None:
    settings = ScheduleSQLAlchemySettings(
        url=_sqlite_url(tmp_path, "plugin.sqlite"),
        tablename=_test_table_name("apscheduler_jobs_test_plugin"),
    )
    store = build_sqlalchemy_jobstore(settings=settings)
    scheduler = build_scheduler(jobstore=store)
    plugin = ScheduleImpl.from_scheduler(scheduler)

    async def _message_handler(_message: object) -> None:
        return None

    state = plugin.load_state(message=None, session_id="schedule:test")

    assert state["scheduler"] is scheduler
    assert scheduler.running
    assert [channel.name for channel in plugin.provide_channels(message_handler=_message_handler)] == ["schedule"]


def test_onboard_config_can_skip_schedule_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        "agentseek_schedule_sqlalchemy.config.bub_inquirer.ask_confirm", lambda message, default=False: False
    )

    config = onboard_config(current_config={})

    assert config is None


def test_onboard_config_collects_schedule_section(monkeypatch) -> None:
    answers = iter([
        True,
        "sqlite+pysqlite:///./schedule.sqlite",
        "custom_schedule_jobs",
    ])

    monkeypatch.setattr(
        "agentseek_schedule_sqlalchemy.config.bub_inquirer.ask_confirm",
        lambda message, default=False: next(answers),
    )
    monkeypatch.setattr(
        "agentseek_schedule_sqlalchemy.config.bub_inquirer.ask_text",
        lambda message, default="": next(answers),
    )

    config = onboard_config(current_config={})

    assert config == {
        "schedule": {
            "url": "sqlite+pysqlite:///./schedule.sqlite",
            "tablename": "custom_schedule_jobs",
        }
    }


def test_onboard_config_reuses_existing_schedule_defaults(monkeypatch) -> None:
    prompts: list[tuple[str, str]] = []

    monkeypatch.setattr(
        "agentseek_schedule_sqlalchemy.config.bub_inquirer.ask_confirm",
        lambda message, default=False: True,
    )

    def _ask_text(message: str, default: str = "") -> str:
        prompts.append((message, default))
        return default

    monkeypatch.setattr(
        "agentseek_schedule_sqlalchemy.config.bub_inquirer.ask_text",
        _ask_text,
    )

    config = onboard_config(
        current_config={
            "schedule": {
                "url": "sqlite+pysqlite:///./existing.sqlite",
                "tablename": "existing_schedule_jobs",
            }
        }
    )

    assert prompts == [
        ("Schedule SQLAlchemy URL (optional)", "sqlite+pysqlite:///./existing.sqlite"),
        ("Schedule table name", "existing_schedule_jobs"),
    ]
    assert config == {
        "schedule": {
            "url": "sqlite+pysqlite:///./existing.sqlite",
            "tablename": "existing_schedule_jobs",
        }
    }


def test_registered_schedule_settings_support_config_section(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    config_data = {
        "schedule": {
            "url": _sqlite_url(tmp_path, "config.sqlite"),
            "tablename": "schedule_jobs_from_config",
        }
    }
    config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    _load_bub_config(config_path)

    settings = get_schedule_settings()

    assert settings.url == _sqlite_url(tmp_path, "config.sqlite")
    assert settings.tablename == "schedule_jobs_from_config"


def test_registered_schedule_settings_env_override_config(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    config_data = {
        "schedule": {
            "url": _sqlite_url(tmp_path, "config.sqlite"),
            "tablename": "schedule_jobs_from_config",
        }
    }
    config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    _load_bub_config(config_path)
    monkeypatch.setenv("BUB_SCHEDULE_SQLALCHEMY_URL", _sqlite_url(tmp_path, "env.sqlite"))

    settings = get_schedule_settings()

    assert settings.url == _sqlite_url(tmp_path, "env.sqlite")
    assert settings.tablename == "schedule_jobs_from_config"


def test_default_scheduler_uses_registered_schedule_settings(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    config_data = {
        "schedule": {
            "url": _sqlite_url(tmp_path, "registered.sqlite"),
            "tablename": "jobs_from_registered_settings",
        }
    }
    config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    _load_bub_config(config_path)

    scheduler = _default_scheduler()

    try:
        assert scheduler._jobstores["default"].jobs_t.name == "jobs_from_registered_settings"
        assert str(scheduler._jobstores["default"].engine.url) == _sqlite_url(tmp_path, "registered.sqlite")
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


def test_sqlalchemy_settings_support_env(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTSEEK_SCHEDULE_SQLALCHEMY_URL", _sqlite_url(tmp_path, "env.sqlite"))
    monkeypatch.delenv("BUB_SCHEDULE_SQLALCHEMY_URL", raising=False)

    settings = ScheduleSQLAlchemySettings()

    assert settings.url == _sqlite_url(tmp_path, "env.sqlite")
    assert settings.tablename == "apscheduler_jobs"


def test_sqlalchemy_settings_keep_bub_env_compatible(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUB_SCHEDULE_SQLALCHEMY_URL", _sqlite_url(tmp_path, "bub.sqlite"))
    monkeypatch.delenv("AGENTSEEK_SCHEDULE_SQLALCHEMY_URL", raising=False)

    settings = ScheduleSQLAlchemySettings()

    assert settings.url == _sqlite_url(tmp_path, "bub.sqlite")


def test_sqlalchemy_settings_prefer_bub_env_over_agentseek_alias(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUB_SCHEDULE_SQLALCHEMY_URL", _sqlite_url(tmp_path, "bub.sqlite"))
    monkeypatch.setenv("AGENTSEEK_SCHEDULE_SQLALCHEMY_URL", _sqlite_url(tmp_path, "agentseek.sqlite"))

    settings = ScheduleSQLAlchemySettings()

    assert settings.url == _sqlite_url(tmp_path, "bub.sqlite")


def test_sqlalchemy_settings_fallback_to_tapestore_env(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUB_SCHEDULE_SQLALCHEMY_URL", raising=False)
    monkeypatch.delenv("AGENTSEEK_SCHEDULE_SQLALCHEMY_URL", raising=False)
    monkeypatch.setenv("AGENTSEEK_TAPESTORE_SQLALCHEMY_URL", _sqlite_url(tmp_path, "tapestore.sqlite"))
    monkeypatch.delenv("BUB_TAPESTORE_SQLALCHEMY_URL", raising=False)

    settings = ScheduleSQLAlchemySettings()

    assert settings.url == _sqlite_url(tmp_path, "tapestore.sqlite")
    assert settings.tablename == "apscheduler_jobs"


def test_sqlalchemy_settings_allow_missing_url(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUB_SCHEDULE_SQLALCHEMY_URL", raising=False)
    monkeypatch.delenv("AGENTSEEK_SCHEDULE_SQLALCHEMY_URL", raising=False)

    settings = ScheduleSQLAlchemySettings()

    assert settings.url is None
    assert settings.tablename == "apscheduler_jobs"


def test_sqlalchemy_settings_support_prefixed_table_name(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTSEEK_SCHEDULE_SQLALCHEMY_TABLENAME", "agentseek_jobs")
    monkeypatch.delenv("BUB_SCHEDULE_SQLALCHEMY_TABLENAME", raising=False)

    settings = ScheduleSQLAlchemySettings(url=_sqlite_url(tmp_path, "table.sqlite"))

    assert settings.tablename == "agentseek_jobs"


@pytest.fixture
def scheduler() -> Iterator[BackgroundScheduler]:
    scheduler = BackgroundScheduler()
    scheduler.start()
    yield scheduler
    scheduler.shutdown(wait=False)


@pytest.fixture
def tool_context(scheduler: BackgroundScheduler) -> ToolContext:
    return ToolContext(
        tape=None,
        run_id="test-run",
        state={"scheduler": scheduler, "session_id": "test-session"},
    )


def test_schedule_trigger_executes_sync_job_without_shifting_next_run(
    scheduler: BackgroundScheduler, tool_context: ToolContext
) -> None:
    execution_log: list[dict[str, Any]] = []

    def sync_job(value: str) -> None:
        execution_log.append({"value": value, "timestamp": datetime.now(UTC)})

    next_run = datetime.now(UTC) + timedelta(hours=1)
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(minutes=5),
        id="sync-job",
        kwargs={"value": "payload"},
        next_run_time=next_run,
    )

    result = _trigger("sync-job", tool_context)

    assert len(execution_log) == 1
    assert execution_log[0]["value"] == "payload"
    assert scheduler.get_job("sync-job") is not None
    assert scheduler.get_job("sync-job").next_run_time == next_run
    assert "triggered: sync-job" in result
    assert next_run.isoformat() in result


def test_schedule_trigger_executes_async_job(scheduler: BackgroundScheduler, tool_context: ToolContext) -> None:
    execution_log: list[str] = []

    async def async_job(value: str) -> None:
        await asyncio.sleep(0.01)
        execution_log.append(value)

    scheduler.add_job(
        async_job,
        trigger=IntervalTrigger(minutes=5),
        id="async-job",
        args=["payload"],
        next_run_time=datetime.now(UTC) + timedelta(hours=1),
    )

    result = _trigger("async-job", tool_context)

    assert execution_log == ["payload"]
    assert "triggered: async-job" in result


def test_schedule_trigger_raises_for_missing_job(tool_context: ToolContext) -> None:
    with pytest.raises(RuntimeError, match="job not found: missing-job"):
        _trigger("missing-job", tool_context)
