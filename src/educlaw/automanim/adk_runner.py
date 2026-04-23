"""Run a single-turn ADK ``LlmAgent`` and return the final text response."""

from __future__ import annotations

import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def run_llm_agent_once(agent: LlmAgent, *, user_text: str, user_id: str = "automanim") -> str:
    """Execute *agent* with one user message; return the last final text from the model."""
    session_id = str(uuid.uuid4())
    runner = Runner(
        app_name="educlaw_automanim",
        agent=agent,
        session_service=InMemorySessionService(),
        memory_service=None,
        auto_create_session=True,
    )
    new_message = types.Content(role="user", parts=[types.Part(text=user_text)])
    last_text = ""
    async for ev in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        if getattr(ev, "error_message", None):
            raise RuntimeError(str(ev.error_message))
        if ev.is_final_response() and ev.author != "user" and ev.content and ev.content.parts:
            for part in ev.content.parts:
                if part.text:
                    last_text = part.text
    return last_text.strip()
