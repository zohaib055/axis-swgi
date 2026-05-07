from __future__ import annotations

from pathlib import Path
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "swgi-openshift"
    app_version: str = "0.1.0"
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_format: str = Field(default_factory=lambda: os.getenv("LOG_FORMAT", "json").lower())
    swgi_mode: str = Field(default_factory=lambda: os.getenv("SWGI_MODE", "production").strip().lower())
    org_id: str = Field(default_factory=lambda: os.getenv("SWGI_ORG_ID", "org-prod"))
    node_id: str = Field(default_factory=lambda: os.getenv("SWGI_NODE_ID", "fen-ocp-001"))
    policy_path: str = Field(default_factory=lambda: os.getenv("POLICY_PATH", "data/input/policy.json"))
    signing_key_path: str = Field(
        default_factory=lambda: os.getenv("SIGNING_KEY_PATH", "/tmp/secrets/signing_key_ed25519.pem")
    )
    receipt_store_backend: str = Field(default_factory=lambda: os.getenv("RECEIPT_STORE_BACKEND", "sqlite").lower())
    receipt_db_path: str = Field(default_factory=lambda: os.getenv("RECEIPT_DB_PATH", "/tmp/swgi/receipts.db"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    db_connect_timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))
    )
    run_db_migrations: bool = Field(
        default_factory=lambda: os.getenv("RUN_DB_MIGRATIONS", "true").lower() == "true"
    )
    admin_api_token: str = Field(default_factory=lambda: os.getenv("ADMIN_API_TOKEN", ""))
    viewer_api_token: str = Field(default_factory=lambda: os.getenv("VIEWER_API_TOKEN", ""))
    tls_enabled: bool = Field(default_factory=lambda: os.getenv("TLS_ENABLED", "false").lower() == "true")
    metrics_enabled: bool = Field(default_factory=lambda: os.getenv("METRICS_ENABLED", "true").lower() == "true")

    def validate_runtime(self) -> None:
        if self.swgi_mode != "production":
            raise ValueError("swgi-openshift requires SWGI_MODE=production")
        if self.receipt_store_backend not in {"sqlite", "postgres"}:
            raise ValueError("RECEIPT_STORE_BACKEND must be sqlite or postgres")
        if self.receipt_store_backend == "sqlite" and not self.receipt_db_path:
            raise ValueError("RECEIPT_DB_PATH is required when RECEIPT_STORE_BACKEND=sqlite")
        if self.receipt_store_backend == "postgres" and not self.database_url:
            raise ValueError("DATABASE_URL is required when RECEIPT_STORE_BACKEND=postgres")
        if not self.admin_api_token or not self.viewer_api_token:
            raise ValueError("ADMIN_API_TOKEN and VIEWER_API_TOKEN are required")
        if not Path(self.policy_path).exists():
            raise ValueError(f"POLICY_PATH not found: {self.policy_path}")
        if not Path(self.signing_key_path).exists():
            raise ValueError(f"SIGNING_KEY_PATH not found: {self.signing_key_path}")


settings = Settings()
