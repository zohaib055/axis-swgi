from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


Decision = Literal["ALLOW", "DENY", "MODIFY"]


class ExecutionIntentRequest(BaseModel):
    org_id: str = Field(..., min_length=1)
    cluster_id: str = Field(..., min_length=1)
    namespace: str = Field(..., min_length=1)
    workload_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    intent: str = Field(..., min_length=1)
    identity: str = Field(default="unknown")
    authority: dict[str, Any] = Field(default_factory=dict)
    policy_context: dict[str, Any] = Field(default_factory=dict)
    requested_metadata: dict[str, Any] = Field(default_factory=dict)
    attestation: dict[str, Any] = Field(default_factory=dict)
    marketplace: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None

    @field_validator("authority", "policy_context", "requested_metadata", "attestation", "marketplace")
    @classmethod
    def reject_sensitive_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        blocked = {"secret", "password", "token", "api_key", "apikey", "authorization", "env", "logs", "payload"}
        found = blocked.intersection({key.lower() for key in value})
        if found:
            raise ValueError(f"metadata contains disallowed sensitive keys: {', '.join(sorted(found))}")
        return value

    @field_validator("attestation")
    @classmethod
    def validate_attestation_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            return value
        provider = value.get("provider")
        if provider and provider not in {"intel-tdx", "intel-trust-authority", "custom"}:
            raise ValueError("attestation provider must be intel-tdx, intel-trust-authority, or custom")
        result = value.get("verification_result")
        if result and result not in {"verified", "failed", "missing", "not_required"}:
            raise ValueError("attestation verification_result is invalid")
        evidence_ref = value.get("evidence_ref")
        quote_hash = value.get("quote_hash")
        if provider in {"intel-tdx", "intel-trust-authority"} and result == "verified" and not (evidence_ref or quote_hash):
            raise ValueError("verified Intel attestation requires evidence_ref or quote_hash")
        return value

    @field_validator("marketplace")
    @classmethod
    def validate_marketplace_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            return value
        provider = value.get("provider")
        if provider and provider != "google-cloud-marketplace":
            raise ValueError("marketplace provider must be google-cloud-marketplace")
        return value

    def expiry_or_default(self) -> datetime:
        return self.expires_at or datetime.now(tz=timezone.utc) + timedelta(minutes=15)


class IntentDecisionResponse(BaseModel):
    result: Decision
    reason: str
    receipt_id: str
    cluster_id: str
    namespace: str
    workload_id: str
    expires_at: datetime
    latency_ms: float


class ReceiptListResponse(BaseModel):
    count: int
    items: list[dict[str, Any]]
