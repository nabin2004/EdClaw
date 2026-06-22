import json
import logging

import pytest

from educlaw.automanim.planner import parse_viz_plan
from educlaw.tts.md_to_srt import SubtitleBlock


def _blocks(n: int = 0) -> list[SubtitleBlock]:
    return [
        SubtitleBlock(index=i + 1, text=f"Block {i+1}", tts_text=f"Block {i+1}", start_ms=i * 5000, end_ms=(i + 1) * 5000)
        for i in range(n)
    ]


def test_parse_viz_plan_caps_scenes() -> None:
    raw = json.dumps(
        {
            "scenes": [
                {"title": f"S{i}", "description": "d", "visual_intent": "v"}
                for i in range(10)
            ]
        }
    )
    plan = parse_viz_plan(raw, max_scenes=3, subtitle_blocks=_blocks())
    assert len(plan.scenes) == 3
    assert plan.scenes[0].title == "S0"


def test_parse_viz_plan_strips_fence() -> None:
    raw = """```json
{"scenes": [{"title": "A", "description": "", "visual_intent": ""}]}
```"""
    plan = parse_viz_plan(raw, max_scenes=6, subtitle_blocks=_blocks())
    assert len(plan.scenes) == 1
    assert plan.scenes[0].title == "A"


def test_parse_viz_plan_invalid_json_logs_context(caplog: pytest.LogCaptureFixture) -> None:
    # Ensure log propagates to root logger so caplog can capture it
    logger = logging.getLogger("educlaw.automanim")
    old_prop = logger.propagate
    logger.propagate = True
    try:
        # Truncated JSON — cannot be fixed by any backslash substitution.
        raw = '{"scenes": [{"title": "Missing end bracket"'
        with caplog.at_level(logging.ERROR, logger="educlaw.automanim.adk.planner"):
            with pytest.raises(json.JSONDecodeError):
                parse_viz_plan(raw, max_scenes=6, subtitle_blocks=_blocks())
        assert "automanim planner JSON parse failed" in caplog.text
        assert "len_text=" in caplog.text
    finally:
        logger.propagate = old_prop
