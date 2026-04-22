"""HTTP webhooks for channel adapters."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/webhooks/{channel_id}")
async def channel_webhook(channel_id: str, body: dict) -> dict:
    # MVP: echo; Telegram/Discord register handlers via entry points later.
    if channel_id not in {"telegram", "discord", "matrix", "debug"}:
        raise HTTPException(status_code=404, detail="unknown channel")
    return {"ok": True, "channel_id": channel_id, "received": bool(body)}
