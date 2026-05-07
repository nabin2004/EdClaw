"""Construct the gateway execution engine from settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from educlaw.gateway.agents.execution.base import ExecutionEngine, StubExecutionEngine

if TYPE_CHECKING:
    from educlaw.config.settings import Settings


def build_execution_engine(settings: Settings) -> ExecutionEngine:
    if settings.gateway_execution_engine == "pi":
        from educlaw.gateway.agents.execution.pi_engine import PiExecutionEngine

        return PiExecutionEngine(settings)
    return StubExecutionEngine()
