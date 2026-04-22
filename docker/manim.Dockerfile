# Manim worker (stub — pin manim-community + ffmpeg in production)
FROM python:3.11-slim-bookworm
RUN pip install --no-cache-dir manim
WORKDIR /work
CMD ["manim", "--version"]
