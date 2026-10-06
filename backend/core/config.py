import os
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

class Settings(BaseSettings):
    SPOTIFY_CLIENT_ID: str = "your_spotify_client_id"
    SPOTIFY_CLIENT_SECRET: str = "your_spotify_client_secret"
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/api/callback"
    GEMINI_API_KEY: str = "your_gemini_api_key"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_SECONDS: float = 6.0
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if os.path.exists(_ENV_FILE) else None,
        extra="ignore"
    )

settings = Settings()

