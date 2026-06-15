import asyncio
import contextlib
from asyncio import Event
from typing import ClassVar

from apscheduler.schedulers import SchedulerAlreadyRunningError
from apscheduler.schedulers.base import BaseScheduler
from bub.channels import Lifecycle
from bub.channels.message import ChannelMessage
from loguru import logger


class ScheduleChannel(Lifecycle):
    """Starts/stops BackgroundScheduler when this channel is enabled (e.g. gateway)."""

    name: ClassVar[str] = "schedule"
    _framework: ClassVar[object | None] = None
    _loop: ClassVar[asyncio.AbstractEventLoop | None] = None

    def __init__(self, scheduler: BaseScheduler, *, framework: object | None = None) -> None:
        self.scheduler = scheduler
        self._instance_framework = framework

    @classmethod
    def bind_framework(cls, framework: object | None, loop: asyncio.AbstractEventLoop | None = None) -> None:
        if framework is None:
            return
        cls._framework = framework
        cls._loop = loop

    @classmethod
    def clear_framework(cls, framework: object | None = None) -> None:
        if framework is not None and cls._framework is not framework:
            return
        cls._framework = None
        cls._loop = None

    @classmethod
    def current_framework(cls) -> object:
        if cls._framework is None:
            raise RuntimeError("no live schedule framework available, cannot deliver scheduled message")
        return cls._framework

    @classmethod
    async def dispatch_message(cls, message: ChannelMessage) -> None:
        framework = cls.current_framework()
        process_inbound = framework.process_inbound
        await process_inbound(message)

    @classmethod
    def dispatch_message_sync(cls, message: ChannelMessage) -> None:
        framework = cls.current_framework()
        process_inbound = framework.process_inbound
        loop = cls._loop
        if loop is not None and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(process_inbound(message), loop)
            future.result()
            return
        asyncio.run(process_inbound(message))

    async def start(self, stop_event: Event) -> None:
        self.bind_framework(self._instance_framework, asyncio.get_running_loop())
        if not self.scheduler.running:
            with contextlib.suppress(SchedulerAlreadyRunningError):
                self.scheduler.start()
        logger.info("schedule.start complete")

    async def stop(self) -> None:
        if not self.scheduler.running:
            logger.info("schedule.stop complete (idle)")
            return
        # BackgroundScheduler.shutdown() blocks until the worker thread stops.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: self.scheduler.shutdown(wait=True))
        self.clear_framework(self._instance_framework)
        logger.info("schedule.stop complete")
