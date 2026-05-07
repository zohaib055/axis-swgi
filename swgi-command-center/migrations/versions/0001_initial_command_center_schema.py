"""initial command center schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-05-07 00:00:00
"""
from __future__ import annotations

from alembic import op


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            org_id TEXT PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS clusters (
            cluster_id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            runtime TEXT NOT NULL DEFAULT 'kubernetes',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS namespaces (
            org_id TEXT NOT NULL,
            cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
            namespace TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (cluster_id, namespace)
        );

        CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            version TEXT,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS trust_receipts (
            receipt_id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            cluster_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            workload_id TEXT NOT NULL,
            action TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT,
            policy_id TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            authority_token_hash TEXT NOT NULL,
            signature TEXT NOT NULL,
            signature_algorithm TEXT NOT NULL DEFAULT 'ed25519',
            integrity_classification TEXT,
            created_at TIMESTAMPTZ NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            latency_ms DOUBLE PRECISION,
            receipt_metadata JSONB NOT NULL
        );

        CREATE TABLE IF NOT EXISTS usage_metering (
            id BIGSERIAL PRIMARY KEY,
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            cluster_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            receipt_id TEXT NOT NULL REFERENCES trust_receipts(receipt_id),
            decision TEXT NOT NULL,
            billable BOOLEAN NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS operator_events (
            id BIGSERIAL PRIMARY KEY,
            receipt_id TEXT NOT NULL,
            cluster_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            workload_id TEXT NOT NULL,
            enforcement_status TEXT NOT NULL,
            error_code TEXT,
            error_summary TEXT,
            operator_version TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS billing_periods (
            id BIGSERIAL PRIMARY KEY,
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            period_start TIMESTAMPTZ NOT NULL,
            period_end TIMESTAMPTZ NOT NULL,
            plan_code TEXT NOT NULL,
            execution_limit INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_trust_receipts_org_created ON trust_receipts(org_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_trust_receipts_cluster ON trust_receipts(cluster_id);
        CREATE INDEX IF NOT EXISTS idx_trust_receipts_namespace ON trust_receipts(namespace);
        CREATE INDEX IF NOT EXISTS idx_trust_receipts_decision ON trust_receipts(decision);
        CREATE INDEX IF NOT EXISTS idx_trust_receipts_policy ON trust_receipts(policy_id);
        CREATE INDEX IF NOT EXISTS idx_operator_events_receipt ON operator_events(receipt_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS billing_periods;
        DROP TABLE IF EXISTS operator_events;
        DROP TABLE IF EXISTS usage_metering;
        DROP TABLE IF EXISTS trust_receipts;
        DROP TABLE IF EXISTS policies;
        DROP TABLE IF EXISTS namespaces;
        DROP TABLE IF EXISTS clusters;
        DROP TABLE IF EXISTS organizations;
        """
    )
