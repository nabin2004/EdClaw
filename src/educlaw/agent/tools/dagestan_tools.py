from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool

from educlaw.agent.deps import AgentDeps


def build(deps: AgentDeps) -> list[Any]:
    async def record_mastery(
        learner_id: str,
        ir_node_id: str,
        correct: bool,
        confidence: float = 0.9,
    ) -> dict[str, Any]:
        """Record a mastery-related fact for the learner."""
        pred = "knows" if correct else "struggled_with"
        f = await deps.dagestan.assert_fact(
            learner_id,
            pred,
            ir_node_id,
            confidence=confidence,
        )
        return {"id": f.id, "predicate": pred, "object": ir_node_id}

    async def snapshot_beliefs(learner_id: str) -> dict[str, Any]:
        facts = await deps.dagestan.snapshot(learner_id)
        return {
            "facts": [
                {
                    "predicate": x.predicate,
                    "object": x.object,
                    "confidence": x.confidence,
                }
                for x in facts[:50]
            ]
        }

    return [FunctionTool(record_mastery), FunctionTool(snapshot_beliefs)]
