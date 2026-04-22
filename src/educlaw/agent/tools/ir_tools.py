from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool

from educlaw.agent.deps import AgentDeps


def build(deps: AgentDeps) -> list[Any]:
    async def ir_find_node(node_id: str) -> dict[str, Any]:
        """Look up a single IR node by id."""
        node = await deps.ir.get(node_id)
        if not node:
            return {"found": False, "node_id": node_id}
        return {
            "found": True,
            "id": node.id,
            "title": node.title,
            "objective": node.objective,
        }

    return [FunctionTool(ir_find_node)]
