"""user session auth

Revision ID: 0004_user_auth
Revises: 0003_prod_hardening
Create Date: 2026-06-09 00:00:00
"""
from __future__ import annotations

from alembic import op


revision = "0004_user_auth"
down_revision = "0003_prod_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            display_name TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            org_id TEXT REFERENCES organizations(org_id),
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_login_at TIMESTAMPTZ,
            CONSTRAINT users_role_check CHECK (
                role IN ('platform_admin', 'platform_viewer', 'org_admin', 'org_viewer', 'operator')
            ),
            CONSTRAINT users_status_check CHECK (status IN ('active', 'disabled'))
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(user_id),
            token_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            last_seen_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            CONSTRAINT user_sessions_status_check CHECK (status IN ('active', 'revoked'))
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_org ON users(org_id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_user_sessions_expires;
        DROP INDEX IF EXISTS idx_user_sessions_user;
        DROP INDEX IF EXISTS idx_user_sessions_token_hash;
        DROP INDEX IF EXISTS idx_users_org;
        DROP INDEX IF EXISTS idx_users_email;
        DROP TABLE IF EXISTS user_sessions;
        DROP TABLE IF EXISTS users;
        """
    )
