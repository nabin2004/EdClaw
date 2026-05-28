"""Compatibility shim — implementation in ``educlaw.automanim.adk.render``."""

from educlaw.automanim.adk.render import *  # noqa: F403
from educlaw.automanim.adk.render import (
    _docker_render_sync,
    _docker_user_run_args,
)
