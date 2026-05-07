# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Optional dependency group `educlaw[automanim]` installing **Manim CE** (`manim>=0.18.0`).
- Setting `automanim_docker_user` for Docker Manim runs (`auto`, `none`, or a literal `uid:gid` on POSIX).
- Richer AutoManim scene outputs: manifest / events can carry `scene_dir`, `source_path`, and `log_path` when available.
- `educlaw doctor` warns when AutoManim is configured for **local** rendering but Manim is not available (install extra or switch backend).

### Changed

- Default `automanim_image` to `manimcommunity/manim:stable` (replacing `educlaw/manim:latest`).
- AutoManim local and Docker render paths improved (logging, artifact paths, scene directory reporting).
- Expanded unit and integration tests for the orchestrator and local render helpers.

### Repository

- Example Manim outputs under `media/` from a local `TheLinearEquationComponents` run (SVG/TeX intermediates and 480p15 partials).
