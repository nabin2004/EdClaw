"""Serialize ADK ``Event`` objects for WebSocket JSON."""

from __future__ import annotations

from typing import Any


def event_to_wire(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        try:
            return {"type": "adk_event", "payload": obj.model_dump(mode="json", exclude_none=True)}
        except TypeError:
            return {"type": "adk_event", "payload": obj.model_dump(exclude_none=True)}
    return {"type": "adk_event", "repr": repr(obj)}
