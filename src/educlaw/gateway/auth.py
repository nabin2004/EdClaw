"""Pairing tokens + idempotent WS responses."""

from __future__ import annotations

from dataclasses import dataclass

from cachetools import TTLCache


@dataclass
class ClientContext:
    user_id: str
    session_id: str


_idempotency: TTLCache[tuple[str, str], dict] = TTLCache(maxsize=4096, ttl=3600)


def verify_pairing_token(token: str) -> ClientContext:
    """MVP: accept any non-empty token as authenticated local client."""
    if not token or not str(token).strip():
        raise ValueError("invalid token")
    # Token format optional: "user_id:session_id" or opaque
    if ":" in token:
        user_id, session_id = token.split(":", 1)
    else:
        user_id = "local_user"
        session_id = token.strip()[:128]
    return ClientContext(user_id=user_id, session_id=session_id)


def idempotency_get(client_key: str, idem_key: str | None) -> dict | None:
    if not idem_key:
        return None
    return _idempotency.get((client_key, idem_key))


def idempotency_put(client_key: str, idem_key: str | None, payload: dict) -> None:
    if idem_key:
        _idempotency[(client_key, idem_key)] = payload
