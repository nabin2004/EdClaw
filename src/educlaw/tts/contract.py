from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from educlaw.config.settings import Settings


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    sample_rate: int = Field(default=24000, ge=8000, le=48000)


class TTSAudio(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio_bytes: bytes
    sample_rate: int
    voice: str | None = None
    format: Literal["wav"] = "wav"


@runtime_checkable
class TTSBackend(Protocol):
    name: str
    available_voices: list[str]

    async def synthesize(self, req: TTSRequest) -> TTSAudio: ...

    async def close(self) -> None: ...


TTSBackendFactory = Callable[["Settings"], TTSBackend]
