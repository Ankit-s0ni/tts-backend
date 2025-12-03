"""Config that is compatible with pydantic v1 and v2 environments.

We avoid importing newer-only symbols to keep the code runnable regardless of
the host pydantic version. PIPER_URL is stored as a string.
"""
try:
    # pydantic v1
    from pydantic import BaseSettings
except Exception:
    # pydantic v2 separates settings into pydantic-settings
    from pydantic_settings import BaseSettings  # type: ignore


class Settings(BaseSettings):
    ENV: str = "development"
    PIPER_URL: str = "http://piper-service:5000/"  # Keep for /tts/sync endpoint (backward compat)
    MODELS_DIR: str = "/models"  # Base directory for ONNX model files
    MAX_CACHED_VOICES: int = 5  # Maximum voices to keep in VoiceManager cache
    # placeholders for future config
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
