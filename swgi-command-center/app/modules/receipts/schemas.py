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
    expires_at: datetime | None = None

    @field_validator("authority", "policy_context", "requested_metadata")
    @classmethod
    def reject_sensitive_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        blocked = {"secret", "password", "token", "api_key", "apikey", "authorization", "env", "logs", "payload"}
        found = blocked.intersection({key.lower() for key in value})
        if found:
            raise ValueError(f"metadata contains disallowed sensitive keys: {', '.join(sorted(found))}")
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
