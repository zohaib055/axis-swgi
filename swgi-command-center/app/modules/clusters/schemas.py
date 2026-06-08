from __future__ import annotations

from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, Field


ClusterRuntime = Literal["kubernetes", "openshift", "gke", "eks", "aks", "on-prem", "private-cloud"]
ClusterStatus = Literal["pending", "active", "degraded", "disconnected", "disabled"]


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
