"""Pi-agent-core StreamFn backed by Ollama ``/api/chat`` streaming."""

from __future__ import annotations

import asyncio
import contextlib
import json
import uuid
from typing import Any, cast

from ollama import AsyncClient, Tool
from pi_agent_core.types import (
    AgentContext,
    AgentTool,
    AssistantMessage,
    Message,
    Model,
    SimpleStreamOptions,
    StopReason,
    StreamDoneEvent,
    StreamErrorEvent,
    StreamResult,
    StreamStartEvent,
    StreamTextDeltaEvent,
    StreamTextEndEvent,
    StreamTextStartEvent,
    StreamToolCallEndEvent,
    StreamToolCallStartEvent,
    TextContent,
    ToolCall,
    ToolResultMessage,
    UserMessage,
)


def _pi_messages_to_ollama(messages: list[Message]) -> list[dict[str, Any]]:
    """Map pi-agent-core messages to Ollama chat API shape."""
    out: list[dict[str, Any]] = []
    for msg in messages:
        if isinstance(msg, UserMessage):
            parts: list[str] = []
            for c in msg.content:
                if isinstance(c, TextContent):
                    parts.append(c.text)
            out.append({"role": "user", "content": "".join(parts)})
        elif isinstance(msg, AssistantMessage):
            text_chunks: list[str] = []
            tool_calls_out: list[dict[str, Any]] = []
            for block in msg.content:
                if isinstance(block, TextContent) and block.text:
                    text_chunks.append(block.text)
                elif isinstance(block, ToolCall):
                    tool_calls_out.append(
                        {
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": json.dumps(block.arguments),
                            },
                        },
                    )
            entry: dict[str, Any] = {
                "role": "assistant",
                "content": "".join(text_chunks) if text_chunks else "",
            }
            if tool_calls_out:
                entry["tool_calls"] = tool_calls_out
            out.append(entry)
        elif isinstance(msg, ToolResultMessage):
            text = "".join(c.text for c in msg.content if isinstance(c, TextContent))
            out.append({"role": "tool", "content": text, "name": msg.tool_name})
    return out


def _pi_tools_to_ollama(tools: list[AgentTool]) -> list[Tool]:
    result: list[Tool] = []
    for t in tools:
        result.append(
            Tool(
                type="function",
                function=Tool.Function(
                    name=t.name,
                    description=t.description or "",
                    parameters=Tool.Function.Parameters(  # type: ignore[call-arg]
                        type="object",
                        properties=cast(Any, dict(t.parameters.properties)),
                        required=list(t.parameters.required),
                    ),
                ),
            ),
        )
    return result


async def stream_ollama(
    model: Model,
    context: AgentContext,
    options: SimpleStreamOptions,
    *,
    ollama_host: str,
) -> StreamResult:
    """StreamFn implementation for Pi agent loop using local Ollama."""
    client = AsyncClient(host=ollama_host.rstrip("/"))
    ollama_messages = _pi_messages_to_ollama(list(context.messages))
    ollama_tools = _pi_tools_to_ollama(list(context.tools)) if context.tools else []

    queue: asyncio.Queue[Any | None] = asyncio.Queue()
    done = asyncio.Event()
    state: dict[str, Any] = {"final": None}

    partial = AssistantMessage(api=model.api, provider=model.provider, model=model.id)

    async def events_iter():
        while True:
            item = await queue.get()
            if item is None:
                return
            yield item

    async def result() -> AssistantMessage:
        await done.wait()
        final = state["final"]
        if final is None:
            raise RuntimeError("No result available")
        return final

    async def _pump() -> None:
        nonlocal partial
        text_started = False
        accumulated = ""
        content_idx = 0
        try:
            kwargs: dict[str, Any] = {
                "model": model.id,
                "messages": ollama_messages,
                "stream": True,
            }
            if ollama_tools:
                kwargs["tools"] = ollama_tools
            if options.temperature is not None:
                kwargs["options"] = {"temperature": options.temperature}

            raw_stream = await client.chat(**kwargs)

            queue.put_nowait(StreamStartEvent(partial=partial))

            last_chunk: Any = None
            async for chunk in raw_stream:
                if options.cancel_event and options.cancel_event.is_set():
                    raise RuntimeError("Request aborted by user")
                last_chunk = chunk
                msg = chunk.message
                frag = msg.content or ""
                if frag:
                    if not text_started:
                        partial.content.append(TextContent(text=""))
                        queue.put_nowait(
                            StreamTextStartEvent(content_index=content_idx, partial=partial),
                        )
                        text_started = True
                    accumulated += frag
                    tc = partial.content[content_idx]
                    if isinstance(tc, TextContent):
                        tc.text = accumulated
                    queue.put_nowait(
                        StreamTextDeltaEvent(
                            content_index=content_idx,
                            delta=frag,
                            partial=partial,
                        ),
                    )

            if options.cancel_event and options.cancel_event.is_set():
                raise RuntimeError("Request aborted by user")

            if text_started:
                tc_end = partial.content[content_idx]
                text_val = tc_end.text if isinstance(tc_end, TextContent) else accumulated
                queue.put_nowait(
                    StreamTextEndEvent(
                        content_index=content_idx,
                        content=text_val,
                        partial=partial,
                    ),
                )

            stop_reason: StopReason = "stop"
            if last_chunk is not None and getattr(last_chunk.message, "tool_calls", None):
                tcalls = last_chunk.message.tool_calls or []
                for oc in tcalls:
                    fn = oc.function
                    raw_args = fn.arguments
                    if isinstance(raw_args, dict):
                        args_dict = dict(raw_args)
                    elif isinstance(raw_args, str):
                        args_dict = {}
                        with contextlib.suppress(json.JSONDecodeError):
                            parsed = json.loads(raw_args)
                            if isinstance(parsed, dict):
                                args_dict = parsed
                    else:
                        args_dict = {}
                    call_id = getattr(oc, "id", None) or f"call_{uuid.uuid4().hex[:12]}"
                    idx = len(partial.content)
                    partial.content.append(ToolCall(id=call_id, name=fn.name, arguments=args_dict))
                    queue.put_nowait(StreamToolCallStartEvent(content_index=idx, partial=partial))
                    tc_block = partial.content[idx]
                    if isinstance(tc_block, ToolCall):
                        queue.put_nowait(
                            StreamToolCallEndEvent(
                                content_index=idx,
                                tool_call=tc_block,
                                partial=partial,
                            ),
                        )
                stop_reason = "toolUse"

            partial.stop_reason = stop_reason
            queue.put_nowait(StreamDoneEvent(reason=stop_reason, message=partial))
            state["final"] = partial

        except Exception as error:
            cancelled = options.cancel_event and options.cancel_event.is_set()
            reason: StopReason = "aborted" if cancelled else "error"
            partial.stop_reason = reason
            partial.error_message = str(error)
            queue.put_nowait(StreamErrorEvent(reason=reason, error=partial))
            state["final"] = partial

        finally:
            done.set()
            queue.put_nowait(None)

    asyncio.create_task(_pump())

    return {"events": events_iter(), "result": result}
