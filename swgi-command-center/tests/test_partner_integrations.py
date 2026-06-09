from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import ExecutionIntentRequest
from app.receipts import metadata_receipt


def test_intel_tdx_attestation_metadata_is_preserved_in_receipt() -> None:
    req = ExecutionIntentRequest(
        org_id="org-1",
        cluster_id="cluster-1",
        namespace="default",
        workload_id="workload-1",
        action="kubernetes.apply",
        intent="deploy confidential workload",
        attestation={
            "provider": "intel-tdx",
            "verification_result": "verified",
            "quote_hash": "sha256:abc123",
            "runtime_class": "kata-tdx",
        },
        expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    receipt = metadata_receipt(
        {
            "receipt_id": "receipt-1",
            "schema_version": "1.0",
            "result": "ALLOW",
            "reason": "authorized",
            "policy_id": "policy-1",
            "payload_hash": "hash",
            "authority_token_hash": "authority-hash",
            "signature": "signature",
            "integrity_classification": "HIGH",
            "timestamp": "2026-01-01T00:00:00+00:00",
        },
        req,
        1.25,
        command_center_id="cc-test",
    )

    assert receipt["attestation"]["provider"] == "intel-tdx"
    assert receipt["attestation"]["verification_result"] == "verified"
    assert receipt["attestation"]["quote_hash"] == "sha256:abc123"


def test_verified_intel_attestation_requires_evidence_reference() -> None:
    with pytest.raises(ValueError):
        ExecutionIntentRequest(
            org_id="org-1",
            cluster_id="cluster-1",
            namespace="default",
            workload_id="workload-1",
            action="kubernetes.apply",
            intent="deploy confidential workload",
            attestation={
                "provider": "intel-tdx",
                "verification_result": "verified",
            },
        )


def test_google_marketplace_metadata_accepts_usage_reporting_id() -> None:
    req = ExecutionIntentRequest(
        org_id="org-1",
        cluster_id="cluster-1",
        namespace="default",
        workload_id="workload-1",
        action="kubernetes.apply",
        intent="deploy workload",
        marketplace={
            "provider": "google-cloud-marketplace",
            "usage_reporting_id": "usage-reporting-id",
        },
    )

    assert req.marketplace["usage_reporting_id"] == "usage-reporting-id"


def test_marketplace_metadata_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        ExecutionIntentRequest(
            org_id="org-1",
            cluster_id="cluster-1",
            namespace="default",
            workload_id="workload-1",
            action="kubernetes.apply",
            intent="deploy workload",
            marketplace={"provider": "unknown"},
        )
