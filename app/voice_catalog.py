"""Hard-coded voice catalog for development/testing.

This module provides a small, fixed set of voices and helper accessors
so the system does not perform any dynamic scanning or syncing during
startup. Keep the catalog limited to the three development voices.
"""
from typing import List, Dict, Optional
import os
from pathlib import Path

# Base models directory can be overridden with MODELS_DIR env var (defaults to ../piper_models)
MODELS_DIR = os.getenv("MODELS_DIR", os.path.abspath(os.path.join(os.getcwd(), "..", "piper_models")))

def _model_path(*parts: str) -> str:
    return str(Path(MODELS_DIR).joinpath(*parts))

VOICE_CATALOG: List[Dict] = [
    {
        "id": "en_US-lessac-medium",
        "display_name": "English (US) - Lessac (medium)",
        "language": "en_US",
        "gender": "neutral",
        "engine": "piper",
        "model_path": _model_path("en_US-lessac-medium", "en_US-lessac-medium.onnx"),
        "available": True,
    },
    {
        "id": "hi_IN-rohan-medium",
        "display_name": "Hindi (IN) - Rohan (medium)",
        "language": "hi_IN",
        "gender": "male",
        "engine": "piper",
        # model file present in repo under this directory is named
        # hi_IN-pratham-medium.onnx; point to the actual filename to avoid
        # failing to load at runtime.
        "model_path": _model_path("hi_IN-rohan-medium", "hi_IN-pratham-medium.onnx"),
        "available": True,
    },
    {
        "id": "hi_IN-priyamvada-medium",
        "display_name": "Hindi (IN) - Priyamvada (medium)",
        "language": "hi_IN",
        "gender": "female",
        "engine": "piper",
        "model_path": _model_path("hi_IN-priyamvada-medium", "hi_IN-priyamvada-medium.onnx"),
        "available": True,
    },
]


def list_voices() -> List[Dict]:
    return VOICE_CATALOG.copy()


def list_available_voices() -> List[Dict]:
    return [v for v in VOICE_CATALOG if v.get("available")]


def get_voice(voice_id: str) -> Optional[Dict]:
    for v in VOICE_CATALOG:
        if v.get("id") == voice_id:
            return v
    return None


def engine_for_voice(voice_id: str) -> Optional[str]:
    """Return the engine name for a given voice id (e.g. 'piper')."""
    v = get_voice(voice_id)
    if not v:
        return None
    return v.get("engine")
