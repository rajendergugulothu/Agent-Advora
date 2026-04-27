"""
Application configuration via Pydantic Settings.
All values are loaded from environment variables.
Fails fast at startup if any required value is missing.
"""

import os
import json
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ───────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # ── API ───────────────────────────────────────────────────
    api_v1_prefix: str = "/api/v1"
    allowed_origins: str | list[str] = Field(default=["http://localhost:3000"])

    # ── Supabase ──────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str          # backend uses service role to bypass RLS
    database_url: str                        # postgres+asyncpg://...

    # ── Security ──────────────────────────────────────────────
    # 32-byte hex key used to encrypt/decrypt stored tokens.
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    encryption_key: str = Field(min_length=64)

    # ── OpenAI ────────────────────────────────────────────────
    openai_api_key: str
    openai_text_model: str = "gpt-4o-mini"
    openai_image_model: str = "dall-e-3"

    # ── Cloudinary ────────────────────────────────────────────
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    cloudinary_upload_preset: str = "advora_posts"

    # ── WhatsApp ──────────────────────────────────────────────
    # Platform-level phone number used to send drafts to all users.
    whatsapp_phone_number_id: str
    whatsapp_access_token: str
    whatsapp_app_secret: str
    whatsapp_webhook_verify_token: str

    # ── Meta / Instagram OAuth ────────────────────────────────
    meta_app_id: str
    meta_app_secret: str
    meta_oauth_redirect_uri: AnyHttpUrl       # e.g. https://yourdomain.com/api/v1/instagram/callback

    # ── Frontend ──────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"

    # ── Sentry ────────────────────────────────────────────────
    sentry_dsn: str | None = None

    # ── Rate limiting ─────────────────────────────────────────
    rate_limit_per_minute: int = 60
    enable_scheduler: bool = True

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: object) -> object:
        if isinstance(v, str):
            value = v.strip().lower()
            if value in {"release", "production", "prod", "staging"}:
                return False
            if value in {"development", "dev"}:
                return True
        return v

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            value = v.strip()
            if value.startswith("[") and value.endswith("]"):
                parsed = json.loads(value)
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def should_start_scheduler(self) -> bool:
        return self.enable_scheduler and os.getenv("VERCEL") != "1"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance. Import and call this anywhere:
        from app.core.config import get_settings
        settings = get_settings()
    """
    return Settings()
