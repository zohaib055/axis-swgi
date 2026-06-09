from __future__ import annotations

from typing import Any

from .models import ExecutionIntentRequest


def metadata_receipt(
    base_receipt: dict[str, Any],
    req: ExecutionIntentRequest,
    latency_ms: float,
    *,
    command_center_id: str,
) -> dict[str, Any]:
    expires_at = req.expiry_or_default()
    return {
        "receipt_id": base_receipt["receipt_id"],
        "schema_version": base_receipt.get("schema_version"),
        "org_id": req.org_id,
        "cluster_id": req.cluster_id,
        "namespace": req.namespace,
        "workload_id": req.workload_id,
        "action": req.action,
        "decision": base_receipt["result"],
        "reason": base_receipt.get("reason", ""),
        "policy_id": base_receipt["policy_id"],
        "payload_hash": base_receipt["payload_hash"],
        "authority_token_hash": base_receipt["authority_token_hash"],
        "signature": base_receipt["signature"],
        "signature_algorithm": "ed25519",
        "integrity_classification": base_receipt.get("integrity_classification"),
        "created_at": base_receipt["timestamp"],
        "expires_at": expires_at.isoformat(),
        "latency_ms": round(latency_ms, 4),
        "identity": req.identity,
        "command_center_id": command_center_id,
        "runtime": "kubernetes",
        "attestation": req.attestation,
        "marketplace": req.marketplace,
    }
