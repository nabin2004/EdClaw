"""Docker-backed sandbox (hardened defaults; requires Docker daemon)."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import docker
from docker.errors import DockerException

from .contract import ExecResult


class DockerSandbox:
    def __init__(
        self,
        image: str = "educlaw/runner:latest",
        cpu_quota: int = 50_000,
        mem_limit: str = "512m",
        network: str = "none",
    ) -> None:
        self._image = image
        self._cpu_quota = cpu_quota
        self._mem_limit = mem_limit
        self._network = network
        self._client: docker.DockerClient | None = None
        self._container: Any = None

    async def start(self) -> None:
        loop = asyncio.get_running_loop()

        def _run() -> None:
            self._client = docker.from_env()
            self._container = self._client.containers.run(
                image=self._image,
                command="sleep infinity",
                detach=True,
                tty=False,
                network_mode=self._network,
                mem_limit=self._mem_limit,
                cpu_quota=self._cpu_quota,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/work": "rw,size=128m,exec"},
                user="65534:65534",
            )

        await loop.run_in_executor(None, _run)

    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str = "/work",
        timeout: timedelta = timedelta(seconds=30),
        stdin: bytes | None = None,
    ) -> ExecResult:
        if not self._container:
            raise RuntimeError("DockerSandbox not started")

        loop = asyncio.get_running_loop()

        def _run() -> ExecResult:
            res = self._container.exec_run(  # type: ignore[union-attr]
                cmd=argv,
                workdir=cwd,
                demux=True,
                stdin=bool(stdin),
            )
            out, err = res.output if isinstance(res.output, tuple) else (res.output, b"")
            return ExecResult(
                exit_code=res.exit_code or 0,
                stdout=(out or b"").decode("utf-8", "replace")[:200_000],
                stderr=(err or b"").decode("utf-8", "replace")[:50_000],
                truncated=False,
            )

        return await asyncio.wait_for(
            loop.run_in_executor(None, _run),
            timeout=timeout.total_seconds(),
        )

    async def write_file(self, path: str, data: bytes) -> None:
        raise NotImplementedError("Use exec with heredoc or docker cp in a follow-up")

    async def read_file(self, path: str, max_bytes: int = 1_000_000) -> bytes:
        raise NotImplementedError("Use exec cat in a follow-up")

    async def close(self) -> None:
        if self._container:
            loop = asyncio.get_running_loop()

            def _rm() -> None:
                try:
                    self._container.remove(force=True)  # type: ignore[union-attr]
                except DockerException:
                    pass

            await loop.run_in_executor(None, _rm)
        self._container = None
        self._client = None
