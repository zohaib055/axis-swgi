from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings


@dataclass(slots=True)
class AuthContext:
    role: str
    token: str


bearer_scheme = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    token = credentials.credentials.strip()
    if token == settings.admin_api_token:
        return AuthContext(role="admin", token=token)
    if token == settings.viewer_api_token:
        return AuthContext(role="viewer", token=token)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token is not authorized")


def require_admin(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    if auth.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return auth
