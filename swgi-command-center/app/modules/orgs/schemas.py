from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


OrgStatus = Literal["active", "suspended", "disabled"]


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
