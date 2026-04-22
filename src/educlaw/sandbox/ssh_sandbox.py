"""Remote execution via AsyncSSH (stub — implement host keys + jailed user)."""

from __future__ import annotations

from datetime import timedelta

from .contract import ExecResult


class SshSandbox:
    def __init__(self, host: str, username: str) -> None:
        self.host = host
        self.username = username

    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str = "/work",
        timeout: timedelta = timedelta(seconds=30),
        stdin: bytes | None = None,
    ) -> ExecResult:
        raise NotImplementedError("SshSandbox: connect with asyncssh and run command")

    async def write_file(self, path: str, data: bytes) -> None:
        raise NotImplementedError

    async def read_file(self, path: str, max_bytes: int = 1_000_000) -> bytes:
        raise NotImplementedError

    async def close(self) -> None:
        return None
