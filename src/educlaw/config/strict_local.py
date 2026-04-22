"""Enforce loopback-only endpoints when ``strict_local`` is enabled."""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", None})


def hostname_allowed(url: str) -> bool:
    host = urlparse(url).hostname
    return host in ALLOWED_HOSTS


def assert_strict_local(*urls: str) -> None:
    for url in urls:
        if not url:
            continue
        host = urlparse(url).hostname
        if host not in ALLOWED_HOSTS:
            raise RuntimeError(
                f"strict_local violation: endpoint host {host!r} is not loopback ({url!r})"
            )
