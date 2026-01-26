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
    
    # Cloudinary settings (for file storage)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Legacy AWS settings (kept for backward compatibility)
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""
    AWS_REGION: str = "ap-south-1"
    DYNAMODB_TABLE_TEMP_AUDIO: str = "tts_temp_audio"
    
    # Cognito settings
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    
    # Database settings
    database_url: str = "sqlite:///./dev.db"
    
    # DynamoDB settings
    dynamodb_region: str = "ap-south-1"
    dynamodb_table_users: str = "users"
    dynamodb_table_name: str = "jobs"
    
    # AWS credentials
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    
    # Redis settings
    redis_url: str = "redis://redis:6379/0"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
