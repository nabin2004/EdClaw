import json
import logging

import pytest

from educlaw.automanim.planner import parse_viz_plan


def test_parse_viz_plan_caps_scenes() -> None:
    raw = json.dumps(
        {
            "scenes": [
                {"title": f"S{i}", "description": "d", "visual_intent": "v"}
                for i in range(10)
            ]
        }
    )
    plan = parse_viz_plan(raw, max_scenes=3)
    assert len(plan.scenes) == 3
    assert plan.scenes[0].title == "S0"


def test_parse_viz_plan_strips_fence() -> None:
    raw = """```json
{"scenes": [{"title": "A", "description": "", "visual_intent": ""}]}
```"""
    plan = parse_viz_plan(raw, max_scenes=6)
    assert len(plan.scenes) == 1
    assert plan.scenes[0].title == "A"


def test_parse_viz_plan_invalid_json_logs_context(caplog: pytest.LogCaptureFixture) -> None:
    # Invalid escape \\l in JSON string (common when models emit LaTeX).
    raw = r'{"scenes": [{"title": "T", "description": "see \lambda", "visual_intent": ""}]}'
    with caplog.at_level(logging.ERROR, logger="educlaw.automanim.planner"):
        with pytest.raises(json.JSONDecodeError):
            parse_viz_plan(raw, max_scenes=6)
    assert "automanim planner JSON parse failed" in caplog.text
    assert "len_text=" in caplog.text
    assert "lambda" in caplog.text
