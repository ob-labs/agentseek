from collections.abc import Callable, Mapping
from typing import Any

from apscheduler.jobstores.base import BaseJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler
from bub import hookimpl
from bub.channels import Channel
from bub.framework import BubFramework
from bub.types import Envelope, MessageHandler, State
from loguru import logger

from agentseek_schedule_sqlalchemy.config import (
    ScheduleSQLAlchemySettings,
    get_schedule_settings,
)
from agentseek_schedule_sqlalchemy.config import (
    onboard_config as collect_onboard_config,
)
from agentseek_schedule_sqlalchemy.job_store import build_sqlalchemy_jobstore

SchedulerFactory = Callable[[], BaseScheduler]


def build_scheduler(*, jobstore: BaseJobStore, jobstore_alias: str = "default") -> BaseScheduler:
    return AsyncIOScheduler(jobstores={jobstore_alias: jobstore})


def build_sqlalchemy_scheduler(
    *,
    settings: ScheduleSQLAlchemySettings,
    engine_options: Mapping[str, Any] | None = None,
    jobstore_alias: str = "default",
) -> BaseScheduler:
    jobstore = build_sqlalchemy_jobstore(settings=settings, engine_options=engine_options)
    return build_scheduler(jobstore=jobstore, jobstore_alias=jobstore_alias)


def _default_scheduler() -> BaseScheduler:
    return build_sqlalchemy_scheduler(settings=get_schedule_settings())


class ScheduleImpl:
    """Schedule plugin backed by an APScheduler SQLAlchemy job store."""

    def __init__(
        self, framework: BubFramework | None = None, scheduler_factory: SchedulerFactory | None = None
    ) -> None:
        from agentseek_schedule_sqlalchemy import tools  # noqa: F401

        self.framework = framework
        self._scheduler_factory = scheduler_factory or _default_scheduler
        self._scheduler: BaseScheduler | None = None

    @classmethod
    def from_scheduler(cls, scheduler: BaseScheduler, framework: BubFramework | None = None) -> "ScheduleImpl":
        return cls(framework=framework, scheduler_factory=lambda: scheduler)

    @property
    def scheduler(self) -> BaseScheduler:
        if self._scheduler is None:
            self._scheduler = self._scheduler_factory()
        return self._scheduler

    @hookimpl
    def load_state(self, message: Envelope, session_id: str) -> State:
        return {"scheduler": self.scheduler}

    @hookimpl
    def onboard_config(self, current_config: dict[str, Any]) -> dict[str, Any] | None:
        return collect_onboard_config(current_config)

    @hookimpl
    def provide_channels(self, message_handler: MessageHandler) -> list[Channel]:
        from agentseek_schedule_sqlalchemy.channel import ScheduleChannel

        try:
            scheduler = self.scheduler
        except Exception as exc:
            logger.warning(f"Schedule plugin disabled: {exc}")
            return []
        return [ScheduleChannel(scheduler, framework=self.framework)]
