"""sales readiness auth settings

Revision ID: 0005_sales_readiness
Revises: 0004_user_auth
Create Date: 2026-06-09 00:00:00
"""
from __future__ import annotations

from alembic import op


revision = "0005_sales_readiness"
down_revision = "0004_user_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS user_action_tokens (
            token_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(user_id),
            token_hash TEXT NOT NULL UNIQUE,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            CONSTRAINT user_action_tokens_purpose_check CHECK (purpose IN ('invite', 'password_reset')),
            CONSTRAINT user_action_tokens_status_check CHECK (status IN ('active', 'used', 'revoked'))
        );

        CREATE INDEX IF NOT EXISTS idx_user_action_tokens_hash ON user_action_tokens(token_hash);
        CREATE INDEX IF NOT EXISTS idx_user_action_tokens_user ON user_action_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_action_tokens_expires ON user_action_tokens(expires_at);

        CREATE TABLE IF NOT EXISTS control_plane_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        INSERT INTO control_plane_settings (setting_key, setting_value)
        VALUES
            ('security', '{"receipt_retention_days":365,"operator_event_retention_days":90,"audit_log_retention_days":2555,"intent_rate_limit_per_second":500,"operator_poll_limit_per_second":2000,"org_admin_requests_per_minute":600,"burst_window_seconds":10}'::jsonb),
            ('onboarding', '{"support_email":"support@swgi.io","docs_url":"https://docs.swgi.io"}'::jsonb)
        ON CONFLICT (setting_key) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.get_bind().exec_driver_sql(
        """
        DROP TABLE IF EXISTS control_plane_settings;
        DROP INDEX IF EXISTS idx_user_action_tokens_expires;
        DROP INDEX IF EXISTS idx_user_action_tokens_user;
        DROP INDEX IF EXISTS idx_user_action_tokens_hash;
        DROP TABLE IF EXISTS user_action_tokens;
        """
    )
