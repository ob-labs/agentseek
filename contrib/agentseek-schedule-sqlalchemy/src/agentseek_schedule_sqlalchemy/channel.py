import asyncio
from asyncio import Event
from typing import ClassVar

from apscheduler.schedulers.base import BaseScheduler
from bub.channels import Lifecycle
from bub.framework import BubFramework
from loguru import logger


class ScheduleChannel(Lifecycle):
    """Starts/stops the scheduler and binds the live Bub framework."""

    name: ClassVar[str] = "schedule"
    _framework: ClassVar[BubFramework | None] = None

    def __init__(self, scheduler: BaseScheduler, *, framework: BubFramework | None = None) -> None:
        self.scheduler = scheduler
        self._instance_framework = framework

    @classmethod
    def current_framework(cls) -> BubFramework:
        if cls._framework is None:
            raise RuntimeError("no live schedule framework available, cannot deliver scheduled message")
        return cls._framework

    async def start(self, stop_event: Event) -> None:
        ScheduleChannel._framework = self._instance_framework

        loop = asyncio.get_running_loop()
        if not self.scheduler.running:
            loop.call_soon_threadsafe(self.scheduler.start)
        logger.info("schedule.start complete")

    async def stop(self) -> None:
        loop = asyncio.get_running_loop()
        if self.scheduler.running:
            loop.call_soon_threadsafe(self.scheduler.shutdown)

        ScheduleChannel._framework = None
        logger.info("schedule.stop complete")
