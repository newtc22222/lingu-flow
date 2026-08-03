import os
import pytest
from app.config import Settings, get_settings


def test_default_settings():
    """Test default configuration settings."""
    settings = get_settings()
    assert settings.PORT == 8000
    assert settings.ENVIRONMENT == "development"
    assert settings.JWT_ALGORITHM == "HS256"


def test_jwt_secret_validation_in_production():
    """Test that JWT_SECRET raises ValueError in production if empty or default placeholder."""
    os.environ["ENVIRONMENT"] = "production"
    try:
        with pytest.raises(ValueError, match="JWT_SECRET environment variable MUST be explicitly set"):
            Settings(JWT_SECRET="")
    finally:
        os.environ["ENVIRONMENT"] = "development"


def test_custom_jwt_secret():
    """Test setting a custom secure JWT secret."""
    custom_secret = "super_secure_custom_secret_key_123456789"
    settings = Settings(JWT_SECRET=custom_secret)
    assert settings.JWT_SECRET == custom_secret
