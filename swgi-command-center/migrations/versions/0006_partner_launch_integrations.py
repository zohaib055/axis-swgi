"""partner launch integrations

Revision ID: 0006_partner_launch_integrations
Revises: 0005_sales_readiness
Create Date: 2026-06-09 00:00:00
"""
from __future__ import annotations

from alembic import op


revision = "0006_partner_launch_integrations"
down_revision = "0005_sales_readiness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS marketplace_usage_events (
            event_id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL REFERENCES organizations(org_id),
            cluster_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            receipt_id TEXT NOT NULL REFERENCES trust_receipts(receipt_id),
            provider TEXT NOT NULL DEFAULT 'google-cloud-marketplace',
            metric_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit TEXT NOT NULL DEFAULT '1',
            usage_time TIMESTAMPTZ NOT NULL,
            usage_reporting_id TEXT,
            labels JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            report_attempts INTEGER NOT NULL DEFAULT 0,
            last_reported_at TIMESTAMPTZ,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT marketplace_usage_events_status_check CHECK (status IN ('pending', 'reported', 'failed', 'skipped'))
        );

        CREATE INDEX IF NOT EXISTS idx_marketplace_usage_events_provider_status
            ON marketplace_usage_events(provider, status, usage_time);
        CREATE INDEX IF NOT EXISTS idx_marketplace_usage_events_org
            ON marketplace_usage_events(org_id, usage_time);
        CREATE INDEX IF NOT EXISTS idx_marketplace_usage_events_receipt
            ON marketplace_usage_events(receipt_id);

        INSERT INTO control_plane_settings (setting_key, setting_value)
        VALUES
            ('marketplace', '{"google_cloud_marketplace":{"enabled":false,"service_name":"","metric_name":"swgi_governed_execution","reporting_mode":"external_reporter"}}'::jsonb),
            ('intel_partner', '{"tdx_attestation":{"enabled":false,"required_for_confidential_policies":false,"accepted_providers":["intel-tdx","intel-trust-authority"]}}'::jsonb)
        ON CONFLICT (setting_key) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.get_bind().exec_driver_sql(
        """
        DROP INDEX IF EXISTS idx_marketplace_usage_events_receipt;
        DROP INDEX IF EXISTS idx_marketplace_usage_events_org;
        DROP INDEX IF EXISTS idx_marketplace_usage_events_provider_status;
        DROP TABLE IF EXISTS marketplace_usage_events;
        DELETE FROM control_plane_settings WHERE setting_key IN ('marketplace', 'intel_partner');
        """
    )
