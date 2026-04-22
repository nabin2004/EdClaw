from pathlib import Path


def content_root() -> Path:
    return Path(__file__).resolve().parent / "content"
