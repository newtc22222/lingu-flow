import os
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/linguflow"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security (MUST BE SET!)
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # OAuth & AI Providers (Optional in dev)
    GOOGLE_CLIENT_ID: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("JWT_SECRET", mode="after")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        secret = (v or "").strip()
        if not secret or secret == "change_this_to_a_long_secure_random_string_in_production":
            # For development convenience if no secret provided, generate fallback with warning
            env = os.getenv("ENVIRONMENT", "development")
            if env == "production":
                raise ValueError("JWT_SECRET environment variable MUST be explicitly set in production!")
            return "lingu_dev_jwt_secret_key_change_in_production_99"
        return secret


@lru_cache()
def get_settings() -> Settings:
    return Settings()
