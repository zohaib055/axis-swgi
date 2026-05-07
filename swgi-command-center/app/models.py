from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field, field_validator


Decision = Literal["ALLOW", "DENY", "MODIFY"]
OrgStatus = Literal["active", "suspended", "disabled"]
ClusterRuntime = Literal["kubernetes", "openshift", "gke", "eks", "aks", "on-prem", "private-cloud"]
ClusterStatus = Literal["pending", "active", "degraded", "disconnected", "disabled"]
ApiKeyRole = Literal["org_admin", "org_viewer", "operator"]


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


class UsageResponse(BaseModel):
    total_executions: int
    allowed_executions: int
    denied_attempts: int
    modified_executions: int
    cluster_count: int
    namespace_count: int


class OrgCreateRequest(BaseModel):
    org_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    plan_code: str = Field(default="starter", min_length=1)
    status: OrgStatus = "active"


class OrgUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)
    plan_code: str | None = Field(default=None, min_length=1)
    status: OrgStatus | None = None


class OrgResponse(BaseModel):
    org_id: str
    display_name: str | None = None
    status: str
    plan_code: str
    created_at: datetime
    updated_at: datetime


class ClusterCreateRequest(BaseModel):
    cluster_id: str = Field(default_factory=lambda: f"cluster-{uuid.uuid4()}")
    display_name: str = Field(..., min_length=1)
    runtime: ClusterRuntime = "kubernetes"


class ClusterResponse(BaseModel):
    cluster_id: str
    org_id: str
    runtime: str
    display_name: str | None = None
    status: str
    created_at: datetime
    last_seen_at: datetime | None = None
    health: str | None = None
    operator_version: str | None = None
    heartbeat_namespace: str | None = None
    last_heartbeat_at: datetime | None = None
    updated_at: datetime


class ClusterRegistrationResponse(BaseModel):
    cluster: ClusterResponse
    install: dict[str, str]


class ApiKeyCreateRequest(BaseModel):
    key_name: str = Field(..., min_length=1)
    role: ApiKeyRole
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    api_key_id: str
    org_id: str | None = None
    cluster_id: str | None = None
    key_name: str
    role: str
    status: str
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyResponse
    token: str


class OperatorEventRequest(BaseModel):
    org_id: str
    receipt_id: str
    cluster_id: str
    namespace: str
    workload_id: str
    enforcement_status: str
    operator_version: str
    error_code: str | None = None
    error_summary: str | None = None


class OperatorHeartbeatRequest(BaseModel):
    org_id: str
    cluster_id: str
    namespace: str
    operator_version: str
    health: str = Field(default="healthy", min_length=1)


class ExecutionStatusRequest(BaseModel):
    status: Literal["claimed", "running", "succeeded", "failed", "rejected"]
    error_code: str | None = None
    error_summary: str | None = None


class ExecutionResponse(BaseModel):
    execution_id: str
    receipt_id: str
    org_id: str
    cluster_id: str
    namespace: str
    workload_id: str
    action: str
    decision: str
    payload_hash: str
    receipt_metadata: dict[str, Any]
    status: str
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    error_code: str | None = None
    error_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class PlanResponse(BaseModel):
    plan_code: str
    display_name: str
    monthly_execution_limit: int | None = None
    cluster_limit: int | None = None
    namespace_limit: int | None = None
    retention_days: int


class AuditLogResponse(BaseModel):
    audit_id: int
    org_id: str | None = None
    cluster_id: str | None = None
    actor_role: str
    actor_org_id: str | None = None
    actor_cluster_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    outcome: str
    request_id: str | None = None
    created_at: datetime
