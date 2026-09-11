"""
Centralized app configuration, loaded from environment variables (.env).

Every setting the rest of the app needs lives here so nothing reads
`os.environ` directly elsewhere — keeps config traceable to one file
(SDD §5: app/core/config.py).
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "HireLens AI"
    api_v1_prefix: str = "/api/v1"
    debug: bool = True

    # --- Database ---
    database_url: str = "postgresql://postgres:password@localhost:5432/hirelens"

    # --- Supabase ---
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_storage_bucket: str = "candidate-documents"

    # --- Auth / JWT ---
    jwt_secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15

    # --- Generative AI ---
    llm_provider: Literal["gemini", "openai"] = "gemini"
    google_api_key: str = ""
    openai_api_key: str = ""
    llm_model_name: str = "gemini-3.5-flash"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Public intake bridge (Google Form -> Apps Script -> this API) ---
    # Static shared-secret, not a JWT — the caller is a script, not a logged-in
    # user. Empty by default so the endpoint 503s until deliberately configured.
    public_apply_api_key: str = ""

    # --- Frontend base URL (OAuth redirects land the browser back here) ---
    frontend_url: str = "http://localhost:3000"

    # --- Google Calendar integration (interview scheduling) ---
    # From a Google Cloud project's OAuth client (Web application type) —
    # see app/modules/scheduling/google_client.py's docstring. Empty by
    # default so /integrations/google/* 503s until configured, same
    # pattern as public_apply_api_key above.
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    # Must exactly match a redirect URI registered on that OAuth client,
    # and point at this backend's own /integrations/google/callback route.
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/integrations/google/callback"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so Settings() is only parsed once per process."""
    return Settings()
