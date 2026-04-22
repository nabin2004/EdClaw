"""WebChat channel: envelopes produced by the gateway WS layer (reference)."""

from __future__ import annotations

from datetime import UTC, datetime

from educlaw.channels.contract import InboundEnvelope


def envelope_from_webchat(*, user_id: str, session_id: str, text: str) -> InboundEnvelope:
    return InboundEnvelope(
        channel_id="webchat",
        thread_id=session_id,
        user_id=user_id,
        user_display=user_id,
        text=text,
        received_at=datetime.now(UTC),
    )
