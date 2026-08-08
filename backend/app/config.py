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

    # Guest lifecycle. Keep GUEST_RETENTION_DAYS aligned with the token TTL above:
    # a shorter window would delete guests who still hold a valid token.
    GUEST_RETENTION_DAYS: int = 7
    # How stale last_active may get before an authenticated request rewrites it.
    # Purely a write-amplification guard — every request would otherwise be a write.
    LAST_ACTIVE_THROTTLE_MINUTES: int = 15
    
    # OAuth & AI Providers (Optional in dev)
    GOOGLE_CLIENT_ID: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "https://linguflow.vercel.app",
    ]
    CORS_ORIGIN_REGEX: str = r"https://linguflow-.*\.vercel\.app"

    # Cloudflare R2 Storage
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "linguflow-media"
    R2_ENDPOINT_URL: str = ""


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
        dev_fallbacks = {
            "lingu_dev_jwt_secret_key_change_in_production_99",
            "change_this_to_a_long_secure_random_string_in_production",
            "your_jwt_secret_key_here",
            "change-me",
            "secret",
        }
        # Read the resolved *field*, not the process env: `ENVIRONMENT` is
        # declared above `JWT_SECRET`, so pydantic-settings has already merged
        # process env over `.env` by now. `os.getenv` saw only the former, so a
        # deploy that declared production purely in `backend/.env` booted on the
        # committed dev secret below.
        env = (info.data.get("ENVIRONMENT") or "development").strip().lower()
        if env == "production" and (not secret or secret in dev_fallbacks):
            raise ValueError("JWT_SECRET environment variable MUST be explicitly set to a secure random key in production!")
        if not secret:
            return "lingu_dev_jwt_secret_key_change_in_production_99"
        return secret


@lru_cache()
def get_settings() -> Settings:
    return Settings()
