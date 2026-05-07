"""Pluggable agent execution backends for the WebSocket gateway."""

from __future__ import annotations

from educlaw.gateway.agents.execution.base import ExecutionEngine, StubExecutionEngine
from educlaw.gateway.agents.execution.factory import build_execution_engine

__all__ = ["ExecutionEngine", "StubExecutionEngine", "build_execution_engine"]
