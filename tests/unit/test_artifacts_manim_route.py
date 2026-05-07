"""``GET /artifacts/manim`` path safety."""

from __future__ import annotations
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from educlaw.gateway.app import app


def test_artifacts_manim_rejects_traversal(monkeypatch: pytest.MonkeyPatch) -> None:
    import educlaw.gateway.run as gw_run

    monkeypatch.setattr(gw_run._settings, "automanim_output_dir", Path("/tmp/educlaw-am-test"))

    with TestClient(app) as client:
        r = client.get("/artifacts/manim/../../../etc/passwd")
        assert r.status_code == 404


def test_artifacts_manim_missing_file_404(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import educlaw.gateway.run as gw_run

    root = tmp_path / "am"
    root.mkdir()
    monkeypatch.setattr(gw_run._settings, "automanim_output_dir", root)

    with TestClient(app) as client:
        r = client.get("/artifacts/manim/nothing.mp4")
        assert r.status_code == 404
