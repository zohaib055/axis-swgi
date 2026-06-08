from __future__ import annotations

from pydantic import BaseModel, Field


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
