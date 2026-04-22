"""Runtime dependencies wired into tools and callbacks."""

from __future__ import annotations

from dataclasses import dataclass

from educlaw.config.settings import Settings
from educlaw.ir.store import IrStore
from educlaw.memory.dagestan import Dagestan
from educlaw.safety.shield import Shield
from educlaw.sandbox.contract import Sandbox


@dataclass
class AgentDeps:
    settings: Settings
    ir: IrStore
    dagestan: Dagestan
    shield: Shield
    sandbox: Sandbox
