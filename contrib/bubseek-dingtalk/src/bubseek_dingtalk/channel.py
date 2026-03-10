"""DingTalk channel adapter using Stream Mode."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from bub.channels import Channel
from bub.channels.message import ChannelMessage
from bub.types import MessageHandler
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from dingtalk_stream import (
        AckMessage,
        CallbackHandler,
        CallbackMessage,
        Credential,
        DingTalkStreamClient,
    )
    from dingtalk_stream.chatbot import ChatbotMessage

    DINGTALK_AVAILABLE = True
except ImportError:
    DINGTALK_AVAILABLE = False
    CallbackHandler = object  # type: ignore[assignment,misc]
    CallbackMessage = None  # type: ignore[assignment,misc]
    AckMessage = None  # type: ignore[assignment,misc]
    ChatbotMessage = None  # type: ignore[assignment,misc]



class DingTalkConfig(BaseSettings):
    """DingTalk channel config."""

    model_config = SettingsConfigDict(
        env_prefix="BUB_DINGTALK_",
        env_file=".env",
        extra="ignore",
    )

    client_id: str = ""
    client_secret: str = ""
    allow_users: str = ""  # Comma-separated staff_ids, or "*" for all


def _parse_allow_users(value: str) -> set[str]:
    if not value or not value.strip():
        return set()
    v = value.strip()
    if v == "*":
        return {"*"}
    return {u.strip() for u in v.split(",") if u.strip()}


class DingTalkCallbackHandler(CallbackHandler):
    """DingTalk Stream callback handler; forwards messages to Bub."""

    def __init__(self, channel: DingTalkChannel) -> None:
        super().__init__()
        self.channel = channel

    async def process(self, message: CallbackMessage) -> tuple[int, str]:
        """Process incoming stream message."""
        try:
            chatbot_msg = ChatbotMessage.from_dict(message.data)
            content = ""
            if chatbot_msg.text:
                content = (chatbot_msg.text.content or "").strip()
            if not content:
                content = message.data.get("text", {}).get("content", "").strip()

            if not content:
                logger.warning(
                    "DingTalk: empty or unsupported message type: {}",
                    getattr(chatbot_msg, "message_type", "?"),
                )
                return AckMessage.STATUS_OK, "OK"

            sender_id = chatbot_msg.sender_staff_id or chatbot_msg.sender_id or ""
            sender_name = chatbot_msg.sender_nick or "Unknown"
            conversation_type = message.data.get("conversationType")
            conversation_id = message.data.get("conversationId") or message.data.get("openConversationId")

            logger.info(
                "DingTalk inbound from {} ({}): {}",
                sender_name,
                sender_id,
                content[:80],
            )

            task = asyncio.create_task(
                self.channel._on_message(
                    content=content,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    conversation_type=conversation_type,
                    conversation_id=conversation_id,
                )
            )
            self.channel._background_tasks.add(task)
            task.add_done_callback(self.channel._background_tasks.discard)

        except Exception as e:
            logger.error("DingTalk process error: {}", e)
            return AckMessage.STATUS_OK, "Error"
        else:
            return AckMessage.STATUS_OK, "OK"


class DingTalkChannel(Channel):
    """DingTalk channel using Stream Mode (WebSocket receive, HTTP send)."""

    name = "dingtalk"

    def __init__(self, on_receive: MessageHandler) -> None:
        self._on_receive = on_receive
        self._config = DingTalkConfig()
        self._allow_users = _parse_allow_users(self._config.allow_users)
        self._client: Any = None
        self._background_tasks: set[asyncio.Task] = set()
        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None
        self._stream_task: asyncio.Task | None = None

    def _is_allowed(self, sender_id: str) -> bool:
        if not self._allow_users:
            return False
        if "*" in self._allow_users:
            return True
        return str(sender_id) in self._allow_users

    async def start(self, stop_event: asyncio.Event) -> None:
        """Start DingTalk Stream client."""
        self._stop_event = stop_event
        if not DINGTALK_AVAILABLE:
            logger.error("dingtalk-stream not installed. Run: pip install dingtalk-stream")
            return
        if not self._config.client_id or not self._config.client_secret:
            logger.error("DingTalk client_id/client_secret not configured")
            return

        self._main_loop = asyncio.get_running_loop()

        credential = Credential(self._config.client_id, self._config.client_secret)
        self._client = DingTalkStreamClient(credential)
        handler = DingTalkCallbackHandler(self)
        self._client.register_callback_handler(ChatbotMessage.TOPIC, handler)

        logger.info("DingTalk channel starting (Stream Mode)")

        async def _run_stream() -> None:
            while not (self._stop_event and self._stop_event.is_set()):
                try:
                    await self._client.start()
                except Exception as e:
                    logger.warning("DingTalk stream error: {}", e)
                if self._stop_event and self._stop_event.is_set():
                    break
                logger.info("DingTalk reconnecting in 5s...")
                await asyncio.sleep(5)

        self._stream_task = asyncio.create_task(_run_stream())

    async def stop(self) -> None:
        """Stop DingTalk channel."""
        if self._stop_event:
            self._stop_event.set()
        for task in self._background_tasks:
            task.cancel()
        self._background_tasks.clear()
        if self._stream_task:
            self._stream_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._stream_task
            self._stream_task = None
        self._client = None
        logger.info("DingTalk channel stopped")

    async def send(self, message: ChannelMessage) -> None:
        """Send message to DingTalk via skill."""
        content = (message.content or "").strip()
        logger.info(
            "DingTalk send: called session_id={} chat_id={} content_len={}",
            message.session_id,
            message.chat_id,
            len(content),
        )

        chat_id = message.chat_id or ""
        if not chat_id and message.session_id:
            _, _, chat_id = message.session_id.partition(":")
        if not chat_id:
            logger.warning("DingTalk send: no chat_id session_id={}", message.session_id)
            return

        if not content:
            logger.warning("DingTalk send: skipping empty content session_id={}", message.session_id)
            return

        logger.info("DingTalk send: sending chat_id={} content_len={}", chat_id, len(content))
        try:
            from bub_skills.dingtalk.send import send_message

            await asyncio.to_thread(
                send_message,
                self._config.client_id,
                self._config.client_secret,
                chat_id,
                content,
                title="Bub Reply",
                verify=False,
            )
            logger.info("DingTalk send: success chat_id={}", chat_id)
        except Exception as e:
            logger.error("DingTalk send failed for chat_id={} error={}", chat_id, e)

    async def _on_message(
        self,
        content: str,
        sender_id: str,
        sender_name: str,
        conversation_type: str | None = None,
        conversation_id: str | None = None,
    ) -> None:
        """Handle incoming message from callback handler."""
        if not self._is_allowed(sender_id):
            logger.warning("DingTalk inbound denied: sender_id={}", sender_id)
            return

        is_group = conversation_type == "2" and conversation_id
        chat_id = f"group:{conversation_id}" if is_group else sender_id
        session_id = f"{self.name}:{chat_id}"

        is_command = content.strip().startswith(",")
        channel_msg = ChannelMessage(
            session_id=session_id,
            content=content,
            channel=self.name,
            chat_id=chat_id,
            kind="command" if is_command else "normal",
            is_active=True,
        )
        logger.debug("DingTalk inbound session_id={} content={}", session_id, content[:50])
        await self._on_receive(channel_msg)
