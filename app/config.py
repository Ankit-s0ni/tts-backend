"""Config using Pydantic v2 settings."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    ENV: str = "development"
    PIPER_URL: str = "http://piper-service:5000/"  # Keep for /tts/sync endpoint (backward compat)
    MODELS_DIR: str = "/models"  # Base directory for ONNX model files
    MAX_CACHED_VOICES: int = 5  # Maximum voices to keep in VoiceManager cache
    
    # MongoDB settings
    MONGODB_URI: str = "mongodb+srv://voicetexta:voicetexta@cluster0.dvq4rui.mongodb.net/?appName=Cluster0"
    MONGODB_DB_NAME: str = "tts_production"
    
    # Legacy AWS settings (kept for backward compatibility)
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""
    AWS_REGION: str = "ap-south-1"
    DYNAMODB_TABLE_TEMP_AUDIO: str = "tts_temp_audio"

    model_config = {
        "env_file": ".env"
    }


settings = Settings()
