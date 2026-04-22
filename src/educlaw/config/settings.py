"""Pydantic-settings + TOML profile loader."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_profile_path() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "profiles" / "local.toml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EDUCLAW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    profile_path: Path = Field(default_factory=_default_profile_path)
    app_name: str = "educlaw"
    gateway_host: str = "127.0.0.1"
    gateway_port: int = 18789

    # Ollama / LiteLLM (ADK uses ollama_chat/*; set OLLAMA_API_BASE in env)
    ollama_url: str = "http://127.0.0.1:11434"
    model_id: str = "gemma3:latest"
    embedding_model: str = "embeddinggemma"
    embedding_dim: int = 768
    shield_model: str = "shieldgemma:2b"

    data_dir: Path = Field(default_factory=lambda: Path.home() / ".educlaw")
    ir_root: Path | None = None
    sqlite_path: Path | None = None
    vec_sqlite_path: Path | None = None

    strict_local: bool = True
    sandbox_backend: Literal["docker", "ssh", "local_jail"] = "docker"
    sandbox_mode: Literal["off", "non_main", "all"] = "all"

    # Text-to-speech (optional; see docs/TTS.md)
    tts_enabled: bool = False
    tts_backend: str = "kitten"
    tts_model_id: str | None = None
    tts_voice: str | None = None
    tts_speed: float = 1.0
    tts_sample_rate: int = 24000
    tts_cache_dir: Path | None = None

    def model_post_init(self, __context: object) -> None:
        if self.ir_root is None:
            repo_ir = Path(__file__).resolve().parents[3] / "content" / "ir"
            object.__setattr__(
                self,
                "ir_root",
                repo_ir if repo_ir.exists() else (self.data_dir / "ir"),
            )
        if self.sqlite_path is None:
            object.__setattr__(self, "sqlite_path", self.data_dir / "educlaw.sqlite")
        if self.vec_sqlite_path is None:
            object.__setattr__(self, "vec_sqlite_path", self.data_dir / "vectors.sqlite")
        if self.tts_cache_dir is None:
            object.__setattr__(self, "tts_cache_dir", self.data_dir / "tts")


def _merge_toml_into_environ(profile: dict) -> None:
    """Apply [env] section from profile TOML (optional)."""
    env_section = profile.get("env") if isinstance(profile, dict) else None
    if not isinstance(env_section, dict):
        return
    for k, v in env_section.items():
        os.environ.setdefault(str(k), str(v))


def load_settings() -> Settings:
    s = Settings()
    path = Path(os.environ.get("EDUCLAW_PROFILE_PATH", s.profile_path))
    if path.exists():
        # ruamel can load TOML if tomli not required — use built-in tomllib for read
        import tomllib

        with path.open("rb") as f:
            data = tomllib.load(f)
        _merge_toml_into_environ(data)
        flat = {k: v for k, v in data.items() if k != "env" and not isinstance(v, dict)}
        nested = data.get("educlaw") if isinstance(data.get("educlaw"), dict) else {}
        merged: dict[str, Any] = {**cast(dict[str, Any], flat), **cast(dict[str, Any], nested)}
        if "data_dir" in merged:
            merged["data_dir"] = Path(os.path.expanduser(str(merged["data_dir"])))
        if "ir_root" in merged:
            merged["ir_root"] = Path(os.path.expanduser(str(merged["ir_root"])))
        if "sqlite_path" in merged:
            merged["sqlite_path"] = Path(os.path.expanduser(str(merged["sqlite_path"])))
        if "vec_sqlite_path" in merged:
            merged["vec_sqlite_path"] = Path(os.path.expanduser(str(merged["vec_sqlite_path"])))
        if "tts_cache_dir" in merged:
            merged["tts_cache_dir"] = Path(os.path.expanduser(str(merged["tts_cache_dir"])))
        s = Settings(**{**s.model_dump(), **merged})
    # Ensure OLLAMA_API_BASE for LiteLLM (ADK docs)
    os.environ.setdefault("OLLAMA_API_BASE", s.ollama_url.rstrip("/"))
    return s
