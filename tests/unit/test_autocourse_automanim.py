import json
from unittest.mock import AsyncMock

import pytest

from educlaw.autocourse.orchestrator import run_autocourse
from educlaw.automanim.schema import AutoManimEvent
from educlaw.config.settings import Settings
from educlaw.safety.shield import Shield, Verdict


class _FakeOllama:
    def __init__(self, plan: dict, lecture_md: str) -> None:
        self._plan_json = json.dumps(plan)
        self._lecture_md = lecture_md

    async def chat(self, model: str, messages: list, **kwargs: object) -> dict:
        if kwargs.get("format") == "json":
            return {"message": {"content": self._plan_json}}
        return {"message": {"content": self._lecture_md}}


@pytest.mark.asyncio
async def test_autocourse_emits_automanim_events(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = {
        "title": "Tiny",
        "audience": "x",
        "lectures": [
            {
                "title": "Only",
                "objectives": ["a"],
                "key_topics": ["b"],
            },
        ],
    }
    fake = _FakeOllama(plan, "# L\n\nok")

    async def fake_am(*_a, **_k):
        yield AutoManimEvent(kind="plan", lecture_id="x", message="1")
        yield AutoManimEvent(kind="done", lecture_id="x", message="fin")

    monkeypatch.setattr("educlaw.autocourse.orchestrator.run_automanim", fake_am)
    monkeypatch.setattr(Shield, "classify", AsyncMock(return_value=Verdict.ALLOW))

    settings = Settings(automanim_enabled=True)
    events = [e async for e in run_autocourse("topic", settings, fake)]  # type: ignore[arg-type]

    assert any(e.kind == "automanim" for e in events)
    am_events = [e for e in events if e.kind == "automanim"]
    assert am_events[0].automanim is not None
    assert am_events[0].automanim.kind == "plan"
    dumped = am_events[0].model_dump(mode="json")
    assert dumped["kind"] == "automanim"
    assert dumped["automanim"]["kind"] == "plan"


@pytest.mark.asyncio
async def test_autocourse_passes_noop_shield_when_shield_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "title": "Tiny",
        "audience": "x",
        "lectures": [
            {
                "title": "Only",
                "objectives": ["a"],
                "key_topics": ["b"],
            },
        ],
    }
    fake = _FakeOllama(plan, "# L\n\nok")
    captured: dict[str, str] = {}

    async def fake_run_am(
        _md: str,
        _meta: dict,
        _settings: object,
        shield: object,
        **_kw: object,
    ):
        captured["shield_cls"] = type(shield).__name__
        yield AutoManimEvent(kind="done", lecture_id="x", message="fin")

    monkeypatch.setattr("educlaw.autocourse.orchestrator.run_automanim", fake_run_am)

    settings = Settings(automanim_enabled=True, shield_enabled=False)
    events = [e async for e in run_autocourse("topic", settings, fake)]  # type: ignore[arg-type]

    assert any(e.kind == "automanim" for e in events)
    assert captured["shield_cls"] == "NoopShield"
