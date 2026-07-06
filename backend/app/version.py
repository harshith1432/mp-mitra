"""
Central version module — reads from version.json at project root.
All backend modules should import from here instead of hardcoding versions.
"""
import json
import os

def _load_version() -> dict:
    """Load version info from version.json at project root."""
    # Walk up from this file to find version.json
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        candidate = os.path.join(here, "version.json")
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)
        here = os.path.dirname(here)
    # Fallback defaults
    return {
        "version": "1.0.0",
        "channel": "stable",
        "build": "unknown",
        "release_date": "unknown",
    }

_info = _load_version()

VERSION       = _info.get("version", "1.0.0")
CHANNEL       = _info.get("channel", "stable")
BUILD         = _info.get("build", "unknown")
RELEASE_DATE  = _info.get("release_date", "unknown")

__version__   = VERSION
