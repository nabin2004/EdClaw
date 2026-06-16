"""EduClaw — educational agent gateway (ADK-native, local-first)."""

import warnings

# Suppress experimental feature warnings from google-adk (e.g. PLUGGABLE_AUTH)
warnings.filterwarnings("ignore", category=UserWarning, message=".*EXPERIMENTAL.*feature.*")

__version__ = "0.1.0"
