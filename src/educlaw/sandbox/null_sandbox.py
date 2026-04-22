"""Passthrough sandbox for development when Docker is unavailable."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from .contract import ExecResult


class NullSandbox:
    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str = "/work",
        timeout: timedelta = timedelta(seconds=30),
        stdin: bytes | None = None,
    ) -> ExecResult:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            stdin=asyncio.subprocess.PIPE if stdin else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await asyncio.wait_for(proc.communicate(stdin), timeout=timeout.total_seconds())
        return ExecResult(
            exit_code=proc.returncode or 0,
            stdout=(out or b"").decode("utf-8", "replace")[:200_000],
            stderr=(err or b"").decode("utf-8", "replace")[:50_000],
        )

    async def write_file(self, path: str, data: bytes) -> None:
        raise NotImplementedError

    async def read_file(self, path: str, max_bytes: int = 1_000_000) -> bytes:
        raise NotImplementedError

    async def close(self) -> None:
        return None
