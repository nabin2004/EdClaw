"""Structured learner outcome (FunctionGemma-style JSON over tools)."""

from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool
from pydantic import BaseModel, Field


class RecordAnswer(BaseModel):
    learner_id: str
    ir_node_id: str
    correct: bool
    confidence: float = Field(ge=0, le=1, default=0.8)


def build() -> Any:
    async def record_answer(payload: RecordAnswer) -> dict[str, Any]:
        """Record a structured assessment outcome."""
        return {
            "ok": True,
            "learner_id": payload.learner_id,
            "ir_node_id": payload.ir_node_id,
            "correct": payload.correct,
            "confidence": payload.confidence,
        }

    return FunctionTool(record_answer)
