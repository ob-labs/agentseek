from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from .bridge import LangchainRunContext, RunnableBinding, build_runnable_config


@dataclass(frozen=True)
class RunnableExecutor:
    binding: RunnableBinding
    run_context: LangchainRunContext
    callbacks: list[Any]

    @property
    def _invoke_kwargs(self) -> dict[str, Any]:
        return {
            "config": build_runnable_config(
                langchain_context=self.run_context,
                callbacks=self.callbacks,
            )
        }

    async def ainvoke_text(self) -> str:
        output = await self.binding.runnable.ainvoke(
            self.binding.invoke_input,
            **self._invoke_kwargs,
        )
        return self._parse_output(output)

    async def astream_text(self) -> AsyncIterator[str]:
        astream = getattr(self.binding.runnable, "astream", None)
        if not callable(astream) or self.binding.stream_parser is None:
            yield await self.ainvoke_text()
            return

        async for chunk in astream(self.binding.invoke_input, **self._invoke_kwargs):
            text = self.binding.stream_parser(chunk)
            if text:
                yield text

    def _parse_output(self, value: Any) -> str:
        parser = self.binding.output_parser
        if parser is None:
            raise RuntimeError("RunnableBinding.output_parser must be resolved before execution")
        return parser(value)
