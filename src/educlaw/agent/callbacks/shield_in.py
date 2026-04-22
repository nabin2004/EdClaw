from __future__ import annotations

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from educlaw.agent.deps import AgentDeps
from educlaw.safety.audit import append_audit
from educlaw.safety.shield import Verdict


def _last_user_text(llm_request: LlmRequest) -> str:
    for c in reversed(llm_request.contents or []):
        if c.role == "user" and c.parts:
            for p in c.parts:
                if p.text:
                    return p.text
    return ""


def make(deps: AgentDeps):
    async def shield_before_model(
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        text = _last_user_text(llm_request)
        if not text.strip():
            return None
        verdict = await deps.shield.classify(text)
        audit_path = deps.settings.data_dir / "audit" / "shield.jsonl"
        if verdict in (Verdict.BLOCK, Verdict.REVIEW):
            append_audit(audit_path, verdict=verdict, phase="input", text=text)
        if verdict is Verdict.BLOCK:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="Blocked by EduClaw safety layer (input).")],
                )
            )
        return None

    return shield_before_model
