"""production hardening

Revision ID: 0003_prod_hardening
Revises: 0002_org_auth
Create Date: 2026-05-07 00:00:00
"""
from __future__ import annotations

from alembic import op


revision = "0003_prod_hardening"
down_revision = "0002_org_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE api_keys
            ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS rotated_from_api_key_id TEXT,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

        CREATE TABLE IF NOT EXISTS plans (
            plan_code TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            monthly_execution_limit INTEGER,
            cluster_limit INTEGER,
            namespace_limit INTEGER,
            retention_days INTEGER NOT NULL DEFAULT 365,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        INSERT INTO plans (plan_code, display_name, monthly_execution_limit, cluster_limit, namespace_limit)
        VALUES
            ('starter', 'Starter', 1000, 1, 5),
            ('business', 'Business', 100000, 25, 250),
            ('enterprise', 'Enterprise', NULL, NULL, NULL)
        ON CONFLICT (plan_code) DO NOTHING;

        CREATE TABLE IF NOT EXISTS execution_requests (
            execution_id TEXT PRIMARY KEY,
            receipt_id TEXT NOT NULL REFERENCES trust_receipts(receipt_id),
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
            namespace TEXT NOT NULL,
            workload_id TEXT NOT NULL,
            action TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            receipt_metadata JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            claimed_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            error_code TEXT,
            error_summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id BIGSERIAL PRIMARY KEY,
            org_id TEXT,
            cluster_id TEXT,
            actor_role TEXT NOT NULL,
            actor_org_id TEXT,
            actor_cluster_id TEXT,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            outcome TEXT NOT NULL,
            request_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS failed_auth_events (
            id BIGSERIAL PRIMARY KEY,
            token_hash TEXT,
            reason TEXT NOT NULL,
            request_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_api_keys_expires ON api_keys(expires_at);
        CREATE INDEX IF NOT EXISTS idx_execution_requests_operator_pending
            ON execution_requests(org_id, cluster_id, status, created_at);
        CREATE INDEX IF NOT EXISTS idx_execution_requests_receipt ON execution_requests(receipt_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_org_created ON audit_logs(org_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_failed_auth_created ON failed_auth_events(created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_failed_auth_created;
        DROP INDEX IF EXISTS idx_audit_logs_org_created;
        DROP INDEX IF EXISTS idx_execution_requests_receipt;
        DROP INDEX IF EXISTS idx_execution_requests_operator_pending;
        DROP INDEX IF EXISTS idx_api_keys_expires;
        DROP TABLE IF EXISTS failed_auth_events;
        DROP TABLE IF EXISTS audit_logs;
        DROP TABLE IF EXISTS execution_requests;
        DROP TABLE IF EXISTS plans;
        ALTER TABLE api_keys
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS rotated_from_api_key_id,
            DROP COLUMN IF EXISTS expires_at;
        """
    )
