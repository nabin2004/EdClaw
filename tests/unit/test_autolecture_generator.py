import pytest

from educlaw.autolecture.generator import generate_lecture
from educlaw.autolecture.schema import LectureOutline


class _FakeOllama:
    async def chat(self, model: str, messages: list, **kwargs: object) -> dict:
        assert "temperature" in (kwargs.get("options") or {})
        return {"message": {"content": "## Hook\n\nBody here."}}


@pytest.mark.asyncio
async def test_generate_lecture_returns_markdown_and_ir_hint() -> None:
    outline = LectureOutline(
        title="Vectors",
        objectives=["Define a vector"],
        key_topics=["magnitude", "direction"],
    )
    r = await generate_lecture(
        _FakeOllama(),  # type: ignore[arg-type]
        "gemma3:latest",
        outline,
        course_title="Linear Algebra",
        lecture_index=1,
        lecture_count=3,
        prior_lecture_titles=[],
    )
    assert "Hook" in r.markdown
    assert r.ir_suggestion.get("title") == "Vectors"
    assert r.ir_suggestion.get("id") == "vectors.1"
