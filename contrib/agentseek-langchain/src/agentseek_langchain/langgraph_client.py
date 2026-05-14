from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from agentseek_langchain.shapes import as_str_mapping


class LangGraphRunsProtocol(Protocol):
    async def wait(
        self,
        thread_id: str | None,
        assistant_id: str,
        *,
        runnable_input: object | None = None,
        metadata: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
        if_not_exists: str | None = None,
        **kwargs: object,
    ) -> object: ...


class LangGraphClientProtocol(Protocol):
    runs: LangGraphRunsProtocol


@dataclass(frozen=True, slots=True)
class LangGraphClientRunnable:
    client: LangGraphClientProtocol
    assistant_id: str
    thread_on_session: bool = True

    def __post_init__(self) -> None:
        if not self.assistant_id.strip():
            raise ValueError("assistant_id must not be empty")

    async def ainvoke(
        self,
        runnable_input: object,
        config: Mapping[str, object] | None = None,
    ) -> object:
        thread_id = _thread_id_from_config(config, enabled=self.thread_on_session)
        metadata = _mapping_or_none(config, "metadata")
        run_config = _assistant_config_from_config(config)
        if_not_exists = "create" if thread_id is not None else None
        return await self.client.runs.wait(
            thread_id,
            self.assistant_id,
            input=runnable_input,
            metadata=metadata,
            config=run_config,
            if_not_exists=if_not_exists,
        )


def _thread_id_from_config(config: Mapping[str, object] | None, *, enabled: bool) -> str | None:
    if not enabled or config is None:
        return None
    configurable = _mapping_or_none(config, "configurable")
    if configurable is None:
        return None
    for key in ("thread_id", "session_id"):
        value = configurable.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _assistant_config_from_config(config: Mapping[str, object] | None) -> dict[str, object] | None:
    configurable = _mapping_or_none(config, "configurable")
    if configurable is None:
        return None
    assistant_config = {key: value for key, value in configurable.items() if key not in {"thread_id", "session_id"}}
    return assistant_config or None


def _mapping_or_none(config: Mapping[str, object] | None, key: str) -> Mapping[str, Any] | None:
    if config is None:
        return None
    return as_str_mapping(config.get(key))
