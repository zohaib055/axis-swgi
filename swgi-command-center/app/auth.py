from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .security import constant_time_equal


@dataclass(slots=True)
class AuthContext:
    role: str
    token: str
    org_id: str | None = None
    cluster_id: str | None = None
    user_id: str | None = None
    email: str | None = None


AccessRole = Literal["platform_admin", "platform_viewer", "org_admin", "org_viewer", "operator"]


bearer_scheme = HTTPBearer(auto_error=False)


def require_bootstrap_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    token = credentials.credentials.strip()
    if constant_time_equal(token, settings.admin_api_token):
        return AuthContext(role="platform_admin", token=token)
    if constant_time_equal(token, settings.viewer_api_token):
        return AuthContext(role="platform_viewer", token=token)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token is not authorized")


def require_platform_admin(auth: AuthContext = Depends(require_bootstrap_auth)) -> AuthContext:
    if auth.role != "platform_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin role required")
    return auth


def require_role(auth: AuthContext, allowed: set[str]) -> AuthContext:
    if auth.role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is not authorized")
    return auth


def require_org_access(auth: AuthContext, org_id: str, *, write: bool = False) -> AuthContext:
    if auth.role in {"platform_admin", "platform_viewer"}:
        if write and auth.role != "platform_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin role required")
        return auth
    if auth.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Org access denied")
    if write and auth.role != "org_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Org admin role required")
    return auth


def require_cluster_operator(auth: AuthContext, org_id: str, cluster_id: str) -> AuthContext:
    if auth.role == "platform_admin":
        return auth
    if auth.role != "operator" or auth.org_id != org_id or auth.cluster_id != cluster_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator cluster access denied")
    return auth
