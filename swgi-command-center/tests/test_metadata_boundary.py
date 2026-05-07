from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import ExecutionIntentRequest
from app.receipts import metadata_receipt


def test_execution_intent_rejects_sensitive_metadata_keys() -> None:
    with pytest.raises(ValueError):
        ExecutionIntentRequest(
            org_id="org-1",
            cluster_id="cluster-1",
            namespace="default",
            workload_id="workload-1",
            action="kubernetes.apply",
            intent="deploy workload",
            requested_metadata={"secret": "do-not-store"},
        )


def test_metadata_receipt_does_not_store_raw_request_payload() -> None:
    req = ExecutionIntentRequest(
        org_id="org-1",
        cluster_id="cluster-1",
        namespace="default",
        workload_id="workload-1",
        action="kubernetes.apply",
        intent="deploy workload",
        identity="platform-admin",
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

    assert "request_payload" not in receipt
    assert "policy_context" not in receipt
    assert "requested_metadata" not in receipt
    assert receipt["cluster_id"] == "cluster-1"
    assert receipt["namespace"] == "default"
