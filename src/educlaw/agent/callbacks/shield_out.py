from __future__ import annotations

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from educlaw.agent.deps import AgentDeps
from educlaw.safety.audit import append_audit
from educlaw.safety.shield import Verdict


def _response_text(resp: LlmResponse) -> str:
    if not resp.content or not resp.content.parts:
        return ""
    return " ".join(p.text or "" for p in resp.content.parts)


def make(deps: AgentDeps):
    async def shield_after_model(
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> LlmResponse | None:
        text = _response_text(llm_response)
        if not text.strip():
            return None
        verdict = await deps.shield.classify(text)
        audit_path = deps.settings.data_dir / "audit" / "shield.jsonl"
        if verdict in (Verdict.BLOCK, Verdict.REVIEW):
            append_audit(audit_path, verdict=verdict, phase="output", text=text)
        if verdict is Verdict.BLOCK:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="Reply blocked by EduClaw safety layer.")],
                )
            )
        return None

    return shield_after_model
