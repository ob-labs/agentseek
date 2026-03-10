"""Bub plugin entry for DingTalk channel."""

from bub import hookimpl
from bub.channels import Channel
from bub.types import MessageHandler

from . import ssl_patch  # noqa: F401 - apply websockets SSL patch before dingtalk_stream

from .channel import DingTalkChannel


@hookimpl
def provide_channels(message_handler: MessageHandler) -> list[Channel]:
    return [DingTalkChannel(message_handler)]
