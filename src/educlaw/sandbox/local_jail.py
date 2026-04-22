"""Local nsjail/bubblewrap sandbox (invoke subprocess; never os.system)."""

from __future__ import annotations

from datetime import timedelta

from .contract import ExecResult


class LocalJailSandbox:
    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str = "/work",
        timeout: timedelta = timedelta(seconds=30),
        stdin: bytes | None = None,
    ) -> ExecResult:
        raise NotImplementedError("Wrap nsjail/bwrap around argv")

    async def write_file(self, path: str, data: bytes) -> None:
        raise NotImplementedError

    async def read_file(self, path: str, max_bytes: int = 1_000_000) -> bytes:
        raise NotImplementedError

    async def close(self) -> None:
        return None
