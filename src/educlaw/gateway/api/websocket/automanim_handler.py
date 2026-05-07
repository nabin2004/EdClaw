"""WebSocket AutoManim: one-shot lecture Markdown to streamed pipeline events."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from ollama import AsyncClient

from educlaw.automanim.orchestrator import run_automanim
from educlaw.config.settings import Settings
from educlaw.gateway.agents.session import AgentSession
from educlaw.gateway.agents.streaming import Streamer
from educlaw.safety.shield import NoopShield, Shield

LOG = logging.getLogger("educlaw.automanim")


async def _maybe_close_ollama(client: AsyncClient) -> None:
    aclose = getattr(client, "aclose", None)
    if callable(aclose):
        await aclose()  # type: ignore[misc]
        return
    close = getattr(client, "close", None)
    if callable(close):
        out = close()
        if asyncio.iscoroutine(out):
            await out  # type: ignore[misc]


def _default_title(markdown: str) -> str:
    for line in markdown.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip() or "AutoManim"
    return "AutoManim"


def _artifact_url_for_path(artifact_abs: str, base: Path) -> str | None:
    try:
        p = Path(artifact_abs).resolve()
        rel = p.relative_to(base.resolve())
    except ValueError:
        return None
    return "/artifacts/manim/" + rel.as_posix()


async def handle_automanim_ws(
    session: AgentSession,
    stream: Streamer,
    settings: Settings,
    payload: dict[str, Any],
) -> None:
    """Run ``run_automanim`` for one lecture; stream ``automanim.progress`` + ``automanim.done``."""
    raw_md = payload.get("markdown")
    markdown = raw_md if isinstance(raw_md, str) else ""
    meta_in = payload.get("metadata")
    ir_suggestion: dict[str, Any] = dict(meta_in) if isinstance(meta_in, dict) else {}

    if not markdown.strip():
        await stream.event("assistant.status", {"phase": "start"})
        await stream.event(
            "automanim.progress",
            {
                "kind": "error",
                "message": "Missing or empty markdown field.",
                "lecture_id": None,
            },
        )
        await stream.event(
            "automanim.done",
            {
                "success": False,
                "artifact_paths": [],
                "artifact_urls": [],
                "output_dir": "",
                "error": "Missing or empty markdown field.",
            },
        )
        await stream.token("Missing or empty markdown field.\n")
        await stream.event("assistant.status", {"phase": "error", "message": "Missing markdown."})
        await stream.event("assistant.status", {"phase": "end"})
        return

    if not ir_suggestion.get("id"):
        ir_suggestion["id"] = "ws-lecture"
    if "title" not in ir_suggestion:
        ir_suggestion["title"] = _default_title(markdown)

    base_out = Path(settings.automanim_output_dir).expanduser().resolve()
    output_root = base_out / f"ws-{session.session_id}"
    output_root.mkdir(parents=True, exist_ok=True)

    LOG.info(
        "automanim_ws start session=%s lecture_id=%s title=%s output_root=%s shield_enabled=%s",
        session.session_id,
        ir_suggestion.get("id"),
        ir_suggestion.get("title"),
        output_root,
        settings.shield_enabled,
    )

    host = settings.ollama_url.rstrip("/")
    client = AsyncClient(host=host)
    shield: Shield | NoopShield = (
        Shield(client, model=settings.shield_model)
        if settings.shield_enabled
        else NoopShield()
    )

    await stream.event("assistant.status", {"phase": "start"})
    artifact_paths: list[str] = []
    artifact_urls: list[str] = []
    had_error = False
    last_error: str | None = None
    summary_lines: list[str] = []

    try:
        try:
            async for ev in run_automanim(
                markdown,
                ir_suggestion,
                settings,
                shield,
                ollama=client,
                output_root=output_root,
            ):
                payload_ev = ev.model_dump(mode="json", exclude_none=True)
                if payload_ev.get("kind") == "scene_done":
                    art = payload_ev.get("artifact")
                    if isinstance(art, dict) and art.get("artifact_path"):
                        art_url = _artifact_url_for_path(str(art["artifact_path"]), base_out)
                        if art_url:
                            payload_ev["artifact_url"] = art_url
                await stream.event("automanim.progress", payload_ev)
                msg_snip = (ev.message or "")[:160].replace("\n", " ")
                LOG.info(
                    "automanim_ws progress session=%s kind=%s scene_index=%s message=%s",
                    session.session_id,
                    ev.kind,
                    ev.scene_index,
                    msg_snip or "-",
                )
                if ev.kind == "error":
                    had_error = True
                    last_error = ev.message or "error"
                if ev.kind == "scene_done" and ev.artifact and ev.artifact.artifact_path:
                    ap = ev.artifact.artifact_path
                    artifact_paths.append(ap)
                    url = _artifact_url_for_path(ap, base_out)
                    if url:
                        artifact_urls.append(url)
        except Exception as e:  # noqa: BLE001
            had_error = True
            last_error = str(e)
            LOG.exception("automanim_ws session=%s pipeline_exception err=%s", session.session_id, e)
            await stream.event(
                "automanim.progress",
                {"kind": "error", "message": str(e), "lecture_id": ir_suggestion.get("id")},
            )
    finally:
        await _maybe_close_ollama(client)

    LOG.info(
        "automanim_ws done session=%s success=%s artifacts=%d error=%s",
        session.session_id,
        not had_error,
        len(artifact_paths),
        last_error or "-",
    )

    await stream.event(
        "automanim.done",
        {
            "success": not had_error,
            "output_dir": str(output_root),
            "artifact_paths": artifact_paths,
            "artifact_urls": artifact_urls,
            "error": last_error,
        },
    )

    if had_error:
        err_line = last_error or "AutoManim failed."
        summary_lines.append(err_line)
        await stream.event("assistant.status", {"phase": "error", "message": err_line})
    else:
        summary_lines.append("AutoManim finished.")
        if artifact_paths:
            summary_lines.append("Videos:")
            summary_lines.extend(f"  • {p}" for p in artifact_paths)
        if artifact_urls:
            summary_lines.append("Play in browser:")
            summary_lines.extend(f"  • {u}" for u in artifact_urls)
        summary_lines.append(f"Output directory: {output_root}")

    summary = "\n".join(summary_lines) + "\n"
    session.add_user_message(f"[automanim] {ir_suggestion.get('title', 'lecture')}")
    session.add_assistant_message(summary.strip())
    await stream.token(summary)

    await stream.event("assistant.status", {"phase": "end"})
