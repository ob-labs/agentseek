"""
Test that DingTalk inbound messages correctly reach the agent loop.

Simulates the full path:
  DingTalk _on_message -> ChannelMessage -> on_receive -> process_inbound -> agent
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from bub.channels.message import ChannelMessage
from bub.framework import BubFramework


def _make_dingtalk_inbound(
    content: str = "hello",
    sender_id: str = "204818006723348842",
    conversation_type: str | None = None,
    conversation_id: str | None = None,
) -> ChannelMessage:
    """Build ChannelMessage exactly as DingTalkChannel._on_message would."""
    is_group = conversation_type == "2" and conversation_id
    chat_id = f"group:{conversation_id}" if is_group else sender_id
    session_id = f"dingtalk:{chat_id}"
    is_command = content.strip().startswith(",")
    return ChannelMessage(
        session_id=session_id,
        content=content,
        channel="dingtalk",
        chat_id=chat_id,
        kind="command" if is_command else "normal",
        is_active=True,
    )


def test_dingtalk_inbound_message_format() -> None:
    """Verify DingTalk _on_message produces correct ChannelMessage format."""
    inbound = _make_dingtalk_inbound(content="hi")
    assert inbound.session_id == "dingtalk:204818006723348842"
    assert inbound.chat_id == "204818006723348842"
    assert inbound.channel == "dingtalk"
    assert inbound.context.get("channel") == "$dingtalk"
    assert inbound.context.get("chat_id") == "204818006723348842"
    assert inbound.context_str  # Used by build_prompt


def test_dingtalk_inbound_reaches_agent(tmp_path: Path) -> None:
    """Verify DingTalk inbound flows through process_inbound to dispatch (requires LLM)."""

    async def _run() -> None:
        framework = BubFramework()
        framework.workspace = tmp_path
        framework.load_hooks()

        inbound = _make_dingtalk_inbound(content="hi")
        outbounds_captured: list = []

        class CaptureRouter:
            async def dispatch(self, message) -> bool:
                outbounds_captured.append(message)
                return True

        framework.bind_outbound_router(CaptureRouter())
        try:
            result = await framework.process_inbound(inbound)
        finally:
            framework.bind_outbound_router(None)

        assert result.session_id == "dingtalk:204818006723348842"
        assert len(result.outbounds) >= 1
        assert len(outbounds_captured) >= 1

        out = outbounds_captured[0]
        assert out.channel == "dingtalk"
        assert out.chat_id == "204818006723348842"
        assert out.session_id == "dingtalk:204818006723348842"

    asyncio.run(_run())


def _run_simulation() -> None:
    """Run simulation from CLI for manual verification."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    workspace = Path.cwd()
    if (workspace / "contrib" / "bubseek-dingtalk").exists():
        workspace = workspace.parent

    framework = BubFramework()
    framework.workspace = workspace
    framework.load_hooks()

    inbound = _make_dingtalk_inbound(content="hello, reply me")
    print(f"[1] Inbound: session_id={inbound.session_id} chat_id={inbound.chat_id}")
    print(f"    context: {inbound.context}")

    outbounds: list = []

    class CaptureRouter:
        async def dispatch(self, message) -> bool:
            outbounds.append(message)
            print(
                f"[2] Dispatch: channel={message.channel} chat_id={message.chat_id} content_len={len(message.content or '')}"
            )
            return True

    framework.bind_outbound_router(CaptureRouter())
    try:
        result = asyncio.run(framework.process_inbound(inbound))
        print(f"[3] Result: session_id={result.session_id} outbounds={len(result.outbounds)}")
        for i, o in enumerate(outbounds):
            print(f"    outbound[{i}]: content={(o.content or '')[:100]!r}")
    finally:
        framework.bind_outbound_router(None)


def test_channel_manager_on_receive_to_process_inbound() -> None:
    """Verify message flows: on_receive -> queue -> process_inbound (no real channel start)."""

    async def _run() -> None:
        from bub.channels.manager import ChannelManager

        framework = BubFramework()
        framework.workspace = Path.cwd()
        framework.load_hooks()

        manager = ChannelManager(framework, enabled_channels=["dingtalk"])
        dingtalk_ch = manager.get_channel("dingtalk")
        assert dingtalk_ch is not None, "DingTalk channel must be registered"

        inbound = _make_dingtalk_inbound(content="test")
        outbounds: list = []

        class CaptureRouter:
            async def dispatch(self, message) -> bool:
                outbounds.append(message)
                return True

        framework.bind_outbound_router(CaptureRouter())

        await manager.on_receive(inbound)
        msg = await asyncio.wait_for(manager._messages.get(), timeout=2.0)
        assert msg.session_id == "dingtalk:204818006723348842"
        assert msg.content == "test"

        await framework.process_inbound(msg)
        framework.bind_outbound_router(None)

        assert len(outbounds) >= 1
        assert outbounds[0].channel == "dingtalk"
        assert outbounds[0].chat_id == "204818006723348842"

    asyncio.run(_run())


if __name__ == "__main__":
    _run_simulation()
