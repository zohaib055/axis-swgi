from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ApiKeyRole = Literal["org_admin", "org_viewer", "operator"]


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
