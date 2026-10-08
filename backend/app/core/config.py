"""
Privacy Eye — Application Configuration
Uses pydantic-settings for typed, validated environment variable loading.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union, Any
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production-must-be-32-chars"
    APP_VERSION: str = "1.0.0-mvp"
    APP_DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./privacyeye.db"
    DATABASE_URL_SYNC: str = "sqlite:///./privacyeye.db"

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret-32-chars-min"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini AI Agent
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # File Limits
    MAX_IMAGE_SIZE_MB: int = 20
    MAX_VIDEO_SIZE_MB: int = 500
    MAX_AUDIO_SIZE_MB: int = 50
    TEMP_UPLOAD_DIR: str = "./tmp/uploads"
    TEMP_RETENTION_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            clean = v.strip()
            if clean.startswith("[") and clean.endswith("]"):
                import json
                try:
                    return json.loads(clean)
                except Exception:
                    pass
            return [i.strip() for i in clean.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["http://localhost:3000", "http://localhost:3001"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_UPLOADS_PER_HOUR: int = 20

    # ML & Model Storage (Hugging Face Hub)
    ML_MODELS_DIR: str = "app/ml/weights"
    ML_DEVICE: str = "cpu"
    MODEL_REPOSITORY: str = "privacy-eye/privacy-eye-models"
    MODEL_REVISION: str = "main"
    MODEL_CACHE_DIR: str = "./models_cache"
    HF_TOKEN: str = ""
    AUTO_DOWNLOAD_MODELS: bool = True

    @property
    def max_image_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    @property
    def max_video_bytes(self) -> int:
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024

    @property
    def max_audio_bytes(self) -> int:
        return self.MAX_AUDIO_SIZE_MB * 1024 * 1024

    def ensure_temp_dir(self) -> None:
        os.makedirs(self.TEMP_UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.MODEL_CACHE_DIR, exist_ok=True)


settings = Settings()
settings.ensure_temp_dir()
