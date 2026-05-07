"""Typer CLI: ``educlaw`` entry point."""

from __future__ import annotations

import asyncio
import subprocess
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


@app.command("automanim")
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
                    if ev.kind == "scene_done" and ev.artifact and ev.artifact.artifact_path:
                        manifest[lecture_id].append(
                            {
                                "scene_index": ev.scene_index,
                                "scene_title": ev.scene_title,
                                "artifact_path": ev.artifact.artifact_path,
                                "exit_code": ev.artifact.exit_code,
                            }
                        )
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
    app()


if __name__ == "__main__":
    main()
