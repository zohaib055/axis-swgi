from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


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
