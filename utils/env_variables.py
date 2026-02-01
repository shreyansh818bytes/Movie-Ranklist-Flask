# Central environment variables configuration
import os
from enum import Enum


def _to_bool(value: str) -> bool:
    return value.lower() in ["true", "1", "yes", "y"]


def _get_env(key: str, default: str = None, required: bool = False) -> str:
    """Get environment variable with optional default."""
    value = os.environ.get(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


class EnvVariable(Enum):
    """Enum containing all environment variable names used in the app."""

    # Server configuration - defaults for testing
    PORT = int(_get_env("PORT", "5000"))
    FLASK_DEBUG = _to_bool(_get_env("FLASK_DEBUG", "false"))

    # Database - defaults to SQLite for testing
    DATABASE_URL = _get_env("DATABASE_URL", "sqlite:///movieapp.db")

    # Security - default for testing (should be overridden in production)
    SECRET_KEY = _get_env("SECRET_KEY", "test-secret-key-do-not-use-in-production")

    # API Keys - defaults to empty for testing (mocked in tests)
    TMDB_API_KEY = _get_env("TMDB_API_KEY", "")
    IMDB_API_KEY = _get_env("IMDB_API_KEY", "")
