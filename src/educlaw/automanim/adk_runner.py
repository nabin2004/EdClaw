"""Run a single-turn ADK ``LlmAgent`` and return the final text response."""

from __future__ import annotations

import logging
import time
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

LOG = logging.getLogger(__name__)


async def run_llm_agent_once(agent: LlmAgent, *, user_text: str, user_id: str = "automanim") -> str:
    """Execute *agent* with one user message; return the last final text from the model."""
    agent_name = getattr(agent, "name", None) or type(agent).__name__
    t0 = time.monotonic()
    LOG.info("automanim_llm_start agent=%s user_id=%s", agent_name, user_id)

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
    try:
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
    except Exception:
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        LOG.exception(
            "automanim_llm_fail agent=%s elapsed_ms=%.0f",
            agent_name,
            elapsed_ms,
        )
        raise

    elapsed_ms = (time.monotonic() - t0) * 1000.0
    LOG.info(
        "automanim_llm_done agent=%s elapsed_ms=%.0f chars=%d",
        agent_name,
        elapsed_ms,
        len(last_text),
    )
    return last_text.strip()
