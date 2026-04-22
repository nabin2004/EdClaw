from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool

from educlaw.agent.deps import AgentDeps


def build(deps: AgentDeps) -> Any:
    async def queue_manim_render(scene_hint: str, ir_node_id: str) -> dict[str, str]:
        """Queue a Manim render in the sandbox (stub — wire Docker manim image)."""
        return {
            "status": "queued",
            "scene_hint": scene_hint,
            "ir_node_id": ir_node_id,
            "note": "Implement Docker educlaw/manim:latest worker",
        }

    return FunctionTool(queue_manim_render)
