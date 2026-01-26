from .mongo_db import get_voice, put_voice, list_voices
from .mongodb import init_mongodb

# Expanded voice catalog including Piper and Parler entries.
# This is a representative catalog — add or refine model_path values
# to match your local `/piper_models` layout.
DEFAULT_VOICES = [
    # English (US) examples
    {"id": "en_US-lessac-medium", "engine": "piper", "language": "en_US", "display_name": "Lessac (en_US)", "model_path": "/models/en_US-lessac-medium/en_US-lessac-medium.onnx", "supports_alignments": False},
    {"id": "en_US-male-medium", "engine": "piper", "language": "en_US", "display_name": "Male (en_US)", "model_path": "/models/en_US-male/en_US-male.onnx", "supports_alignments": False},

    # Indian English
    {"id": "en_IN-male", "engine": "piper", "language": "en_IN", "display_name": "Indian English Male", "model_path": "/models/en_IN-male/en_IN-male.onnx", "supports_alignments": False},
    {"id": "en_IN-female", "engine": "piper", "language": "en_IN", "display_name": "Indian English Female", "model_path": "/models/en_IN-female/en_IN-female.onnx", "supports_alignments": False},

    # Hindi
    {"id": "hi-male-medium", "engine": "piper", "language": "hi", "display_name": "Hindi Male", "model_path": "/models/hi-male/hi-male.onnx", "supports_alignments": False},
    {"id": "hi-female-medium", "engine": "piper", "language": "hi", "display_name": "Hindi Female", "model_path": "/models/hi-female/hi-female.onnx", "supports_alignments": False},
    {"id": "hi-parler-v1", "engine": "parler", "language": "hi", "display_name": "Parler Hindi (v1)", "model_path": "", "supports_alignments": True},

    # Tamil
    {"id": "ta-male", "engine": "piper", "language": "ta", "display_name": "Tamil Male", "model_path": "/models/ta-male/ta-male.onnx", "supports_alignments": False},
    {"id": "ta-female", "engine": "piper", "language": "ta", "display_name": "Tamil Female", "model_path": "/models/ta-female/ta-female.onnx", "supports_alignments": False},

    # Telugu
    {"id": "te-male", "engine": "piper", "language": "te", "display_name": "Telugu Male", "model_path": "/models/te-male/te-male.onnx", "supports_alignments": False},
    {"id": "te-female", "engine": "piper", "language": "te", "display_name": "Telugu Female", "model_path": "/models/te-female/te-female.onnx", "supports_alignments": False},

    # Kannada
    {"id": "kn-male", "engine": "piper", "language": "kn", "display_name": "Kannada Male", "model_path": "/models/kn-male/kn-male.onnx", "supports_alignments": False},
    {"id": "kn-female", "engine": "piper", "language": "kn", "display_name": "Kannada Female", "model_path": "/models/kn-female/kn-female.onnx", "supports_alignments": False},

    # Malayalam
    {"id": "ml-male", "engine": "piper", "language": "ml", "display_name": "Malayalam Male", "model_path": "/models/ml-male/ml-male.onnx", "supports_alignments": False},
    {"id": "ml-female", "engine": "piper", "language": "ml", "display_name": "Malayalam Female", "model_path": "/models/ml-female/ml-female.onnx", "supports_alignments": False},

    # Marathi
    {"id": "mr-male", "engine": "piper", "language": "mr", "display_name": "Marathi Male", "model_path": "/models/mr-male/mr-male.onnx", "supports_alignments": False},
    {"id": "mr-female", "engine": "piper", "language": "mr", "display_name": "Marathi Female", "model_path": "/models/mr-female/mr-female.onnx", "supports_alignments": False},

    # Bengali
    {"id": "bn-male", "engine": "piper", "language": "bn", "display_name": "Bengali Male", "model_path": "/models/bn-male/bn-male.onnx", "supports_alignments": False},
    {"id": "bn-female", "engine": "piper", "language": "bn", "display_name": "Bengali Female", "model_path": "/models/bn-female/bn-female.onnx", "supports_alignments": False},

    # Gujarati
    {"id": "gu-male", "engine": "piper", "language": "gu", "display_name": "Gujarati Male", "model_path": "/models/gu-male/gu-male.onnx", "supports_alignments": False},
    {"id": "gu-female", "engine": "piper", "language": "gu", "display_name": "Gujarati Female", "model_path": "/models/gu-female/gu-female.onnx", "supports_alignments": False},

    # Punjabi
    {"id": "pa-male", "engine": "piper", "language": "pa", "display_name": "Punjabi Male", "model_path": "/models/pa-male/pa-male.onnx", "supports_alignments": False},
    {"id": "pa-female", "engine": "piper", "language": "pa", "display_name": "Punjabi Female", "model_path": "/models/pa-female/pa-female.onnx", "supports_alignments": False},

    # Parler entries (GPU engines) - IDs indicate engine
    {"id": "parler-hi-v2", "engine": "parler", "language": "hi", "display_name": "Parler Hindi v2", "model_path": "", "supports_alignments": True},
    {"id": "parler-ta-v1", "engine": "parler", "language": "ta", "display_name": "Parler Tamil v1", "model_path": "", "supports_alignments": True},
]


def seed_default_voices():
    """Ensure default voice records exist in MongoDB. Idempotent."""
    # make sure MongoDB is initialized
    try:
        init_mongodb()
    except Exception:
        pass

    existing = {v.get("id") for v in list_voices()}
    for v in DEFAULT_VOICES:
        if v["id"] in existing:
            continue
        try:
            put_voice(v)
        except Exception:
            # ignore seed errors to avoid preventing app startup
            pass

    return list_voices()

