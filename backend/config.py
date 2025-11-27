from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "PocketLLM"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "sqlite:///./pocketllm.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/models/model.gguf")

    MODEL_N_CTX: int = int(os.getenv("MODEL_N_CTX", 4096))
    MODEL_N_THREADS: int = int(os.getenv("MODEL_N_THREADS", 4))
    MODEL_N_GPU_LAYERS: int = int(os.getenv("MODEL_N_GPU_LAYERS", 0))
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", 0.0))
    MODEL_TOP_P: float = float(os.getenv("MODEL_TOP_P", 1.0))
    MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", 1024))
    MODEL_N_BATCH: int = int(os.getenv("MODEL_N_BATCH", 128))

    # Cache settings
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    ENABLE_CACHE: bool = True

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_PERIOD: int = 60  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
