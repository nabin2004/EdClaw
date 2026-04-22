"""Telegram channel adapter (stub — use ``pip install 'educlaw[channels]'``)."""

from __future__ import annotations

from educlaw.channels.contract import OutboundMessage


class TelegramChannelStub:
    """Placeholder; replace with python-telegram-bot Application integration."""

    id = "telegram"

    async def start(self):
        raise NotImplementedError("TelegramChannelStub.start")

    async def send(self, msg: OutboundMessage) -> None:
        raise NotImplementedError("TelegramChannelStub.send")

    async def stop(self) -> None:
        return None
