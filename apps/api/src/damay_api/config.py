"""Typed application settings.

All env vars are surfaced as a single ``Settings`` instance via :func:`get_settings`.
The settings object is cached for the lifetime of the process; tests override via
``Settings.model_construct`` or by setting env vars before import.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide settings loaded from env / .env.local."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    node_env: Literal["development", "test", "staging", "production"] = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    version: str = "0.1.0"

    # --- Supabase ---
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_db_url: str = ""
    supabase_jwt_secret: str = ""

    # --- Stellar ---
    stellar_network: Literal["testnet", "public"] = "testnet"
    stellar_horizon_url: str = "https://horizon-testnet.stellar.org"
    stellar_soroban_rpc_url: str = "https://soroban-testnet.stellar.org"
    stellar_issuer_secret: str = ""
    reputation_contract_id: str = ""
    paluwagan_contract_id: str = ""

    # --- Twilio ---
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    twilio_webhook_validation: bool = True

    # --- Observability ---
    sentry_dsn: str = ""
    log_level: str = "info"

    # --- Security ---
    jwt_secret: str = ""
    webhook_signing_secret: str = ""

    # --- Feature flags ---
    feature_demo_mode: bool = True
    feature_real_payments: bool = False

    # --- Worker tunables ---
    stellar_worker_interval_seconds: int = Field(default=2, ge=1)
    payout_cron_interval_seconds: int = Field(default=60, ge=10)

    # --- Mock detection ---
    @property
    def stellar_mock_mode(self) -> bool:
        """True when no live contract IDs are configured."""
        return not (self.reputation_contract_id and self.paluwagan_contract_id)

    @property
    def supabase_mock_mode(self) -> bool:
        """True when Supabase isn't configured. Tests rely on this."""
        return not (self.supabase_url and self.supabase_service_role_key)

    @property
    def twilio_mock_mode(self) -> bool:
        return not (self.twilio_account_sid and self.twilio_auth_token)

    @property
    def is_production(self) -> bool:
        return self.node_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached :class:`Settings` instance."""
    return Settings()
