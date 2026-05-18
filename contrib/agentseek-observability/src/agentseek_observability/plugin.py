from __future__ import annotations

import logfire

from agentseek_observability._patches import InstrumentationHandle, PatchRegistry
from agentseek_observability.any_llm import instrument_any_llm
from agentseek_observability.bub import instrument_bub
from agentseek_observability.republic import instrument_republic

_handle: InstrumentationHandle | None = None


def instrument_agentseek_observability(
    logfire_instance: logfire.Logfire | None = None,
    *,
    force: bool = False,
) -> InstrumentationHandle:
    global _handle

    if _handle is not None and not force:
        return _handle
    if _handle is not None and force:
        _handle.close()

    resolved_logfire = logfire_instance or logfire.DEFAULT_LOGFIRE_INSTANCE
    patches = PatchRegistry()
    instrument_any_llm(resolved_logfire, patches)
    instrument_republic(resolved_logfire, patches)
    instrument_bub(resolved_logfire, patches)
    _handle = InstrumentationHandle(patches)
    return _handle


class ObservabilityPlugin:
    def __init__(self) -> None:
        instrument_agentseek_observability()

    def __repr__(self) -> str:
        return "ObservabilityPlugin()"


main = ObservabilityPlugin()

__all__ = ["instrument_agentseek_observability", "main"]
