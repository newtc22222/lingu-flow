import pytest
from app.config import Settings, get_settings


def test_default_settings():
    """Test default configuration settings."""
    settings = get_settings()
    assert settings.PORT == 8000
    assert settings.ENVIRONMENT == "development"
    assert settings.JWT_ALGORITHM == "HS256"


def test_jwt_secret_validation_in_production(monkeypatch):
    """Test that JWT_SECRET raises ValueError in production if empty or default placeholder."""
    # monkeypatch, not a manual set/restore: restoring by writing
    # ENVIRONMENT=development leaves a process-env value behind, and process env
    # outranks any .env file — which silently neutered the tests below.
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValueError, match="JWT_SECRET environment variable MUST be explicitly set"):
        Settings(JWT_SECRET="")


def test_custom_jwt_secret():
    """Test setting a custom secure JWT secret."""
    custom_secret = "super_secure_custom_secret_key_123456789"
    settings = Settings(JWT_SECRET=custom_secret)
    assert settings.JWT_SECRET == custom_secret


# ─── Production guard, driven by a .env file rather than process env ──────────
# `ENVIRONMENT` is a Settings *field*: a deploy can declare production purely in
# `backend/.env`, without ever exporting it. The guard used to read
# `os.getenv("ENVIRONMENT")`, so that deploy booted on the committed dev secret.

DEV_FALLBACK_SECRET = "lingu_dev_jwt_secret_key_change_in_production_99"


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    """Write a throwaway .env and guarantee process env cannot outrank it."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    def _write(body: str) -> str:
        path = tmp_path / ".env"
        path.write_text(body, encoding="utf-8")
        return str(path)

    return _write


def test_production_env_file_rejects_default_secret(env_file):
    """Production declared only in .env must still reject the committed secret."""
    path = env_file(f"ENVIRONMENT=production\nJWT_SECRET={DEV_FALLBACK_SECRET}\n")
    with pytest.raises(ValueError, match="JWT_SECRET environment variable MUST be explicitly set"):
        Settings(_env_file=path)


def test_production_env_file_requires_secret(env_file):
    """Production declared only in .env must reject a missing secret."""
    path = env_file("ENVIRONMENT=production\n")
    with pytest.raises(ValueError, match="JWT_SECRET environment variable MUST be explicitly set"):
        Settings(_env_file=path)


def test_production_env_file_is_case_insensitive(env_file):
    """`ENVIRONMENT=Production` is the same environment, so the guard must fire."""
    path = env_file(f"ENVIRONMENT=Production\nJWT_SECRET={DEV_FALLBACK_SECRET}\n")
    with pytest.raises(ValueError, match="JWT_SECRET environment variable MUST be explicitly set"):
        Settings(_env_file=path)


def test_production_env_file_accepts_strong_secret(env_file):
    """A real secret boots production: the guard rejects weakness, not production."""
    strong_secret = "j8Qw2fN4tR7vZ1cL5mP9sX3bK6hY0dG2aE4uT8nW1rV5"
    path = env_file(f"ENVIRONMENT=production\nJWT_SECRET={strong_secret}\n")
    settings = Settings(_env_file=path)
    assert settings.ENVIRONMENT == "production"
    assert settings.JWT_SECRET == strong_secret


def test_development_env_file_keeps_default_secret(env_file):
    """Local dev keeps working with no secret configured at all."""
    path = env_file("ENVIRONMENT=development\n")
    settings = Settings(_env_file=path)
    assert settings.JWT_SECRET == DEV_FALLBACK_SECRET
