from typing import Dict

def select_engine_for_voice(voice_id: str, language: str) -> Dict[str, str]:
    """Return engine routing info for a given voice/language.

    This is a placeholder. Real implementation should consult the `voices` DB
    or configuration to decide which engine (piper/parler) to use and any
    per-engine parameters.
    """
    # placeholder mapping: voices starting with 'en_' -> piper
    if voice_id.startswith("en_") or language.startswith("en"):
        return {"engine": "piper", "url": "http://piper:5000/"}
    return {"engine": "piper", "url": "http://piper:5000/"}
