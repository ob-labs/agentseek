from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from agentseek_schedule_sqlalchemy.config import ScheduleSQLAlchemySettings


def build_sqlalchemy_jobstore(
    *,
    settings: ScheduleSQLAlchemySettings,
    engine_options: Mapping[str, Any] | None = None,
) -> SQLAlchemyJobStore:
    return SQLAlchemyJobStore(
        url=settings.url,
        tablename=settings.tablename,
        engine_options=dict(engine_options or {}),
    )
