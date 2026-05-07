"""Pi-agent-core as a replaceable execution backend (EduClaw owns gateway + sessions)."""

from __future__ import annotations

import asyncio
from typing import Any

from educlaw.config.settings import Settings
from educlaw.gateway.agents.execution.ollama_stream import stream_ollama
from educlaw.gateway.agents.session import AgentSession
from educlaw.gateway.agents.streaming import Streamer
from educlaw.gateway.agents.tools.tools import ToolRegistry


def _registry_to_pi_tools(registry: ToolRegistry) -> list[Any]:
    from pi_agent_core.types import AgentTool, AgentToolResult, AgentToolSchema, TextContent

    tools: list[AgentTool] = []

    for name in registry.tools:

        def _make_execute(tool_name: str):
            async def execute(
                tool_call_id: str,
                params: dict[str, Any],
                cancel_event: asyncio.Event | None = None,
                on_update: Any = None,
            ) -> AgentToolResult:
                del tool_call_id, cancel_event, on_update
                out = await registry.execute(tool_name, params)
                return AgentToolResult(content=[TextContent(text=str(out))])

            return execute

        tools.append(
            AgentTool(
                name=name,
                description=f"EduClaw tool `{name}`",
                parameters=AgentToolSchema(type="object", properties={}, required=[]),
                execute=_make_execute(name),
            ),
        )
    return tools


def _assistant_plain_text(agent: Any) -> str:
    from pi_agent_core.types import AssistantMessage, TextContent

    for msg in reversed(agent.state.messages):
        if isinstance(msg, AssistantMessage):
            parts: list[str] = []
            for c in msg.content:
                if isinstance(c, TextContent) and c.text:
                    parts.append(c.text)
            return "".join(parts).strip()
    return ""


class PiExecutionEngine:
    """Delegates turn execution to pi-agent-core + Ollama StreamFn."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _get_or_create_agent(self, session: AgentSession) -> Any:
        from pi_agent_core import Agent, AgentOptions
        from pi_agent_core.types import Model

        raw = session.backing
        agent = getattr(raw, "pi_agent", None)
        if agent is not None:
            return agent

        host = self._settings.ollama_url

        async def _stream_fn(model: Any, context: Any, options: Any):
            return await stream_ollama(model, context, options, ollama_host=host)

        opts = AgentOptions(stream_fn=_stream_fn, session_id=session.session_id)
        agent = Agent(opts)
        agent.set_system_prompt("You are an AI agent inside EduClaw.")
        agent.set_model(Model(api="ollama", provider="ollama", id=self._settings.model_id))
        raw.pi_agent = agent
        return agent

    async def run(
        self,
        session: AgentSession,
        input_text: str,
        tools: ToolRegistry,
        stream: Streamer,
    ) -> str:
        from pi_agent_core.types import Model

        agent = self._get_or_create_agent(session)
        agent.set_tools(_registry_to_pi_tools(tools))
        agent.set_model(Model(api="ollama", provider="ollama", id=self._settings.model_id))

        loop = asyncio.get_running_loop()
        unsubscribers: list[Any] = []

        def _on_event(ev: Any) -> None:
            if getattr(ev, "type", None) != "message_update":
                return
            inner = getattr(ev, "assistant_message_event", None)
            if inner is None:
                return
            if getattr(inner, "type", None) == "text_delta":
                delta = getattr(inner, "delta", "") or ""
                if delta:
                    loop.create_task(stream.token(delta))

        unsubscribers.append(agent.subscribe(_on_event))

        try:
            await agent.prompt(input_text)
            await agent.wait_for_idle()
        finally:
            for u in unsubscribers:
                u()

        text = _assistant_plain_text(agent)
        if agent.state.error and not text:
            raise RuntimeError(agent.state.error)
        return text if text else "(no text)"
