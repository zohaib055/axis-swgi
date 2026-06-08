from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


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
