"""Typer CLI: ``educlaw`` entry point."""

from __future__ import annotations

import warnings

# Suppress experimental feature warnings from google-adk (e.g. PLUGGABLE_AUTH)
warnings.filterwarnings("ignore", category=UserWarning, message=".*EXPERIMENTAL.*feature.*")

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Any, cast

import httpx
import typer
import uvicorn

from educlaw.automanim.orchestrator import run_automanim
from educlaw.config.settings import load_settings
from educlaw.config.strict_local import assert_strict_local
from educlaw.ir.loader import lint, load_all
from educlaw.safety.shield import Shield
from educlaw.tts.contract import TTSRequest
from educlaw.tts.md_to_srt import estimate_timing, segment_markdown
from educlaw.tts.registry import build_backend, known_backends

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _intro_logo_path() -> Path:
    try:
        import importlib.resources
        ref = importlib.resources.files("educlaw.assets").joinpath("ascii-logo.txt")
        if isinstance(ref, Path):
            return ref
        with importlib.resources.as_file(ref) as p:
            return Path(p)
    except Exception:
        pass

    dev_path = Path(__file__).resolve().parent / "assets" / "ascii-logo.txt"
    if dev_path.exists():
        return dev_path
    return Path(__file__).resolve().parents[2] / "assets" / "ascii-logo.txt"


def _load_intro_logo() -> str:
    try:
        import importlib.resources
        return importlib.resources.files("educlaw.assets").joinpath("ascii-logo.txt").read_text(encoding="utf-8").rstrip()
    except Exception:
        try:
            return _intro_logo_path().read_text(encoding="utf-8").rstrip()
        except Exception:
            return ""


def _play_intro(stream: Any | None = None) -> bool:
    output = stream or sys.stdout
    if not hasattr(output, "isatty") or not output.isatty():
        return False

    logo = _load_intro_logo()
    if not logo.strip():
        return False

    try:
        from terminaltexteffects.effects.effect_print import Print
    except ImportError:
        typer.echo(logo)
        return True

    try:
        effect = Print(logo)
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
    except Exception:
        typer.echo(logo)

    return True


@app.command()
def serve(
    host: str | None = typer.Option(None, help="Bind host (default from profile)"),
    port: int | None = typer.Option(None, help="Bind port"),
) -> None:
    """Run the FastAPI gateway (HTTP + WebSocket)."""
    s = load_settings()
    uvicorn.run(
        "educlaw.gateway.app:app",
        host=host or s.gateway_host,
        port=port or s.gateway_port,
        workers=1,
        factory=False,
    )


@app.command("doctor")
def doctor_cmd(
    offline: bool = typer.Option(False, help="Skip Ollama HTTP checks (for CI)"),
) -> None:
    """Validate profile, strict-local policy, and optional Ollama models."""
    s = load_settings()
    typer.echo(f"Profile: {s.profile_path}")
    if s.strict_local:
        try:
            assert_strict_local(s.ollama_url)
            typer.secho("strict_local: OK", fg=typer.colors.GREEN)
        except RuntimeError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            raise typer.Exit(code=1) from e
    if s.automanim_enabled and s.automanim_backend == "local":
        from educlaw.viz import manim_available

        if not manim_available():
            typer.secho(
                "Warning: automanim uses local render but Manim CE is not installed "
                "(pip install 'educlaw[automanim]' or pip install manim; or set "
                'automanim_backend = "docker").',
                fg=typer.colors.YELLOW,
            )
    if offline:
        typer.echo("doctor: offline mode — skipping Ollama")
        return
    try:
        r = httpx.get(f"{s.ollama_url.rstrip('/')}/api/tags", timeout=5.0)
        r.raise_for_status()
        names = {m.get("name", "") for m in r.json().get("models", [])}
        typer.echo(f"Ollama: OK ({len(names)} models)")
        for want in sorted({s.model_id, s.shield_model}):
            if not any(n.startswith(want.split(":")[0]) for n in names):
                typer.secho(
                    f"Warning: model matching {want!r} not found in ollama list",
                    fg=typer.colors.YELLOW,
                )
    except Exception as e:
        typer.secho(f"Ollama check failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e


tts_typer = typer.Typer(help="Text-to-speech (offline backends; see docs/TTS.md).")
app.add_typer(tts_typer, name="tts")

autocourse_typer = typer.Typer(help="Autocourse specific commands.")
app.add_typer(autocourse_typer, name="autocourse")


@autocourse_typer.command("plan")
def autocourse_plan(
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Course topic to plan"),
    ] = None,
    lectures: Annotated[
        int,
        typer.Option("--lectures", "-n", min=2, max=8, help="Number of lectures (2–8)"),
    ] = 4,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Save plan as JSON"),
    ] = None,
) -> None:
    """Plan a course curriculum (shows outline without writing lectures)."""
    from educlaw.autocourse.orchestrator import CoursePlanningFailed, plan_course
    from ollama import AsyncClient

    if not prompt:
        prompt = typer.prompt(
            typer.style("Enter course topic", fg=typer.colors.CYAN, bold=True)
        )

    s = load_settings()
    n = max(2, min(8, lectures))
    user = (
        f"Plan a course with exactly {n} lectures (all {n}, not fewer). "
        f"Audience: general learners. Topic:\n{prompt.strip()}"
    )

    async def _run() -> None:
        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        try:
            plan = await plan_course(client, s, user)
        except CoursePlanningFailed as e:
            typer.secho(str(e), fg=typer.colors.RED)
            raise typer.Exit(code=1) from e
        finally:
            aclose = getattr(client, "aclose", None) or getattr(client, "close", None)
            if callable(aclose):
                r = aclose()
                if asyncio.iscoroutine(r):
                    await r

        lecs = plan.lectures[:n]
        typer.secho(f"\n{plan.title}", fg=typer.colors.CYAN, bold=True)
        typer.echo(f"Audience: {plan.audience}")
        typer.echo(f"Lectures: {len(lecs)}\n")
        for i, lec in enumerate(lecs, 1):
            typer.secho(f"  {i}. {lec.title}", fg=typer.colors.GREEN)
            for obj in (lec.objectives or [])[:2]:
                typer.echo(f"     • {obj}")

        if out:
            import json as _json

            out_path = out.expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                _json.dumps(
                    {
                        "title": plan.title,
                        "audience": plan.audience,
                        "lectures": [lec.model_dump() for lec in lecs],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            typer.secho(f"\nSaved plan to {out_path}", fg=typer.colors.GREEN)

    asyncio.run(_run())


@autocourse_typer.command("generate")
def autocourse_generate(
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Course topic"),
    ] = None,
    lectures: Annotated[
        int,
        typer.Option("--lectures", "-n", min=2, max=8, help="Number of lectures (2–8)"),
    ] = 4,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Output directory"),
    ] = None,
    tts: Annotated[
        bool,
        typer.Option("--tts/--no-tts", help="TTS audio synthesis per lecture"),
    ] = True,
    automanim: Annotated[
        bool,
        typer.Option("--automanim/--no-automanim", help="AutoManim video generation"),
    ] = True,
    shield: Annotated[
        bool,
        typer.Option("--shield/--no-shield", help="Ollama safety shield"),
    ] = True,
    continue_on_error: Annotated[
        bool,
        typer.Option("--continue-on-error", help="Keep going after lecture failures"),
    ] = False,
    generate_site: Annotated[
        bool,
        typer.Option("--generate-site", help="Generate Jekyll site when done"),
    ] = False,
    automanim_backend: Annotated[
        str | None,
        typer.Option("--automanim-backend", help="'local' or 'docker'"),
    ] = None,
) -> None:
    """Generate a full course: plan → lectures → subtitle-chunked SRT/VTT+WAV → Manim animations.

    Delegates to the same pipeline as scripts/run_full_course_pipeline.py.
    """
    from educlaw.autocourse.pipeline import PipelineConfig, run_pipeline

    if not prompt:
        prompt = typer.prompt(
            typer.style("Enter course topic", fg=typer.colors.CYAN, bold=True)
        )

    cfg = PipelineConfig(
        topic=prompt,
        lectures=lectures,
        out=out,
        enable_tts=tts,
        enable_automanim=automanim,
        enable_shield=shield,
        automanim_backend=automanim_backend,
        continue_on_error=continue_on_error,
        generate_site=generate_site,
    )
    exit_code, _ = asyncio.run(run_pipeline(cfg))
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


