"""Gateway static assets and manim artifact MIME types."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from educlaw.gateway.app import app


def test_static_player_css() -> None:
    with TestClient(app) as client:
        res = client.get("/static/player.css")
    assert res.status_code == 200
    assert "media-minimal-skin" in res.text


def test_static_educlaw_player_js() -> None:
    with TestClient(app) as client:
        res = client.get("/static/educlaw-player.js")
    assert res.status_code == 200
    assert "EduClawMedia" in res.text


def test_manim_artifact_subtitle_mime_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import educlaw.gateway.run as gw_run

    monkeypatch.setattr(gw_run._settings, "automanim_output_dir", str(tmp_path))

    vtt = tmp_path / "demo.vtt"
    vtt.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHi\n", encoding="utf-8")
    srt = tmp_path / "demo.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")

    with TestClient(app) as client:
        vtt_res = client.get("/artifacts/manim/demo.vtt")
        srt_res = client.get("/artifacts/manim/demo.srt")

    assert vtt_res.status_code == 200
    assert vtt_res.headers["content-type"].startswith("text/vtt")
    assert srt_res.status_code == 200
    assert srt_res.headers["content-type"].startswith("application/x-subrip")
