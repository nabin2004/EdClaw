import json

import pytest

from educlaw.autocourse.orchestrator import run_autocourse
from educlaw.config.settings import Settings


class _FakeOllama:
    def __init__(self, plan: dict, lecture_md: str) -> None:
        self._plan_json = json.dumps(plan)
        self._lecture_md = lecture_md
        self.chat_calls = 0

    async def chat(self, model: str, messages: list, **kwargs: object) -> dict:
        self.chat_calls += 1
        if kwargs.get("format") == "json":
            return {"message": {"content": self._plan_json}}
        return {"message": {"content": self._lecture_md}}


@pytest.mark.asyncio
async def test_run_autocourse_streams_plan_lectures_done() -> None:
    plan = {
        "title": "Tiny course",
        "audience": "Testers",
        "lectures": [
            {
                "title": "First",
                "objectives": ["Learn A"],
                "key_topics": ["A"],
                "estimated_minutes": 10,
            },
            {
                "title": "Second",
                "objectives": ["Learn B"],
                "key_topics": ["B"],
            },
        ],
    }
    fake = _FakeOllama(plan, "# Lecture\n\nOK.")
    settings = Settings()
    events = [e async for e in run_autocourse("topic here", settings, fake)]  # type: ignore[arg-type]

    kinds = [e.kind for e in events]
    assert kinds[0] == "plan"
    assert "lecture_start" in kinds
    assert kinds.count("lecture_done") == 2
    assert kinds[-1] == "done"
    assert fake.chat_calls == 3  # 1 plan + 2 lectures


@pytest.mark.asyncio
async def test_run_autocourse_invalid_plan_json() -> None:
    class _Bad:
        async def chat(self, model: str, messages: list, **kwargs: object) -> dict:
            return {"message": {"content": "not-json"}}

    settings = Settings()
    events = [e async for e in run_autocourse("x", settings, _Bad())]  # type: ignore[arg-type]
    assert len(events) == 1
    assert events[0].kind == "error"
    assert events[0].message


@pytest.mark.asyncio
async def test_run_autocourse_empty_lectures() -> None:
    plan = {"title": "Empty", "audience": "x", "lectures": []}
    fake = _FakeOllama(plan, "n/a")
    settings = Settings()
    events = [e async for e in run_autocourse("x", settings, fake)]  # type: ignore[arg-type]
    assert len(events) == 1
    assert events[0].kind == "error"
    assert "no lectures" in (events[0].message or "").lower()
