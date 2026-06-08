from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "swgi-command-center"
    app_version: str = "0.1.0"
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8081")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_format: str = Field(default_factory=lambda: os.getenv("LOG_FORMAT", "json").lower())
    swgi_mode: str = Field(default_factory=lambda: os.getenv("SWGI_MODE", "production").strip().lower())
    org_id: str = Field(default_factory=lambda: os.getenv("SWGI_ORG_ID", "org-prod"))
    command_center_id: str = Field(default_factory=lambda: os.getenv("SWGI_COMMAND_CENTER_ID", "cc-prod-001"))
    command_center_url: str = Field(default_factory=lambda: os.getenv("COMMAND_CENTER_URL", "http://localhost:8081"))
    policy_path: str = Field(default_factory=lambda: os.getenv("POLICY_PATH", "./data/input/policy.json"))
    signing_key_path: str = Field(
        default_factory=lambda: os.getenv("SIGNING_KEY_PATH", "./data/input/signing_key_ed25519.pem")
    )
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    db_connect_timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))
    )
    run_db_migrations: bool = Field(
        default_factory=lambda: os.getenv("RUN_DB_MIGRATIONS", "true").lower() == "true"
    )
    rate_limit_per_minute: int = Field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")))
    session_ttl_hours: int = Field(default_factory=lambda: int(os.getenv("SESSION_TTL_HOURS", "8")))
    admin_api_token: str = Field(default_factory=lambda: os.getenv("ADMIN_API_TOKEN", ""))
    viewer_api_token: str = Field(default_factory=lambda: os.getenv("VIEWER_API_TOKEN", ""))
    api_key_hash_secret: str = Field(default_factory=lambda: os.getenv("API_KEY_HASH_SECRET", ""))
    metrics_enabled: bool = Field(default_factory=lambda: os.getenv("METRICS_ENABLED", "true").lower() == "true")

    def validate_runtime(self) -> None:
        if self.swgi_mode != "production":
            raise ValueError("swgi-command-center requires SWGI_MODE=production")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required; Command Center uses Postgres")
        if not self.admin_api_token or not self.viewer_api_token:
            raise ValueError("ADMIN_API_TOKEN and VIEWER_API_TOKEN are required")
        if not self.api_key_hash_secret:
            raise ValueError("API_KEY_HASH_SECRET is required for org-scoped API key hashing")
        if not Path(self.policy_path).exists():
            raise ValueError(f"POLICY_PATH not found: {self.policy_path}")
        if not Path(self.signing_key_path).exists():
            raise ValueError(f"SIGNING_KEY_PATH not found: {self.signing_key_path}")


settings = Settings()