autolecture_typer = typer.Typer(help="Autolecture specific commands.")
app.add_typer(autolecture_typer, name="autolecture")


@autolecture_typer.command("plan")
def autolecture_plan(
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Lecture topic"),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Save outline as JSON"),
    ] = None,
) -> None:
    """Plan a single lecture outline from a topic (no lecture generated)."""
    from ollama import AsyncClient

    if not prompt:
        prompt = typer.prompt(
            typer.style("Enter lecture topic", fg=typer.colors.CYAN, bold=True)
        )

    s = load_settings()

    async def _run() -> None:
        import json as _json

        from educlaw.autolecture.schema import LectureOutline

        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        _PLAN_SYS = (
            "You are a curriculum designer. Given a topic, design a single lecture outline. "
            'Respond with JSON only (no markdown fences): {"title": "...", '
            '"objectives": ["..."], "key_topics": ["..."], "estimated_minutes": 45}'
        )
        try:
            resp = await client.chat(
                model=s.model_id,
                messages=[
                    {"role": "system", "content": _PLAN_SYS},
                    {"role": "user", "content": f"Design a lecture on: {prompt.strip()}"},
                ],
                format="json",
                options={"temperature": 0.25, "num_predict": 1024},
            )
            msg = resp.get("message") or {}
            raw = (msg.get("content") or "").strip()
            data = _json.loads(raw)
            outline = LectureOutline(
                title=str(data.get("title") or prompt),
                objectives=data.get("objectives") or [],
                key_topics=data.get("key_topics") or [],
                estimated_minutes=data.get("estimated_minutes"),
            )
        except Exception as e:  # noqa: BLE001
            typer.secho(f"Planning failed: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1) from e
        finally:
            aclose = getattr(client, "aclose", None) or getattr(client, "close", None)
            if callable(aclose):
                r = aclose()
                if asyncio.iscoroutine(r):
                    await r

        typer.secho(f"\n{outline.title}", fg=typer.colors.CYAN, bold=True)
        if outline.estimated_minutes:
            typer.echo(f"Estimated: {outline.estimated_minutes} min")
        if outline.objectives:
            typer.echo("\nObjectives:")
            for obj in outline.objectives:
                typer.echo(f"  • {obj}")
        if outline.key_topics:
            typer.echo("\nKey topics:")
            for t in outline.key_topics:
                typer.echo(f"  - {t}")

        if out:
            out_path = out.expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(_json.dumps(outline.model_dump(), indent=2) + "\n", encoding="utf-8")
            typer.secho(f"\nSaved outline to {out_path}", fg=typer.colors.GREEN)

    asyncio.run(_run())


@autolecture_typer.command("generate")
def autolecture_generate(
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Lecture topic"),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Output .md path (default: lecture-01-<slug>.md)"),
    ] = None,
) -> None:
    """Generate a single lecture in Markdown from a topic."""
    import re as _re

    import frontmatter as _fm
    from ollama import AsyncClient

    from educlaw.autolecture.generator import generate_lecture
    from educlaw.autolecture.schema import LectureOutline

    if not prompt:
        prompt = typer.prompt(
            typer.style("Enter lecture topic", fg=typer.colors.CYAN, bold=True)
        )

    s = load_settings()
    outline = LectureOutline(title=prompt.strip())

    async def _run() -> None:
        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        try:
            typer.echo(f"Generating: {outline.title}")
            result = await generate_lecture(
                client,
                s.model_id,
                outline,
                course_title=outline.title,
                lecture_index=1,
                lecture_count=1,
                prior_lecture_titles=[],
            )
        except Exception as e:  # noqa: BLE001
            typer.secho(f"Generation failed: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1) from e
        finally:
            aclose = getattr(client, "aclose", None) or getattr(client, "close", None)
            if callable(aclose):
                r = aclose()
                if asyncio.iscoroutine(r):
                    await r

        meta = dict(result.ir_suggestion) if result.ir_suggestion else {}
        post = _fm.Post(result.markdown, **meta)
        sl = _re.sub(r"[^a-z0-9]+", "-", outline.title.lower()).strip("-")[:48] or "lecture"
        out_path = out.expanduser() if out else Path(f"lecture-01-{sl}.md")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_fm.dumps(post), encoding="utf-8")
        typer.secho(f"Wrote {out_path}", fg=typer.colors.GREEN)

    asyncio.run(_run())


