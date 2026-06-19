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
    tts_max_chars: Annotated[
        int,
        typer.Option("--tts-max-chars", help="Max plain-text chars per lecture for TTS"),
    ] = 12_000,
    tts_chunk_chars: Annotated[
        int,
        typer.Option("--tts-chunk-chars", help="Max chars per TTS call chunk"),
    ] = 320,
) -> None:
    """Generate a full course: plan → lectures → TTS audio → Manim animations.

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
        tts_max_chars=tts_max_chars,
        tts_chunk_chars=tts_chunk_chars,
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

    async def _run() -> None:
        client = AsyncClient(host=s.ollama_url.rstrip("/"))
        shield_impl: Shield | NoopShield = (
            Shield(client, model=s.shield_model) if s.shield_enabled else NoopShield()
        )
        scenes_data: list[dict] = []
        try:
            async for ev in run_automanim(markdown, meta, s, shield_impl, ollama=client):
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
            async for ev in run_automanim(
                markdown, meta, s, shield_impl, ollama=client, output_root=output_root
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
                async for ev in run_automanim(
                    str(post.content),
                    meta,
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


def main() -> None:
    is_tty = getattr(sys.stdout, "isatty", lambda: False)()
    if not sys.argv[1:] and is_tty and _play_intro(sys.stdout):
        typer.echo()
    app()


if __name__ == "__main__":
    main()
