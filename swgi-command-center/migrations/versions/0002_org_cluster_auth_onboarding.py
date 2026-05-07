"""org cluster auth onboarding

Revision ID: 0002_org_auth
Revises: 0001_initial_schema
Create Date: 2026-05-07 00:00:00
"""
from __future__ import annotations

from alembic import op


revision = "0002_org_auth"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE organizations
            ADD COLUMN IF NOT EXISTS display_name TEXT,
            ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active',
            ADD COLUMN IF NOT EXISTS plan_code TEXT NOT NULL DEFAULT 'starter',
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

        ALTER TABLE clusters
            ADD COLUMN IF NOT EXISTS display_name TEXT,
            ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS install_token_hash TEXT,
            ADD COLUMN IF NOT EXISTS heartbeat_namespace TEXT,
            ADD COLUMN IF NOT EXISTS health TEXT,
            ADD COLUMN IF NOT EXISTS operator_version TEXT,
            ADD COLUMN IF NOT EXISTS last_heartbeat_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

        CREATE TABLE IF NOT EXISTS api_keys (
            api_key_id TEXT PRIMARY KEY,
            org_id TEXT REFERENCES organizations(org_id),
            cluster_id TEXT REFERENCES clusters(cluster_id),
            key_name TEXT NOT NULL,
            role TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ
        );

        ALTER TABLE operator_events
            ADD COLUMN IF NOT EXISTS org_id TEXT REFERENCES organizations(org_id);

        CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(org_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_cluster ON api_keys(cluster_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_token_hash ON api_keys(token_hash);
        CREATE INDEX IF NOT EXISTS idx_operator_events_org ON operator_events(org_id);
        CREATE INDEX IF NOT EXISTS idx_clusters_org_status ON clusters(org_id, status);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_clusters_org_status;
        DROP INDEX IF EXISTS idx_operator_events_org;
        DROP INDEX IF EXISTS idx_api_keys_token_hash;
        DROP INDEX IF EXISTS idx_api_keys_cluster;
        DROP INDEX IF EXISTS idx_api_keys_org;
        DROP TABLE IF EXISTS api_keys;
        ALTER TABLE operator_events DROP COLUMN IF EXISTS org_id;
        ALTER TABLE clusters
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS last_heartbeat_at,
            DROP COLUMN IF EXISTS operator_version,
            DROP COLUMN IF EXISTS health,
            DROP COLUMN IF EXISTS heartbeat_namespace,
            DROP COLUMN IF EXISTS install_token_hash,
            DROP COLUMN IF EXISTS status,
            DROP COLUMN IF EXISTS display_name;
        ALTER TABLE organizations
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS plan_code,
            DROP COLUMN IF EXISTS status,
            DROP COLUMN IF EXISTS display_name;
        """
    )