automanim_typer = typer.Typer(help="AutoManim animation and rendering specific commands.")
app.add_typer(automanim_typer, name="automanim")


@automanim_typer.command("plan")
def automanim_plan(
    lecture_file: Annotated[
        Path | None,
        typer.Argument(help="Lecture .md file to plan scenes for"),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Inline lecture text (alternative to file)"),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Save scene plan as JSON"),
    ] = None,
) -> None:
    """Plan Manim animation scenes for a lecture (shows scenes without rendering)."""
    import json as _json

    import frontmatter as _fm
    from ollama import AsyncClient

    from educlaw.safety.shield import NoopShield, Shield

    s = load_settings()

    if lecture_file is not None:
        lf = lecture_file.expanduser().resolve()
        if not lf.exists():
            typer.secho(f"File not found: {lf}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        post = _fm.loads(lf.read_text(encoding="utf-8"))
        markdown = post.content
        meta: dict = dict(post.metadata) if isinstance(post.metadata, dict) else {}
    elif prompt:
        markdown = prompt
        meta = {}
    else:
        typer.secho(
            "Provide a lecture .md file argument or --prompt with lecture text.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    def _extract_title(md_text: str, fallback_meta: dict) -> str:
        if fallback_meta.get("title"):
            return str(fallback_meta["title"])
        for line in md_text.splitlines():
            s_line = line.strip()
            if s_line.startswith("#"):
                return s_line.lstrip("#").strip() or "Lecture"
        return "Lecture"

    async def _run() -> None:
        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        shield_impl: Shield | NoopShield = (
            Shield(client, model=s.shield_model) if s.shield_enabled else NoopShield()
        )
        scenes_data: list[dict] = []
        try:
            try:
                segs = await segment_markdown(client, s.model_id, markdown)
            except Exception:
                segs = []
            subtitle_blocks = estimate_timing(segs) if segs else estimate_timing([markdown[:500]])
            lecture_title = _extract_title(markdown, meta)
            async for ev in run_automanim(markdown, subtitle_blocks, lecture_title, s, shield_impl, ollama=client):
                if ev.kind == "plan":
                    scenes_data = (ev.extra or {}).get("scenes", [])
                    typer.secho(
                        f"\nPlanned {len(scenes_data)} scene(s):", fg=typer.colors.CYAN, bold=True
                    )
                    for i, sc in enumerate(scenes_data, 1):
                        typer.secho(f"  {i}. {sc.get('title', '?')}", fg=typer.colors.GREEN)
                        if sc.get("description"):
                            typer.echo(f"     {sc['description']}")
                    break  # stop before codegen/render
                elif ev.kind == "error":
                    typer.secho(f"Error: {ev.message}", fg=typer.colors.YELLOW)
                    break
        finally:
            aclose = getattr(client, "aclose", None) or getattr(client, "close", None)
            if callable(aclose):
                r = aclose()
                if asyncio.iscoroutine(r):
                    await r

        if out and scenes_data:
            out_path = out.expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                _json.dumps({"scenes": scenes_data}, indent=2) + "\n", encoding="utf-8"
            )
            typer.secho(f"Saved scene plan to {out_path}", fg=typer.colors.GREEN)

    asyncio.run(_run())


@automanim_typer.command("render")
def automanim_render(
    lecture_file: Annotated[
        Path | None,
        typer.Argument(help="Lecture .md file to render"),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Inline lecture text (alternative to file)"),
    ] = None,
    out_dir: Annotated[
        Path | None,
        typer.Option("--out-dir", "-o", help="Video output directory (default: videos/)"),
    ] = None,
    no_shield: Annotated[
        bool,
        typer.Option("--no-shield", help="Skip safety shield"),
    ] = False,
) -> None:
    """Render Manim animations for a single lecture markdown file."""
    import json as _json

    import frontmatter as _fm
    from ollama import AsyncClient

    from educlaw.safety.shield import NoopShield, Shield

    s = load_settings()

    if lecture_file is not None:
        lf = lecture_file.expanduser().resolve()
        if not lf.exists():
            typer.secho(f"File not found: {lf}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        post = _fm.loads(lf.read_text(encoding="utf-8"))
        markdown = post.content
        meta: dict = dict(post.metadata) if isinstance(post.metadata, dict) else {}
        lecture_id = str(meta.get("id") or lf.stem)
    elif prompt:
        markdown = prompt
        meta = {}
        lecture_id = "lecture"
    else:
        typer.secho(
            "Provide a lecture .md file argument or --prompt with lecture text.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    output_root = (out_dir or Path("videos")).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        shield_impl: Shield | NoopShield = (
            Shield(client, model=s.shield_model)
            if (s.shield_enabled and not no_shield)
            else NoopShield()
        )
        scenes: list[dict] = []
        try:
            try:
                segs = await segment_markdown(client, s.model_id, markdown)
            except Exception:
                segs = []
            sub_blocks = estimate_timing(segs) if segs else estimate_timing([markdown[:500]])
            lec_title = str(meta.get("title") or lecture_id)
            async for ev in run_automanim(
                markdown, sub_blocks, lec_title, s, shield_impl, ollama=client, output_root=output_root
            ):
                if ev.kind == "scene_done" and ev.artifact and ev.artifact.artifact_path:
                    scenes.append(
                        {
                            "scene_index": ev.scene_index,
                            "scene_title": ev.scene_title,
                            "artifact_path": ev.artifact.artifact_path,
                            "exit_code": ev.artifact.exit_code,
                        }
                    )
                    typer.echo(f"  Rendered: {ev.artifact.artifact_path}")
                elif ev.kind == "error" and ev.message:
                    typer.secho(f"  Error: {ev.message}", fg=typer.colors.YELLOW)
        finally:
            aclose = getattr(client, "aclose", None) or getattr(client, "close", None)
            if callable(aclose):
                r = aclose()
                if asyncio.iscoroutine(r):
                    await r

        if scenes:
            mp = output_root / f"{lecture_id}-manifest.json"
            mp.write_text(
                _json.dumps({"lecture_id": lecture_id, "scenes": scenes}, indent=2) + "\n",
                encoding="utf-8",
            )
            typer.secho(f"Wrote manifest to {mp}", fg=typer.colors.GREEN)

    asyncio.run(_run())



@tts_typer.command("list")
def tts_list() -> None:
    """List registered TTS backends and (best-effort) available voices."""
    s = load_settings()
    typer.echo("Registered backends:")
    for name in sorted(known_backends()):
        typer.echo(f"  - {name}")
    typer.echo("")
    if not s.tts_enabled:
        typer.secho(
            "tts_enabled is false — enable TTS in your profile to build kitten and list voices.",
            fg=typer.colors.YELLOW,
        )
        return
    try:
        backend = build_backend(s)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    if backend is None:
        typer.echo("No active backend (tts_enabled is false).")
        return
    typer.echo(f"Active backend for this profile: {backend.name}")
    typer.echo(f"  voices: {backend.available_voices}")

    async def _close() -> None:
        await backend.close()

    asyncio.run(_close())


@tts_typer.command("say")
def tts_say(
    text: Annotated[str, typer.Argument(help="Text to synthesize")],
    voice: Annotated[str | None, typer.Option(help="Voice name (backend-specific)")] = None,
    speed: Annotated[float, typer.Option(help="Speech speed multiplier")] = 1.0,
    out: Annotated[Path, typer.Option("--out", "-o", help="Output WAV path")] = Path("out.wav"),
) -> None:
    """Synthesize speech to a WAV file (requires tts_enabled and a valid backend)."""
    s = load_settings()
    if not s.tts_enabled:
        typer.secho("Set tts_enabled=true in your profile.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    try:
        backend = build_backend(s)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    if backend is None:
        typer.secho("TTS is disabled.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    async def _run() -> None:
        req = TTSRequest(
            text=text,
            voice=voice or s.tts_voice,
            speed=speed,
            sample_rate=s.tts_sample_rate,
        )
        audio = await backend.synthesize(req)
        out_p = out.expanduser()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(audio.audio_bytes)
        await backend.close()

    asyncio.run(_run())
    typer.secho(f"Wrote {out.expanduser()}", fg=typer.colors.GREEN)


@tts_typer.command("speak")
def tts_speak(
    text: Annotated[
        str | None, typer.Option("--text", "-t", help="Text to speak")
    ] = None,
    out: Annotated[
        Path, typer.Option("--out", "-o", help="Output WAV path")
    ] = Path("out.wav"),
) -> None:
    """Synthesize text to a WAV file (alias for ``tts say`` with interactive prompt)."""
    if not text:
        text = typer.prompt(
            typer.style("Enter text to speak", fg=typer.colors.CYAN, bold=True)
        )
    s = load_settings()
    if not s.tts_enabled:
        typer.secho("Set tts_enabled=true in your profile.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    try:
        backend = build_backend(s)
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    if backend is None:
        typer.secho("TTS is disabled.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    async def _run() -> None:
        from educlaw.tts.contract import TTSRequest

        req = TTSRequest(text=text, voice=s.tts_voice, speed=s.tts_speed, sample_rate=s.tts_sample_rate)
        audio = await backend.synthesize(req)
        out_p = out.expanduser()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(audio.audio_bytes)
        await backend.close()

    asyncio.run(_run())
    typer.secho(f"Wrote {out.expanduser()}", fg=typer.colors.GREEN)


@tts_typer.command("status")
def tts_status() -> None:
    """Show TTS backend status and active configuration."""
    s = load_settings()
    typer.echo(f"TTS enabled:  {s.tts_enabled}")
    typer.echo(f"Backend:      {s.tts_backend}")
    typer.echo(f"Voice:        {s.tts_voice}")
    typer.echo(f"Speed:        {s.tts_speed}")
    typer.echo(f"Sample rate:  {s.tts_sample_rate} Hz")
    if not s.tts_enabled:
        typer.secho("TTS is disabled in the active profile.", fg=typer.colors.YELLOW)
        return
    try:
        backend = build_backend(s)
        if backend is None:
            typer.secho("Backend built but returned None.", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Backend OK: {backend.name}", fg=typer.colors.GREEN)

            async def _close() -> None:
                await backend.close()

            asyncio.run(_close())
    except Exception as e:  # noqa: BLE001
        typer.secho(f"Backend error: {e}", fg=typer.colors.RED)


ir_typer = typer.Typer(help="IR maintenance commands.")
app.add_typer(ir_typer, name="ir")


@ir_typer.command("lint")
def ir_lint(
    root: Annotated[Path | None, typer.Option(help="IR root directory")] = None,
) -> None:
    """Lint IR graph (prereqs, cycles, orphans)."""
    s = load_settings()
    base = root if root is not None else (s.ir_root or Path("."))
    r = base.expanduser()
    problems = lint(load_all(r))
    for p in problems:
        typer.secho(p, fg=typer.colors.RED, err=True)
    if problems:
        raise typer.Exit(code=1)
    typer.secho("IR lint: OK", fg=typer.colors.GREEN)


@ir_typer.command("index")
def ir_index(
    out: Annotated[Path | None, typer.Option(help="Vector sqlite output")] = None,
    model: Annotated[str | None, typer.Option(help="Embedding model id")] = None,
) -> None:
    """Build IR vector index (requires running Ollama)."""
    s = load_settings()
    out_base = out if out is not None else (s.vec_sqlite_path or Path("vectors.sqlite"))
    out_p = out_base.expanduser()
    m = model or s.embedding_model
    ir_base = s.ir_root or Path(".")
    ir_root = ir_base.expanduser()
    from educlaw.ir.indexer import build_ir_vector_index
    from educlaw.memory.embeddings import EmbeddingClient

    async def _run() -> int:
        embed = EmbeddingClient(s.ollama_url)
        return await build_ir_vector_index(
            ir_root=ir_root,
            out_db=out_p,
            model=m,
            embed_client=embed,
        )

    n = asyncio.run(_run())
    typer.echo(f"Indexed {n} IR nodes into {out_p}")


@automanim_typer.command("run")
def automanim_cmd(
    series_dir: Annotated[
        Path,
        typer.Argument(help="Directory with lecture-*.md (YAML frontmatter)"),
    ],
) -> None:
    """Render Manim videos for each lecture in a series (writes videos/ + manifest)."""
    import json

    import frontmatter
    from ollama import AsyncClient

    s = load_settings()
    series_path = series_dir.expanduser().resolve()
    if not series_path.is_dir():
        typer.secho(f"Not a directory: {series_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    videos_root = series_path / "videos"
    videos_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, list[dict[str, object]]] = {}

    async def _run() -> None:
        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        shield = Shield(client, model=s.shield_model)
        try:
            for md_path in sorted(series_path.glob("lecture-*.md")):
                post = frontmatter.loads(md_path.read_text(encoding="utf-8"))
                meta = dict(post.metadata) if isinstance(post.metadata, dict) else {}
                lecture_id = str(meta.get("id") or md_path.stem)
                manifest.setdefault(lecture_id, [])
                md_content = str(post.content)
                try:
                    segs = await segment_markdown(client, s.model_id, md_content)
                except Exception:
                    segs = []
                sub_blocks = estimate_timing(segs) if segs else estimate_timing([md_content[:500]])
                lec_title = str(meta.get("title") or lecture_id)
                async for ev in run_automanim(
                    md_content,
                    sub_blocks,
                    lec_title,
                    s,
                    shield,
                    ollama=client,
                    output_root=videos_root,
                ):
                    if ev.kind == "scene_done" and ev.artifact and (
                        ev.artifact.artifact_path or ev.artifact.scene_dir
                    ):
                        row: dict[str, object] = {
                            "scene_index": ev.scene_index,
                            "scene_title": ev.scene_title,
                            "artifact_path": ev.artifact.artifact_path,
                            "exit_code": ev.artifact.exit_code,
                        }
                        if ev.artifact.scene_dir:
                            row["scene_dir"] = ev.artifact.scene_dir
                        if ev.artifact.source_path:
                            row["source_path"] = ev.artifact.source_path
                        if ev.artifact.log_path:
                            row["log_path"] = ev.artifact.log_path
                        manifest[lecture_id].append(row)
                    if ev.kind == "error":
                        typer.secho(f"{lecture_id}: {ev.message}", fg=typer.colors.YELLOW)
        finally:
            await cast(Any, client).close()

    asyncio.run(_run())
    manifest_path = videos_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    typer.secho(f"Wrote manifest to {videos_root / 'manifest.json'}", fg=typer.colors.GREEN)


# ---------------------------------------------------------------------------
# Site generation commands
# ---------------------------------------------------------------------------

site_typer = typer.Typer(help="Course site generation and catalog (see docs/SITE_GENERATION.md).")
app.add_typer(site_typer, name="site")

from educlaw.train.cli import train_typer  # noqa: E402

app.add_typer(train_typer, name="train")


@site_typer.command("generate")
def site_generate(
    series_dir: Annotated[
        Path,
        typer.Argument(help="Series directory with course-plan.json + lecture-*.md"),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Parent dir for generated sites (default: sites/)"),
    ] = None,
) -> None:
    """Generate a Jekyll course site from an autocourse series."""
    from educlaw.sitegen.generator import generate_site

    series_path = series_dir.expanduser().resolve()
    if not series_path.is_dir():
        typer.secho(f"Not a directory: {series_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not (series_path / "course-plan.json").exists():
        typer.secho(f"No course-plan.json in {series_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    dest = generate_site(series_path, output_dir=output_dir)
    typer.secho(f"Site generated at {dest}", fg=typer.colors.GREEN)


@site_typer.command("catalog")
def site_catalog(
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Directory for index.html (default: sites/)"),
    ] = None,
) -> None:
    """Re-render the course catalog landing page from the registry."""
    from educlaw.sitegen.catalog import render_catalog

    out = render_catalog(output_dir=output_dir)
    typer.secho(f"Catalog rendered at {out}", fg=typer.colors.GREEN)


@site_typer.command("list")
def site_list() -> None:
    """List all courses registered in the catalog."""
    from educlaw.sitegen.registry import list_courses

    courses = list_courses()
    if not courses:
        typer.echo("No courses registered yet.")
        return
    for c in courses:
        typer.echo(f"  {c.get('slug', '?'):30s}  {c.get('title', '')}")


@app.command("pull-models")
def pull_models() -> None:
    """Shell out to ``ollama pull`` for default Gemma stack."""
    s = load_settings()
    for m in sorted({s.model_id, s.embedding_model, s.shield_model}):
        typer.echo(f"ollama pull {m}")
        subprocess.run(["ollama", "pull", m], check=False)


# ---------------------------------------------------------------------------
# educlaw course — top-level shortcut (positional topic like the shell script)
# ---------------------------------------------------------------------------

course_typer = typer.Typer(
    help="Generate a complete course (plan → Markdown → SRT/WAV → Manim).",
    no_args_is_help=True,
)
app.add_typer(course_typer, name="course")


@course_typer.command("generate")
def course_generate(
    topic: Annotated[
        str,
        typer.Argument(help="What to teach, e.g. 'Introduction to Linear Algebra'"),
    ],
    lectures: Annotated[
        int,
        typer.Option("--lectures", "-n", min=2, max=8, help="Number of lectures (2–8, default 4)"),
    ] = 4,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Output directory (default: content/courses/YYYY-MM-DD-slug)"),
    ] = None,
    tts: Annotated[
        bool,
        typer.Option("--tts/--no-tts", help="Synthesize per-block TTS audio + SRT/VTT (default: on)"),
    ] = True,
    automanim: Annotated[
        bool,
        typer.Option("--automanim/--no-automanim", help="Generate Manim video scenes (default: on)"),
    ] = True,
    shield: Annotated[
        bool,
        typer.Option("--shield/--no-shield", help="Ollama safety shield before Manim (default: on)"),
    ] = True,
    automanim_backend: Annotated[
        str | None,
        typer.Option("--automanim-backend", help="Manim render backend: 'local' or 'docker'"),
    ] = None,
    automanim_output_dir: Annotated[
        Path | None,
        typer.Option("--automanim-out", help="Override Manim video output directory"),
    ] = None,
    generate_site: Annotated[
        bool,
        typer.Option("--site/--no-site", help="Generate Jekyll site after finishing (default: off)"),
    ] = False,
    site_output_dir: Annotated[
        Path | None,
        typer.Option("--site-out", help="Parent directory for generated site"),
    ] = None,
    continue_on_error: Annotated[
        bool,
        typer.Option("--continue-on-error", help="Keep going if a lecture phase fails"),
    ] = True,
) -> None:
    """Generate a full course from a single topic string.

    Equivalent to:  ./scripts/run_full_course_pipeline.sh "Topic" --lectures 4

    Examples:

    \\b
        educlaw course generate "Introduction to Linear Algebra" --lectures 4

        educlaw course generate "Calculus basics" --lectures 2 --no-tts --no-automanim

        educlaw course generate "Python data structures" --lectures 6 \\
            --automanim-backend docker --site
    """
    from educlaw.autocourse.pipeline import PipelineConfig, run_pipeline

    cfg = PipelineConfig(
        topic=topic,
        lectures=lectures,
        out=out,
        enable_tts=tts,
        enable_automanim=automanim,
        enable_shield=shield,
        automanim_backend=automanim_backend,
        automanim_output_dir=automanim_output_dir,
        generate_site=generate_site,
        site_output_dir=site_output_dir,
        continue_on_error=continue_on_error,
    )
    exit_code, out_dir = asyncio.run(run_pipeline(cfg))
    typer.secho(f"\nArtifacts: {out_dir}", fg=typer.colors.CYAN)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


# ---------------------------------------------------------------------------
# educlaw dataset — SFT dataset generation via teacher models (OpenRouter / LiteLLM)
# ---------------------------------------------------------------------------

dataset_typer = typer.Typer(
    help="Generate SFT/distillation datasets using teacher models (OpenRouter, LiteLLM).",
    no_args_is_help=True,
)
app.add_typer(dataset_typer, name="dataset")


@dataset_typer.command("generate")
def dataset_generate(
    backend: Annotated[
        str,
        typer.Option(
            "--backend", "-b",
            help=(
                "Generation backend: 'local' uses the local Ollama pipeline (no API key needed); "
                "'api' calls an OpenRouter/LiteLLM-compatible API."
            ),
        ),
    ] = "local",
    runs: Annotated[
        int,
        typer.Option("--runs", "-r", help="Number of topics to generate (default 100)"),
    ] = 100,
    model: Annotated[
        str,
        typer.Option(
            "--model", "-m",
            help=(
                "[api backend] Teacher model slug. "
                "Examples: anthropic/claude-sonnet-4-5, openai/gpt-4o, google/gemini-2.5-pro. "
                "For a local LiteLLM proxy: ollama/gemma3:27b"
            ),
        ),
    ] = "anthropic/claude-sonnet-4-5",
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", envvar="OPENROUTER_API_KEY", help="[api backend] API key ($OPENROUTER_API_KEY)"),
    ] = None,
    base_url: Annotated[
        str,
        typer.Option(
            "--base-url",
            help=(
                "[api backend] OpenAI-compatible API base URL (default: OpenRouter). "
                "Use 'http://localhost:4000' for a local LiteLLM proxy."
            ),
        ),
    ] = "https://openrouter.ai/api/v1",
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="JSONL output file (default: dataset/sft.jsonl)"),
    ] = Path("dataset/sft.jsonl"),
    topics: Annotated[
        str | None,
        typer.Option("--topics", help="Comma-separated topics (default: built-in pool of 50+ topics)"),
    ] = None,
    topics_file: Annotated[
        Path | None,
        typer.Option("--topics-file", help="Text file with one topic per line"),
    ] = None,
    lectures: Annotated[
        int,
        typer.Option("--lectures", "-n", min=1, max=8, help="Lectures per topic (default 3)"),
    ] = 3,
    workers: Annotated[
        int,
        typer.Option("--workers", "-w", help="Parallel workers (default: 1 for local, 4 for api)"),
    ] = 0,
    manim: Annotated[
        bool,
        typer.Option("--manim/--no-manim", help="[api backend] Also generate Manim codegen pairs (default: off)"),
    ] = False,
    tts: Annotated[
        bool,
        typer.Option("--tts/--no-tts", help="[local backend] Enable TTS synthesis to get audio_script pairs (default: off)"),
    ] = False,
    resume: Annotated[
        bool,
        typer.Option("--resume", help="Skip topics already in the output file"),
    ] = False,
    push_hf: Annotated[
        str | None,
        typer.Option(
            "--push-hf",
            help=(
                "After generation, push the JSONL to HuggingFace as this repo id. "
                "E.g. 'nabin2004/educlaw-lectures'. Requires $HF_TOKEN or --hf-token."
            ),
        ),
    ] = None,
    hf_token: Annotated[
        str | None,
        typer.Option("--hf-token", envvar="HF_TOKEN", help="HuggingFace token for dataset push"),
    ] = None,
    hf_private: Annotated[
        bool,
        typer.Option("--hf-private/--hf-public", help="Make the HuggingFace dataset private (default: private)"),
    ] = True,
    hf_test_size: Annotated[
        float,
        typer.Option("--hf-test-size", help="Fraction held out as test split for HF push (0 = train only)"),
    ] = 0.0,
) -> None:
    """Generate an SFT dataset using either the local Ollama pipeline or a remote API.

    Creates ShareGPT-format JSONL with conversation pairs per lecture.

    \\b
    --- Local Ollama (default, no API key needed) ---
        educlaw dataset generate --runs 50 --lectures 4

        educlaw dataset generate --runs 100 --tts --lectures 3

    --- OpenRouter (teacher distillation) ---
        export OPENROUTER_API_KEY=sk-or-...
        educlaw dataset generate --backend api --runs 50 --model anthropic/claude-sonnet-4-5

    --- Local LiteLLM proxy (OpenAI-compatible, any model) ---
        litellm --model ollama/gemma3:27b --port 4000
        educlaw dataset generate --backend api --base-url http://localhost:4000 \\
            --model ollama/gemma3:27b --api-key dummy --runs 20

    --- Push to HuggingFace after generation ---
        export HF_TOKEN=hf_...
        educlaw dataset generate --runs 50 --push-hf nabin2004/educlaw-lectures

    --- Resume an interrupted run ---
        educlaw dataset generate --runs 500 --resume --out dataset/sft.jsonl
    """
    import os

    # Normalise backend
    backend = backend.lower().strip()
    if backend not in ("local", "api", "openrouter"):
        typer.secho(
            f"Unknown backend '{backend}'. Choose 'local' or 'api'.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    use_api = backend in ("api", "openrouter")

    # Build topic list
    topic_list: list[str] | None = None
    if topics_file:
        tp = topics_file.expanduser()
        if not tp.is_file():
            typer.secho(f"Topics file not found: {tp}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        topic_list = [
            ln.strip() for ln in tp.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
    elif topics:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]

    out_resolved = out.expanduser().resolve()

    if use_api:
        from educlaw.dataset.openrouter import generate_dataset

        resolved_key = api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LITELLM_API_KEY") or ""
        if not resolved_key:
            typer.secho(
                "No API key found. Set $OPENROUTER_API_KEY or pass --api-key.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        n_workers = workers if workers > 0 else 4
        typer.secho(
            f"Dataset generation [api]: {runs} runs, {lectures} lecture(s) each, "
            f"{n_workers} worker(s), model={model}",
            fg=typer.colors.CYAN,
        )
        typer.secho(f"Output: {out_resolved}", fg=typer.colors.CYAN)

        ok = asyncio.run(
            generate_dataset(
                api_key=resolved_key,
                model=model,
                out_path=out_resolved,
                runs=runs,
                topics=topic_list,
                lectures_per_topic=lectures,
                workers=n_workers,
                include_manim=manim,
                base_url=base_url,
                resume=resume,
            )
        )
    else:
        from educlaw.dataset.local import generate_dataset_local

        n_workers = workers if workers > 0 else 1
        typer.secho(
            f"Dataset generation [local/ollama]: {runs} runs, {lectures} lecture(s) each, "
            f"{n_workers} worker(s), tts={tts}",
            fg=typer.colors.CYAN,
        )
        typer.secho(f"Output: {out_resolved}", fg=typer.colors.CYAN)

        ok = asyncio.run(
            generate_dataset_local(
                out_path=out_resolved,
                runs=runs,
                topics=topic_list,
                lectures_per_topic=lectures,
                workers=n_workers,
                resume=resume,
                enable_tts=tts,
                enable_automanim=False,
                enable_shield=True,
            )
        )

    typer.secho(
        f"\nDone: {ok}/{runs} topics generated → {out_resolved}",
        fg=typer.colors.GREEN,
    )

    # Optional HuggingFace push
    if push_hf:
        from educlaw.train.hf_push import push_jsonl_to_hub

        resolved_hf_token = hf_token or os.environ.get("HF_TOKEN")
        if not resolved_hf_token:
            typer.secho(
                "No HF token. Set $HF_TOKEN or pass --hf-token. Skipping push.",
                fg=typer.colors.YELLOW,
            )
        elif not out_resolved.is_file():
            typer.secho(f"Output file not found: {out_resolved} — skipping push.", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Pushing {out_resolved} → {push_hf} …", fg=typer.colors.CYAN)
            try:
                url = push_jsonl_to_hub(
                    out_resolved,
                    push_hf,
                    token=resolved_hf_token,
                    private=hf_private,
                    test_size=hf_test_size,
                )
                typer.secho(f"Dataset pushed: {url}", fg=typer.colors.GREEN)
            except Exception as exc:
                typer.secho(f"HF push failed: {exc}", fg=typer.colors.RED)
                raise typer.Exit(code=1) from exc


@dataset_typer.command("push-sft")
def dataset_push_sft(
    repo_id: Annotated[
        str,
        typer.Argument(help="HuggingFace dataset repo, e.g. nabin2004/educlaw-lectures"),
    ],
    jsonl: Annotated[
        Path,
        typer.Option("--jsonl", "-f", help="JSONL file to push (default: dataset/sft.jsonl)"),
    ] = Path("dataset/sft.jsonl"),
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", envvar="HF_TOKEN", help="HuggingFace token ($HF_TOKEN)"),
    ] = None,
    private: Annotated[
        bool,
        typer.Option("--private/--public", help="Make the dataset private (default: private)"),
    ] = True,
    test_size: Annotated[
        float,
        typer.Option("--test-size", help="Fraction held out as test split (0 = train only)"),
    ] = 0.0,
) -> None:
    """Push a pre-built SFT JSONL file to HuggingFace Hub.

    Use this after ``educlaw dataset generate`` to upload the result.

    \\b
    Example:
        export HF_TOKEN=hf_...
        educlaw dataset push-sft nabin2004/educlaw-lectures --jsonl dataset/sft.jsonl
        educlaw dataset push-sft nabin2004/educlaw-lectures --public --test-size 0.1
    """
    import os

    from educlaw.train.hf_push import push_jsonl_to_hub

    resolved_token = token or os.environ.get("HF_TOKEN")
    if not resolved_token:
        typer.secho(
            "No HF token. Set $HF_TOKEN or pass --token. "
            "Get yours at https://huggingface.co/settings/tokens",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    jsonl_path = jsonl.expanduser().resolve()
    if not jsonl_path.is_file():
        typer.secho(f"JSONL file not found: {jsonl_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        import json as _json
        n = sum(1 for ln in jsonl_path.read_text(encoding="utf-8").splitlines() if ln.strip())
    except Exception:
        n = 0
    typer.secho(f"Pushing {n} records from {jsonl_path} → {repo_id} …", fg=typer.colors.CYAN)

    try:
        url = push_jsonl_to_hub(
            jsonl_path,
            repo_id,
            token=resolved_token,
            private=private,
            test_size=test_size,
        )
    except ImportError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.secho(f"Push failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    visibility = "private" if private else "public"
    typer.secho(f"Dataset pushed ({visibility}): {url}", fg=typer.colors.GREEN)


@dataset_typer.command("push-manim-sft")
def dataset_push_manim_sft(
    repo_id: Annotated[
        str,
        typer.Argument(help="HuggingFace dataset repo, e.g. nabin2004/educlaw-manim-sft"),
    ],
    jsonl: Annotated[
        Path,
        typer.Option("--jsonl", "-f", help="Manim SFT JSONL file (default: dataset/manim_sft.jsonl)"),
    ] = Path("dataset/manim_sft.jsonl"),
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", envvar="HF_TOKEN", help="HuggingFace token ($HF_TOKEN)"),
    ] = None,
    private: Annotated[
        bool,
        typer.Option("--private/--public", help="Make the dataset private (default: private)"),
    ] = True,
    test_size: Annotated[
        float,
        typer.Option("--test-size", help="Fraction held out as test split (0 = train only)"),
    ] = 0.0,
) -> None:
    """Push the Manim SFT JSONL (messages format) to HuggingFace Hub.

    Validates that every record has the Gemma4 messages format
    (role/content pairs) and prints dataset stats before uploading.

    \\b
    Example:
        export HF_TOKEN=hf_...
        educlaw dataset push-manim-sft nabin2004/educlaw-manim-sft
        educlaw dataset push-manim-sft nabin2004/educlaw-manim-sft --jsonl dataset/manim_sft.jsonl --public
    """
    import os

    from educlaw.train.hf_push import push_manim_sft_to_hub

    resolved_token = token or os.environ.get("HF_TOKEN")
    if not resolved_token:
        typer.secho(
            "No HF token. Set $HF_TOKEN or pass --token. "
            "Get yours at https://huggingface.co/settings/tokens",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    jsonl_path = jsonl.expanduser().resolve()
    if not jsonl_path.is_file():
        typer.secho(f"JSONL file not found: {jsonl_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Validating {jsonl_path} ...", fg=typer.colors.CYAN)

    try:
        url, stats = push_manim_sft_to_hub(
            jsonl_path,
            repo_id,
            token=resolved_token,
            private=private,
            test_size=test_size,
        )
    except ImportError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.secho(f"Push failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    visibility = "private" if private else "public"
    typer.secho(
        f"\nDataset pushed ({visibility}): {url}\n"
        f"  Records   : {stats['total']} training examples\n"
        f"  Topics    : {stats['unique_topics']} unique\n"
        f"  Avg code  : {stats['avg_code_chars']} chars/scene\n"
        f"  Skipped   : {stats['skipped']} malformed lines",
        fg=typer.colors.GREEN,
    )


def main() -> None:
    is_tty = getattr(sys.stdout, "isatty", lambda: False)()
    if not sys.argv[1:] and is_tty and _play_intro(sys.stdout):
        typer.echo()
    app()


if __name__ == "__main__":
    main()
