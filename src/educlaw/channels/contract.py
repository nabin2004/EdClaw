from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel


class Attachment(BaseModel):
    kind: Literal["image", "audio", "file"]
    url: str | None = None
    bytes_b64: str | None = None
    mime: str


class InboundEnvelope(BaseModel):
    channel_id: str
    thread_id: str
    user_id: str
    user_display: str
    text: str | None = None
    attachments: list[Attachment] = []
    received_at: datetime


class OutboundMessage(BaseModel):
    thread_id: str
    text: str | None = None
    attachments: list[Attachment] = []


@runtime_checkable
class Channel(Protocol):
    id: str

    async def start(self): ...  # pragma: no cover

    async def send(self, msg: OutboundMessage) -> None: ...

    async def stop(self) -> None: ...
