"""CLI channel (Typer) — thin adapter for local testing."""

from __future__ import annotations

from datetime import UTC, datetime

from educlaw.channels.contract import InboundEnvelope


def envelope_from_cli(*, user_id: str, text: str) -> InboundEnvelope:
    return InboundEnvelope(
        channel_id="cli",
        thread_id="cli",
        user_id=user_id,
        user_display=user_id,
        text=text,
        received_at=datetime.now(UTC),
    )
