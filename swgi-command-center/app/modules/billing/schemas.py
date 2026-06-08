from __future__ import annotations

from pydantic import BaseModel


class UsageResponse(BaseModel):
    total_executions: int
    allowed_executions: int
    denied_attempts: int
    modified_executions: int
    cluster_count: int
    namespace_count: int


class PlanResponse(BaseModel):
    plan_code: str
    display_name: str
    monthly_execution_limit: int | None = None
    cluster_limit: int | None = None
    namespace_limit: int | None = None
    retention_days: int
