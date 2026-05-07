from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AuthorizeRequest(BaseModel):
    intent: str = Field(..., description="Explicit intent string")
    context: dict[str, Any] = Field(default_factory=dict, description="Context map")
    action: str = Field(..., description="Proposed action/workload")
    authority: dict[str, Any] = Field(default_factory=dict, description="Authority/credentials map")
    state: dict[str, Any] = Field(default_factory=dict, description="Optional state snapshot")
    workload_id: str = Field(default="unknown", description="Workload identifier")


class ReceiptListResponse(BaseModel):
    count: int
    items: list[dict[str, Any]]
