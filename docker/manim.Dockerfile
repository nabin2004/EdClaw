# Manim CE worker for AutoManim / queue_manim_render (pinned deps + ffmpeg + non-root)
FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1
# Pin major line; bump intentionally when validating renders.
RUN pip install --no-cache-dir "manim>=0.18.0,<0.20.0"

RUN useradd -m -u 65532 automan \
    && mkdir -p /work \
    && chown automan:automan /work

USER automan
WORKDIR /work

CMD ["manim", "--version"]
