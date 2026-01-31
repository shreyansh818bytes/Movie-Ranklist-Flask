# Central environment variables configuration
import os
from enum import Enum


def _to_bool(value: str) -> bool:
    return value.lower() in ["true", "1", "yes", "y"]


class EnvVariable(Enum):
    """Enum containing all environment variable names used in the app."""

    # Server configuration.
    PORT = int(os.environ["PORT"])
    FLASK_DEBUG = _to_bool(os.environ.get("FLASK_DEBUG", "false"))

    # Database.
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///movieapp.db")

    # Security.
    SECRET_KEY = os.environ["SECRET_KEY"]

    # API Keys.
    TMDB_API_KEY = os.environ["TMDB_API_KEY"]
    IMDB_API_KEY = os.environ["IMDB_API_KEY"]
