"""Dynamic voice catalog that scans filesystem for Piper models and includes Parler voices.

This module automatically discovers all .onnx model files in the MODELS_DIR
and generates voice metadata dynamically. Also includes pre-defined Parler voices.
"""
from typing import List, Dict, Optional
import os
from pathlib import Path
import logging

_LOGGER = logging.getLogger(__name__)

# Base models directory can be overridden with MODELS_DIR env var (defaults to /models)
MODELS_DIR = os.getenv("MODELS_DIR", "/models")

# Cache for discovered voices (populated on first access)
_VOICE_CATALOG_CACHE: Optional[List[Dict]] = None

# Parler TTS voices (Indian regional languages and more)
# NOTE: Commenting out Parler - using Piper models instead which are lighter and simpler
_PARLER_VOICES = []

# Instead, we'll use Piper's built-in Indian language models:
# - hi_IN-pratham-medium (Hindi)
# - hi_IN-priyamvada-medium (Hindi - female)
# - hi_IN-rohan-medium (Hindi)
# - te_IN-rama-medium (Telugu)


def _scan_models_directory() -> List[Dict]:
    """Scan MODELS_DIR for .onnx files and build voice catalog."""
    voices = []
    models_path = Path(MODELS_DIR)
    
    if not models_path.exists():
        _LOGGER.warning(f"Models directory does not exist: {MODELS_DIR}")
        return voices
    
    try:
        # Scan for directories containing .onnx files
        for item in models_path.iterdir():
            if not item.is_dir():
                continue
            
            # Find .onnx files in this directory
            onnx_files = list(item.glob("*.onnx"))
            if not onnx_files:
                continue
            
            # Use the first .onnx file found
            onnx_file = onnx_files[0]
            voice_id = item.name  # Folder name is the voice ID
            
            # Parse language and voice name from ID (e.g., "en_US-lessac-medium")
            parts = voice_id.split("-")
            language = parts[0] if parts else "unknown"
            voice_name = "-".join(parts[1:]) if len(parts) > 1 else voice_id
            
            # Build display name
            lang_display = language.replace("_", " ").title()
            display_name = f"{lang_display} - {voice_name.replace('-', ' ').title()}"
            
            voices.append({
                "id": voice_id,
                "display_name": display_name,
                "language": language,
                "gender": "neutral",  # Could parse from .json config if available
                "engine": "piper",
                "model_path": str(onnx_file.absolute()),
                "available": True,
            })
            
    except Exception as e:
        _LOGGER.error(f"Error scanning models directory {MODELS_DIR}: {e}")
    
    _LOGGER.info(f"Discovered {len(voices)} voice models in {MODELS_DIR}")
    return voices


def list_voices() -> List[Dict]:
    """Return all discovered voices (Piper + Parler)."""
    global _VOICE_CATALOG_CACHE
    if _VOICE_CATALOG_CACHE is None:
        _VOICE_CATALOG_CACHE = _scan_models_directory() + _PARLER_VOICES
    return _VOICE_CATALOG_CACHE.copy()


def list_available_voices() -> List[Dict]:
    """Return only available voices."""
    return [v for v in list_voices() if v.get("available")]


def get_voice(voice_id: str) -> Optional[Dict]:
    """Get a specific voice by ID. If not found, rescan and try again."""
    # First attempt with current cache
    for v in list_voices():
        if v.get("id") == voice_id:
            return v
    
    # If not found, refresh cache and try again (handles case where models were added after startup)
    global _VOICE_CATALOG_CACHE
    _VOICE_CATALOG_CACHE = None
    for v in list_voices():
        if v.get("id") == voice_id:
            return v
    
    return None


def engine_for_voice(voice_id: str) -> Optional[str]:
    """Return the engine name for a given voice id (e.g. 'piper')."""
    v = get_voice(voice_id)
    if not v:
        return None
    return v.get("engine")


def refresh_catalog():
    """Force a rescan of the models directory."""
    global _VOICE_CATALOG_CACHE
    _VOICE_CATALOG_CACHE = None
    _LOGGER.info("Voice catalog cache cleared - will rescan on next access")
