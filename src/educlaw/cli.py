"""Typer CLI: ``educlaw`` entry point."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Annotated

import httpx
import typer
import uvicorn

from educlaw.config.settings import load_settings
from educlaw.config.strict_local import assert_strict_local
from educlaw.ir.loader import lint, load_all

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
        for want in (s.model_id, s.embedding_model, s.shield_model):
            if not any(n.startswith(want.split(":")[0]) for n in names):
                typer.secho(
                    f"Warning: model matching {want!r} not found in ollama list",
                    fg=typer.colors.YELLOW,
                )
    except Exception as e:
        typer.secho(f"Ollama check failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e


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


@app.command("pull-models")
def pull_models() -> None:
    """Shell out to ``ollama pull`` for default Gemma stack."""
    s = load_settings()
    for m in (s.model_id, s.embedding_model, s.shield_model):
        typer.echo(f"ollama pull {m}")
        subprocess.run(["ollama", "pull", m], check=False)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
