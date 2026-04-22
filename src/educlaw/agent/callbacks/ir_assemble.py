"""Inject IR slice + belief snapshot into the system instruction."""

from __future__ import annotations

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from educlaw.agent.deps import AgentDeps


def _last_user_text(llm_request: LlmRequest) -> str:
    for c in reversed(llm_request.contents or []):
        if c.role == "user" and c.parts:
            for p in c.parts:
                if p.text:
                    return p.text
    return ""


def make(deps: AgentDeps):
    async def ir_before_model(
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        last = _last_user_text(llm_request)
        learner_id = callback_context.user_id
        ir_frag = await deps.ir.slice_for_learner(learner_id, last or None)
        beliefs = await deps.dagestan.snapshot(learner_id)
        btxt = "\n".join(
            f"- {f.predicate}({f.object}) conf={f.confidence:.2f}" for f in beliefs[:24]
        )
        llm_request.append_instructions(
            [
                ir_frag,
                "Current belief snapshot:\n" + (btxt or "(none)"),
            ]
        )
        return None

    return ir_before_model
