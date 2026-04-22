from __future__ import annotations

from datetime import timedelta
from typing import Protocol

from pydantic import BaseModel


class ExecResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    truncated: bool = False


class Sandbox(Protocol):
    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str = "/work",
        timeout: timedelta = timedelta(seconds=30),
        stdin: bytes | None = None,
    ) -> ExecResult: ...

    async def write_file(self, path: str, data: bytes) -> None: ...

    async def read_file(self, path: str, max_bytes: int = 1_000_000) -> bytes: ...

    async def close(self) -> None: ...
