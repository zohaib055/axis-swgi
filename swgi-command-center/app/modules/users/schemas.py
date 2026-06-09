from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


UserRole = Literal["platform_admin", "platform_viewer", "org_admin", "org_viewer", "operator"]
UserStatus = Literal["active", "disabled"]


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserCreateRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=12, max_length=256)
    display_name: str | None = Field(default=None, max_length=200)
    role: UserRole
    org_id: str | None = None
    status: UserStatus = "active"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class SelfServiceSignupRequest(BaseModel):
    org_id: str = Field(..., min_length=2, max_length=80)
    org_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=12, max_length=256)
    display_name: str | None = Field(default=None, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("org_id")
    @classmethod
    def normalize_org_id(cls, value: str) -> str:
        normalized = value.strip().lower().replace("_", "-")
        if not normalized.replace("-", "").isalnum():
            raise ValueError("org_id may contain only letters, numbers, and hyphens")
        return normalized


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    role: UserRole | None = None
    org_id: str | None = None
    status: UserStatus | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str | None = Field(default=None, min_length=1, max_length=256)
    new_password: str = Field(..., min_length=12, max_length=256)


class PasswordResetRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=12, max_length=256)


class UserActionTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    delivery: str = "copy"


class UserResponse(BaseModel):
    user_id: str
    email: str
    display_name: str | None = None
    role: str
    org_id: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserResponse
