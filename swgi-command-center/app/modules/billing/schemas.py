from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

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


class MarketplaceUsageEventResponse(BaseModel):
    event_id: str
    org_id: str
    cluster_id: str
    namespace: str
    receipt_id: str
    provider: str
    metric_name: str
    quantity: int
    unit: str
    usage_time: datetime
    usage_reporting_id: str | None = None
    labels: dict[str, Any]
    status: str
    report_attempts: int
    last_reported_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


class MarketplaceUsageReportRequest(BaseModel):
    status: Literal["reported", "failed"]
    last_error: str | None = None
