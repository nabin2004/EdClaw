"""Discover channel plugins via ``importlib.metadata`` entry points."""

from __future__ import annotations

import importlib.metadata


def load_channel_factories(group: str = "educlaw.channels") -> dict[str, object]:
    eps = importlib.metadata.entry_points()
    if hasattr(eps, "select"):
        selected = list(eps.select(group=group))
    else:
        raw = eps.get(group)
        selected = list(raw) if raw is not None else []
    out: dict[str, object] = {}
    for ep in selected:
        out[ep.name] = ep.load()
    return out
