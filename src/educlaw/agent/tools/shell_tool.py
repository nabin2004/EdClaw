from __future__ import annotations

import shlex
from datetime import timedelta
from typing import Any

from google.adk.tools.function_tool import FunctionTool

from educlaw.agent.deps import AgentDeps
from educlaw.sandbox.policy import ToolPolicy


def build(deps: AgentDeps) -> Any:
    policy = ToolPolicy()

    async def sandbox_shell(command: str) -> dict[str, Any]:
        """Run a shell command inside the configured sandbox (policy-checked)."""
        if "exec" not in policy.allow:
            return {"error": "exec tool not allowed by policy"}
        argv = shlex.split(command)
        if not argv:
            return {"error": "empty command"}
        result = await deps.sandbox.exec(argv, timeout=timedelta(seconds=30))
        return result.model_dump()

    return FunctionTool(sandbox_shell)
