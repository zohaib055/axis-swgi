from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, generate_latest

load_dotenv()

from swgi_core.config import SWGIConfig
from swgi_core.evaluator import SWGIEnforcementNode
from swgi_core.policy_engine import PolicyEngine

from swgi_core.signature import export_public_key_pem, load_private_key

from .auth import (
    AuthContext,
    bearer_scheme,
    require_cluster_operator,
    require_org_access,
    require_role,
)
from .config import settings
from .db import CommandCenterStore
from .logging_config import configure_logging
from .models import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    AuditLogResponse,
    ClusterCreateRequest,
    ClusterRegistrationResponse,
    ClusterResponse,
    ExecutionIntentRequest,
    ExecutionResponse,
    ExecutionStatusRequest,
    IntentDecisionResponse,
    LoginRequest,
    LoginResponse,
    MarketplaceUsageEventResponse,
    MarketplaceUsageReportRequest,
    OperatorHeartbeatRequest,
    OperatorEventRequest,
    OrgCreateRequest,
    OrgResponse,
    OrgUpdateRequest,
    PlanResponse,
    ReceiptListResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    SelfServiceSignupRequest,
    UsageResponse,
    UserActionTokenResponse,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from .receipts import metadata_receipt
from .security import constant_time_equal, generate_api_token, hash_password, hash_token, verify_password

configure_logging(settings.log_level, settings.log_format)
logger = logging.getLogger("swgi_command_center")
settings.validate_runtime()


class Metrics:
    def __init__(self) -> None:
        self.intent_total = Counter("swgi_command_center_intents_total", "Total intent decisions", ["result"])
        self.intent_total_by_scope = Counter(
            "swgi_command_center_scoped_intents_total",
            "Total intent decisions by org and cluster",
            ["org_id", "cluster_id", "result"],
        )
        self.intent_latency = Histogram(
            "swgi_command_center_intent_latency_ms",
            "Intent decision latency (ms)",
            buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100, 250, 500, 1000),
        )

    def observe_intent(self, latency_ms: float, result: str, org_id: str = "unknown", cluster_id: str = "unknown") -> None:
        self.intent_total.labels(result=result).inc()
        self.intent_total_by_scope.labels(org_id=org_id, cluster_id=cluster_id, result=result).inc()
        self.intent_latency.observe(latency_ms)


def _load_private_key_pem(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _load_policy_id(policy_path: str) -> str:
    return PolicyEngine.from_file(policy_path).policy_id


app = FastAPI(title="SWGI Command Center", version=settings.app_version)
store = CommandCenterStore(settings.database_url)
if settings.run_db_migrations:
    store.initialize()

policy_engine = PolicyEngine.from_file(settings.policy_path)
config = SWGIConfig(
    org_id=settings.org_id,
    node_id=settings.command_center_id,
    policy_id=_load_policy_id(settings.policy_path),
)
node = SWGIEnforcementNode(
    config=config,
    signing_private_key_pem=_load_private_key_pem(settings.signing_key_path),
    policy_engine=policy_engine,
)
metrics = Metrics()
rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)
login_failures: dict[str, deque[float]] = defaultdict(deque)

logger.info(
    "swgi_command_center.started mode=%s command_center_id=%s org_id=%s receipt_store=postgres",
    settings.swgi_mode,
    settings.command_center_id,
    settings.org_id,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next: Any) -> Any:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id

    token = request.headers.get("authorization", "")
    bucket_key = hash_token(token or request.client.host if request.client else "unknown", settings.api_key_hash_secret)
    now = time.time()
    bucket = rate_limit_buckets[bucket_key]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse(
            {"detail": "Rate limit exceeded"},
            status_code=429,
            headers={"x-request-id": request_id},
        )
    bucket.append(now)

    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


def get_auth_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    cookie_token = request.cookies.get(settings.auth_cookie_name)
    if credentials is None and not cookie_token:
        store.record_failed_auth(None, "missing_authorization_header", getattr(request.state, "request_id", None))
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if credentials is not None and (credentials.scheme.lower() != "bearer" or not credentials.credentials.strip()):
        store.record_failed_auth(None, "invalid_bearer_header", getattr(request.state, "request_id", None))
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    token = credentials.credentials.strip() if credentials is not None else (cookie_token or "").strip()
    if constant_time_equal(token, settings.admin_api_token):
        return AuthContext(role="platform_admin", token=token)
    if constant_time_equal(token, settings.viewer_api_token):
        return AuthContext(role="platform_viewer", token=token)

    session = store.resolve_user_session(token)
    if session:
        return AuthContext(
            role=session["role"],
            token=token,
            org_id=session.get("org_id"),
            user_id=session.get("user_id"),
            email=session.get("email"),
        )

    key = store.resolve_api_key(token)
    if not key:
        store.record_failed_auth(
            hash_token(token, settings.api_key_hash_secret),
            "unauthorized_token",
            getattr(request.state, "request_id", None),
        )
        raise HTTPException(status_code=403, detail="Token is not authorized")
    return AuthContext(
        role=key["role"],
        token=token,
        org_id=key.get("org_id"),
        cluster_id=key.get("cluster_id"),
    )


def _validate_user_role_scope(role: str, org_id: str | None) -> None:
    if role in {"platform_admin", "platform_viewer"} and org_id:
        raise HTTPException(status_code=400, detail="Platform users cannot be scoped to an org")
    if role in {"org_admin", "org_viewer", "operator"} and not org_id:
        raise HTTPException(status_code=400, detail="Org-scoped users require org_id")


def _require_user_management_scope(auth: AuthContext, *, target_role: str | None, target_org_id: str | None) -> None:
    if auth.role == "platform_admin":
        if target_role:
            _validate_user_role_scope(target_role, target_org_id)
        return
    if auth.role != "org_admin":
        raise HTTPException(status_code=403, detail="User management role required")
    if not auth.org_id or target_org_id != auth.org_id:
        raise HTTPException(status_code=403, detail="Org user management denied")
    if target_role not in {None, "org_admin", "org_viewer"}:
        raise HTTPException(status_code=403, detail="Org admins can only manage org admin/viewer users")


def _user_response_for_auth(auth: AuthContext) -> UserResponse:
    return UserResponse(
        user_id=auth.user_id or "bootstrap",
        email=auth.email or f"{auth.role}@bootstrap.swgi.local",
        display_name="Bootstrap token" if not auth.user_id else None,
        role=auth.role,
        org_id=auth.org_id,
        status="active",
        created_at=None,
        updated_at=None,
        last_login_at=None,
    )


def _login_key(req: LoginRequest, request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{req.email}:{host}"


def _check_login_lockout(req: LoginRequest, request: Request) -> None:
    key = _login_key(req, request)
    now = time.time()
    failures = login_failures[key]
    window_seconds = settings.login_lockout_minutes * 60
    while failures and now - failures[0] > window_seconds:
        failures.popleft()
    if len(failures) >= settings.login_failure_limit:
        raise HTTPException(status_code=429, detail="Too many failed login attempts")


def _record_login_failure(req: LoginRequest, request: Request) -> None:
    login_failures[_login_key(req, request)].append(time.time())


def _clear_login_failures(req: LoginRequest, request: Request) -> None:
    login_failures.pop(_login_key(req, request), None)


def _set_auth_cookie(response: Response, token: str, expires_at: datetime) -> None:
    response.set_cookie(
        settings.auth_cookie_name,
        token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        expires=expires_at,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


def _org_filter_for(auth: AuthContext, requested_org_id: str | None) -> str | None:
    if auth.role in {"platform_admin", "platform_viewer"}:
        return requested_org_id
    if auth.role in {"org_admin", "org_viewer", "operator"}:
        if requested_org_id and requested_org_id != auth.org_id:
            raise HTTPException(status_code=403, detail="Org access denied")
        return auth.org_id
    raise HTTPException(status_code=403, detail="Role is not authorized")


def _public_signing_key_pem() -> str:
    private_key = load_private_key(_load_private_key_pem(settings.signing_key_path))
    return export_public_key_pem(private_key)


def _audit(
    auth: AuthContext,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    org_id: str | None = None,
    cluster_id: str | None = None,
    outcome: str = "success",
    request: Request | None = None,
) -> None:
    store.persist_audit_log(
        {
            "org_id": org_id or auth.org_id,
            "cluster_id": cluster_id or auth.cluster_id,
            "actor_role": auth.role,
            "actor_org_id": auth.org_id,
            "actor_cluster_id": auth.cluster_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "outcome": outcome,
            "request_id": getattr(request.state, "request_id", None) if request else None,
        }
    )


@app.get("/v1/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "mode": settings.swgi_mode,
        "command_center_id": settings.command_center_id,
        "policy_id": config.policy_id,
        "receipt_store": "postgres",
    }


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return health()


@app.get("/readyz")
def readyz() -> dict[str, Any]:
    try:
        db_ok = store.health_check()
    except Exception:
        db_ok = False
    if not db_ok:
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"ok": True, "database": "ready"}


@app.get("/metrics")
def prometheus_metrics() -> PlainTextResponse:
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type="text/plain; version=0.0.4")


@app.post("/v1/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, response: Response) -> LoginResponse:
    _check_login_lockout(req, request)
    user = store.get_user_by_email(req.email)
    if not user or user["status"] != "active" or not verify_password(req.password, user["password_hash"]):
        _record_login_failure(req, request)
        store.record_failed_auth(None, "invalid_user_credentials", getattr(request.state, "request_id", None))
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = generate_api_token("swgi_user")
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    session = store.create_user_session(user["user_id"], token, expires_at)
    if not session:
        raise HTTPException(status_code=403, detail="User is not active")
    auth = AuthContext(
        role=user["role"],
        token=token,
        org_id=user.get("org_id"),
        user_id=user["user_id"],
        email=user["email"],
    )
    _audit(auth, action="login", resource_type="user", resource_id=user["user_id"], org_id=user.get("org_id"), request=request)
    _clear_login_failures(req, request)
    _set_auth_cookie(response, token, session["expires_at"])
    return LoginResponse(access_token=token, expires_at=session["expires_at"], user=UserResponse(**session["user"]))


@app.post("/v1/auth/signup", response_model=LoginResponse)
def signup(req: SelfServiceSignupRequest, request: Request, response: Response) -> LoginResponse:
    token = generate_api_token("swgi_user")
    user_id = str(uuid.uuid4())
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    try:
        created = store.create_self_service_signup(
            org={
                "org_id": req.org_id,
                "display_name": req.org_name,
                "plan_code": "starter",
                "status": "active",
            },
            user={
                "user_id": user_id,
                "email": req.email,
                "display_name": req.display_name or req.email,
                "password_hash": hash_password(req.password),
                "role": "org_admin",
                "org_id": req.org_id,
                "status": "active",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Org or user already exists") from exc
    session = store.create_user_session(user_id, token, expires_at)
    if not session:
        raise HTTPException(status_code=403, detail="User is not active")
    auth = AuthContext(role="org_admin", token=token, org_id=req.org_id, user_id=user_id, email=req.email)
    _audit(auth, action="self_service_signup", resource_type="org", resource_id=created["org"]["org_id"], org_id=req.org_id, request=request)
    _set_auth_cookie(response, token, session["expires_at"])
    return LoginResponse(access_token=token, expires_at=session["expires_at"], user=UserResponse(**session["user"]))


@app.get("/v1/auth/me", response_model=UserResponse)
def me(auth: AuthContext = Depends(get_auth_context)) -> UserResponse:
    if auth.user_id:
        session = store.resolve_user_session(auth.token)
        if session:
            return UserResponse(**session)
    return _user_response_for_auth(auth)


@app.post("/v1/auth/logout")
def logout(response: Response, auth: AuthContext = Depends(get_auth_context)) -> dict[str, str]:
    if auth.user_id:
        store.revoke_user_session(auth.token)
    _clear_auth_cookie(response)
    return {"status": "signed_out"}


@app.post("/v1/auth/password-reset", response_model=UserActionTokenResponse)
def request_password_reset(req: PasswordResetRequest, request: Request) -> UserActionTokenResponse:
    user = store.get_user_by_email(req.email)
    if not user:
        return UserActionTokenResponse(token="", expires_at=datetime.now(tz=timezone.utc), delivery="email_if_found")
    token = generate_api_token("swgi_reset")
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=2)
    store.create_user_action_token(user["user_id"], token, "password_reset", expires_at)
    _audit(
        AuthContext(role=user["role"], token="", org_id=user.get("org_id"), user_id=user["user_id"], email=user["email"]),
        action="request_password_reset",
        resource_type="user",
        resource_id=user["user_id"],
        org_id=user.get("org_id"),
        request=request,
    )
    return UserActionTokenResponse(token=token, expires_at=expires_at, delivery="copy")


@app.post("/v1/auth/password-reset/confirm")
def confirm_password_reset(req: PasswordResetConfirmRequest) -> dict[str, str]:
    payload = store.consume_user_action_token(req.token, "password_reset")
    if not payload:
        payload = store.consume_user_action_token(req.token, "invite")
    if not payload:
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")
    store.update_user_password(payload["user"]["user_id"], hash_password(req.new_password))
    return {"status": "password_updated"}


@app.post("/v1/users", response_model=UserResponse)
def create_user(req: UserCreateRequest, request: Request, auth: AuthContext = Depends(get_auth_context)) -> UserResponse:
    target_org_id = req.org_id
    if auth.role == "org_admin":
        target_org_id = auth.org_id
    _require_user_management_scope(auth, target_role=req.role, target_org_id=target_org_id)
    if target_org_id and not store.get_org(target_org_id):
        raise HTTPException(status_code=404, detail="Org not found")
    try:
        user = store.create_user(
            {
                "user_id": str(uuid.uuid4()),
                "email": req.email,
                "display_name": req.display_name,
                "password_hash": hash_password(req.password),
                "role": req.role,
                "org_id": target_org_id,
                "status": req.status,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="User could not be created") from exc
    _audit(auth, action="create_user", resource_type="user", resource_id=user["user_id"], org_id=user.get("org_id"), request=request)
    return UserResponse(**user)


@app.post("/v1/users/{user_id}/invite", response_model=UserActionTokenResponse)
def create_user_invite(user_id: str, request: Request, auth: AuthContext = Depends(get_auth_context)) -> UserActionTokenResponse:
    existing = store.get_user(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    _require_user_management_scope(auth, target_role=existing["role"], target_org_id=existing["org_id"])
    token = generate_api_token("swgi_invite")
    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=7)
    stored = store.create_user_action_token(user_id, token, "invite", expires_at)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    _audit(auth, action="create_user_invite", resource_type="user", resource_id=user_id, org_id=existing.get("org_id"), request=request)
    return UserActionTokenResponse(token=token, expires_at=expires_at, delivery="copy")


@app.post("/v1/auth/invite/accept")
def accept_invite(req: PasswordResetConfirmRequest) -> dict[str, str]:
    payload = store.consume_user_action_token(req.token, "invite")
    if not payload:
        raise HTTPException(status_code=400, detail="Invite token is invalid or expired")
    store.update_user_password(payload["user"]["user_id"], hash_password(req.new_password), revoke_existing_sessions=True)
    return {"status": "invite_accepted"}


@app.get("/v1/users", response_model=list[UserResponse])
def list_users(
    org_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
) -> list[UserResponse]:
    require_role(auth, {"platform_admin", "platform_viewer", "org_admin", "org_viewer"})
    scoped_org_id = _org_filter_for(auth, org_id)
    return [UserResponse(**user) for user in store.list_users(org_id=scoped_org_id, limit=limit, offset=offset)]


@app.get("/v1/settings")
def get_settings(auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_role(auth, {"platform_admin", "platform_viewer"})
    return store.get_settings()


@app.patch("/v1/settings/{setting_key}")
def update_setting(
    setting_key: str,
    payload: dict[str, Any],
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_role(auth, {"platform_admin"})
    if setting_key not in {"security", "onboarding"}:
        raise HTTPException(status_code=404, detail="Setting not found")
    updated = store.update_setting(setting_key, payload)
    _audit(auth, action="update_setting", resource_type="setting", resource_id=setting_key, request=request)
    return updated


@app.patch("/v1/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, req: UserUpdateRequest, request: Request, auth: AuthContext = Depends(get_auth_context)) -> UserResponse:
    existing = store.get_user(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    patch = req.model_dump(exclude_unset=True, mode="json")
    target_role = patch.get("role", existing["role"])
    target_org_id = patch.get("org_id", existing["org_id"])
    if auth.role == "org_admin":
        target_org_id = auth.org_id
        patch["org_id"] = auth.org_id
    _require_user_management_scope(auth, target_role=target_role, target_org_id=target_org_id)
    if target_org_id and not store.get_org(target_org_id):
        raise HTTPException(status_code=404, detail="Org not found")
    user = store.update_user(user_id, patch)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _audit(auth, action="update_user", resource_type="user", resource_id=user_id, org_id=user.get("org_id"), request=request)
    return UserResponse(**user)


@app.post("/v1/users/{user_id}/password")
def change_user_password(
    user_id: str,
    req: PasswordChangeRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, str]:
    existing = store.get_user(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    if auth.user_id == user_id:
        if not req.current_password or not verify_password(req.current_password, existing["password_hash"]):
            raise HTTPException(status_code=403, detail="Current password is required")
    else:
        _require_user_management_scope(auth, target_role=existing["role"], target_org_id=existing["org_id"])
    if not store.update_user_password(user_id, hash_password(req.new_password)):
        raise HTTPException(status_code=404, detail="User not found")
    _audit(auth, action="change_user_password", resource_type="user", resource_id=user_id, org_id=existing.get("org_id"), request=request)
    return {"status": "password_updated"}


@app.post("/v1/orgs", response_model=OrgResponse)
def create_org(req: OrgCreateRequest, request: Request, auth: AuthContext = Depends(get_auth_context)) -> OrgResponse:
    require_role(auth, {"platform_admin"})
    try:
        org = store.create_org(req.model_dump(mode="json"))
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Org could not be created") from exc
    _audit(auth, action="create_org", resource_type="org", resource_id=org["org_id"], org_id=org["org_id"], request=request)
    return OrgResponse(**org)


@app.get("/v1/orgs", response_model=list[OrgResponse])
def list_orgs(
    limit: int = 100,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
) -> list[OrgResponse]:
    require_role(auth, {"platform_admin", "platform_viewer"})
    return [OrgResponse(**org) for org in store.list_orgs(limit=limit, offset=offset)]


@app.get("/v1/orgs/{org_id}", response_model=OrgResponse)
def get_org(org_id: str, auth: AuthContext = Depends(get_auth_context)) -> OrgResponse:
    require_org_access(auth, org_id)
    org = store.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    return OrgResponse(**org)


@app.patch("/v1/orgs/{org_id}", response_model=OrgResponse)
def update_org(org_id: str, req: OrgUpdateRequest, request: Request, auth: AuthContext = Depends(get_auth_context)) -> OrgResponse:
    require_org_access(auth, org_id, write=True)
    org = store.update_org(org_id, req.model_dump(exclude_unset=True, mode="json"))
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    _audit(auth, action="update_org", resource_type="org", resource_id=org_id, org_id=org_id, request=request)
    return OrgResponse(**org)


@app.post("/v1/orgs/{org_id}/api-keys", response_model=ApiKeyCreateResponse)
def create_api_key(
    org_id: str,
    req: ApiKeyCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> ApiKeyCreateResponse:
    require_org_access(auth, org_id, write=True)
    if req.role == "operator":
        raise HTTPException(status_code=400, detail="Operator keys are generated through cluster registration")
    if not store.get_org(org_id):
        raise HTTPException(status_code=404, detail="Org not found")
    token = generate_api_token("swgi_org")
    api_key = store.create_api_key(
        api_key_id=str(uuid.uuid4()),
        org_id=org_id,
        cluster_id=None,
        key_name=req.key_name,
        role=req.role,
        token=token,
        expires_at=req.expires_at.isoformat() if req.expires_at else None,
    )
    _audit(auth, action="create_api_key", resource_type="api_key", resource_id=api_key["api_key_id"], org_id=org_id, request=request)
    return ApiKeyCreateResponse(api_key=ApiKeyResponse(**api_key), token=token)


@app.get("/v1/orgs/{org_id}/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(org_id: str, auth: AuthContext = Depends(get_auth_context)) -> list[ApiKeyResponse]:
    require_org_access(auth, org_id, write=True)
    return [ApiKeyResponse(**key) for key in store.list_api_keys(org_id)]


@app.delete("/v1/orgs/{org_id}/api-keys/{api_key_id}")
def revoke_api_key(org_id: str, api_key_id: str, request: Request, auth: AuthContext = Depends(get_auth_context)) -> dict[str, str]:
    require_org_access(auth, org_id, write=True)
    if not store.revoke_api_key(org_id, api_key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    _audit(auth, action="revoke_api_key", resource_type="api_key", resource_id=api_key_id, org_id=org_id, request=request)
    return {"status": "revoked"}


@app.post("/v1/orgs/{org_id}/api-keys/{api_key_id}/rotate", response_model=ApiKeyCreateResponse)
def rotate_api_key(org_id: str, api_key_id: str, request: Request, auth: AuthContext = Depends(get_auth_context)) -> ApiKeyCreateResponse:
    require_org_access(auth, org_id, write=True)
    old_key = store.get_api_key(org_id, api_key_id)
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")
    if not store.revoke_api_key(org_id, api_key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    token = generate_api_token("swgi_operator" if old_key["role"] == "operator" else "swgi_org")
    api_key = store.create_api_key(
        api_key_id=str(uuid.uuid4()),
        org_id=org_id,
        cluster_id=old_key.get("cluster_id"),
        key_name=f"{old_key['key_name']} rotated",
        role=old_key["role"],
        token=token,
        rotated_from_api_key_id=api_key_id,
    )
    _audit(auth, action="rotate_api_key", resource_type="api_key", resource_id=api_key_id, org_id=org_id, request=request)
    return ApiKeyCreateResponse(api_key=ApiKeyResponse(**api_key), token=token)


@app.post("/v1/orgs/{org_id}/clusters", response_model=ClusterRegistrationResponse)
def create_cluster(
    org_id: str,
    req: ClusterCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> ClusterRegistrationResponse:
    if auth.role == "platform_admin":
        pass
    elif auth.role == "org_admin" and auth.org_id == org_id:
        pass
    else:
        require_org_access(auth, org_id, write=True)
    install_token = generate_api_token("swgi_operator")
    cluster = store.create_cluster({**req.model_dump(mode="json"), "org_id": org_id}, install_token)
    if not cluster:
        raise HTTPException(status_code=404, detail="Org not found")
    store.create_api_key(
        api_key_id=str(uuid.uuid4()),
        org_id=org_id,
        cluster_id=cluster["cluster_id"],
        key_name=f"{cluster['cluster_id']} operator",
        role="operator",
        token=install_token,
    )
    _audit(auth, action="register_cluster", resource_type="cluster", resource_id=cluster["cluster_id"], org_id=org_id, cluster_id=cluster["cluster_id"], request=request)
    install = {
        "COMMAND_CENTER_URL": settings.command_center_url,
        "ORG_ID": org_id,
        "CLUSTER_ID": cluster["cluster_id"],
        "OPERATOR_TOKEN": install_token,
        "PUBLIC_SIGNING_KEY_PEM": _public_signing_key_pem(),
    }
    return ClusterRegistrationResponse(cluster=ClusterResponse(**cluster), install=install)


@app.get("/v1/orgs/{org_id}/clusters", response_model=list[ClusterResponse])
def list_org_clusters(org_id: str, auth: AuthContext = Depends(get_auth_context)) -> list[ClusterResponse]:
    require_org_access(auth, org_id)
    return [ClusterResponse(**cluster) for cluster in store.list_clusters(org_id=org_id)]


@app.get("/v1/orgs/{org_id}/clusters/{cluster_id}", response_model=ClusterResponse)
def get_cluster(org_id: str, cluster_id: str, auth: AuthContext = Depends(get_auth_context)) -> ClusterResponse:
    require_org_access(auth, org_id)
    cluster = store.get_cluster(org_id, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return ClusterResponse(**cluster)


@app.post("/v1/operator/heartbeat", response_model=ClusterResponse)
def operator_heartbeat(
    req: OperatorHeartbeatRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> ClusterResponse:
    require_cluster_operator(auth, req.org_id, req.cluster_id)
    cluster = store.record_heartbeat(req.model_dump(mode="json"))
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    _audit(auth, action="operator_heartbeat", resource_type="cluster", resource_id=req.cluster_id, org_id=req.org_id, cluster_id=req.cluster_id, request=request)
    return ClusterResponse(**cluster)


@app.post("/v1/intents", response_model=IntentDecisionResponse)
def submit_intent(req: ExecutionIntentRequest, request: Request, auth: AuthContext = Depends(get_auth_context)) -> IntentDecisionResponse:
    require_org_access(auth, req.org_id, write=True)
    t0 = time.perf_counter()
    authority_role = "admin" if auth.role in {"platform_admin", "org_admin"} else auth.role
    authority = {"role": authority_role, **req.authority}
    context = {
        "org_id": req.org_id,
        "cluster_id": req.cluster_id,
        "namespace": req.namespace,
        "identity": req.identity,
        "attestation": req.attestation,
        **req.policy_context,
    }
    decision, base_receipt = node.evaluate(
        intent=req.intent,
        context=context,
        action=req.action,
        authority=authority,
        workload_id=req.workload_id,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    receipt = metadata_receipt(
        base_receipt,
        req,
        elapsed_ms,
        command_center_id=settings.command_center_id,
    )
    store.persist_receipt(receipt)
    metrics.observe_intent(elapsed_ms, decision, org_id=req.org_id, cluster_id=req.cluster_id)

    logger.info(
        "intent.decided receipt_id=%s org_id=%s cluster_id=%s namespace=%s workload_id=%s decision=%s policy_id=%s",
        receipt["receipt_id"],
        receipt["org_id"],
        receipt["cluster_id"],
        receipt["namespace"],
        receipt["workload_id"],
        decision,
        receipt["policy_id"],
    )
    _audit(auth, action="submit_intent", resource_type="receipt", resource_id=receipt["receipt_id"], org_id=req.org_id, cluster_id=req.cluster_id, request=request)
    return IntentDecisionResponse(
        result=decision,
        reason=receipt["reason"],
        receipt_id=receipt["receipt_id"],
        cluster_id=receipt["cluster_id"],
        namespace=receipt["namespace"],
        workload_id=receipt["workload_id"],
        expires_at=req.expiry_or_default(),
        latency_ms=round(elapsed_ms, 4),
    )


@app.get("/v1/receipts/{receipt_id}")
def get_receipt(receipt_id: str, auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    receipt = store.load_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    require_org_access(auth, receipt["org_id"])
    return JSONResponse(receipt)


@app.get("/v1/receipts", response_model=ReceiptListResponse)
def list_receipts(
    org_id: str | None = None,
    cluster_id: str | None = None,
    namespace: str | None = None,
    workload_id: str | None = None,
    decision: str | None = None,
    policy_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
) -> ReceiptListResponse:
    scoped_org_id = _org_filter_for(auth, org_id)
    scoped_cluster_id = auth.cluster_id if auth.role == "operator" else cluster_id
    items = store.list_receipts(
        org_id=scoped_org_id,
        cluster_id=scoped_cluster_id,
        namespace=namespace,
        workload_id=workload_id,
        decision=decision,
        policy_id=policy_id,
        limit=limit,
        offset=offset,
    )
    return ReceiptListResponse(count=len(items), items=items)


@app.get("/v1/usage", response_model=UsageResponse)
def usage(org_id: str | None = None, auth: AuthContext = Depends(get_auth_context)) -> UsageResponse:
    require_role(auth, {"platform_admin", "platform_viewer", "org_admin", "org_viewer"})
    scoped_org_id = _org_filter_for(auth, org_id)
    return UsageResponse(**store.usage_summary(org_id=scoped_org_id))


@app.get("/v1/marketplace/google/usage-events", response_model=list[MarketplaceUsageEventResponse])
def google_marketplace_usage_events(
    status: str | None = "pending",
    org_id: str | None = None,
    limit: int = 100,
    auth: AuthContext = Depends(get_auth_context),
) -> list[MarketplaceUsageEventResponse]:
    require_role(auth, {"platform_admin", "platform_viewer"})
    events = store.list_marketplace_usage_events(
        provider="google-cloud-marketplace",
        status=status,
        org_id=org_id,
        limit=limit,
    )
    return [MarketplaceUsageEventResponse(**event) for event in events]


@app.get("/v1/marketplace/google/service-control-operations")
def google_marketplace_service_control_operations(
    status: str | None = "pending",
    org_id: str | None = None,
    limit: int = 100,
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, list[dict[str, Any]]]:
    require_role(auth, {"platform_admin", "platform_viewer"})
    events = store.list_marketplace_usage_events(
        provider="google-cloud-marketplace",
        status=status,
        org_id=org_id,
        limit=limit,
    )
    operations = []
    for event in events:
        operations.append(
            {
                "operationId": event["event_id"],
                "operationName": event["metric_name"],
                "consumerId": f"project:{event['usage_reporting_id']}" if event.get("usage_reporting_id") else None,
                "startTime": event["usage_time"].isoformat(),
                "endTime": event["usage_time"].isoformat(),
                "metricValueSets": [
                    {
                        "metricName": event["metric_name"],
                        "metricValues": [{"int64Value": event["quantity"]}],
                    }
                ],
                "labels": event["labels"],
            }
        )
    return {"operations": operations}


@app.post("/v1/marketplace/google/usage-events/{event_id}/report", response_model=MarketplaceUsageEventResponse)
def mark_google_marketplace_usage_event(
    event_id: str,
    req: MarketplaceUsageReportRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> MarketplaceUsageEventResponse:
    require_role(auth, {"platform_admin"})
    updated = store.mark_marketplace_usage_event_reported(
        event_id,
        status=req.status,
        last_error=req.last_error,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Marketplace usage event not found")
    _audit(auth, action="mark_marketplace_usage_event", resource_type="marketplace_usage_event", resource_id=event_id, request=request)
    return MarketplaceUsageEventResponse(**updated)


@app.get("/v1/clusters", response_model=list[ClusterResponse])
def clusters(org_id: str | None = None, auth: AuthContext = Depends(get_auth_context)) -> list[ClusterResponse]:
    scoped_org_id = _org_filter_for(auth, org_id)
    clusters = store.list_clusters(org_id=scoped_org_id)
    if auth.role == "operator":
        clusters = [cluster for cluster in clusters if cluster["cluster_id"] == auth.cluster_id]
    return [ClusterResponse(**cluster) for cluster in clusters]


@app.get("/v1/policies")
def policies(org_id: str | None = None, auth: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_role(auth, {"platform_admin", "platform_viewer", "org_admin", "org_viewer"})
    scoped_org_id = _org_filter_for(auth, org_id)
    return store.list_policies(org_id=scoped_org_id)


@app.post("/v1/operator-events")
def create_operator_event(req: OperatorEventRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, str]:
    require_cluster_operator(auth, req.org_id, req.cluster_id)
    store.persist_operator_event(req.model_dump(mode="json"))
    return {"status": "accepted"}


@app.get("/v1/operator/executions/pending", response_model=list[ExecutionResponse])
def pending_executions(
    limit: int = 25,
    auth: AuthContext = Depends(get_auth_context),
) -> list[ExecutionResponse]:
    require_role(auth, {"operator"})
    return [
        ExecutionResponse(**item)
        for item in store.list_pending_executions(auth.org_id or "", auth.cluster_id or "", limit=limit)
    ]


@app.post("/v1/operator/executions/{execution_id}/status", response_model=ExecutionResponse)
def update_execution_status(
    execution_id: str,
    req: ExecutionStatusRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> ExecutionResponse:
    require_role(auth, {"operator"})
    execution = store.update_execution_status(
        auth.org_id or "",
        auth.cluster_id or "",
        execution_id,
        req.status,
        req.error_code,
        req.error_summary,
    )
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    _audit(
        auth,
        action="update_execution_status",
        resource_type="execution",
        resource_id=execution_id,
        org_id=auth.org_id,
        cluster_id=auth.cluster_id,
        request=request,
    )
    return ExecutionResponse(**execution)


@app.get("/v1/plans", response_model=list[PlanResponse])
def list_plans(auth: AuthContext = Depends(get_auth_context)) -> list[PlanResponse]:
    require_role(auth, {"platform_admin", "platform_viewer", "org_admin", "org_viewer"})
    return [PlanResponse(**plan) for plan in store.list_plans()]


@app.get("/v1/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    org_id: str | None = None,
    limit: int = 100,
    auth: AuthContext = Depends(get_auth_context),
) -> list[AuditLogResponse]:
    scoped_org_id = _org_filter_for(auth, org_id)
    require_role(auth, {"platform_admin", "platform_viewer", "org_admin", "org_viewer"})
    return [AuditLogResponse(**item) for item in store.list_audit_logs(org_id=scoped_org_id, limit=limit)]


@app.get("/v1/operator-events")
def operator_events(
    receipt_id: str | None = None,
    org_id: str | None = None,
    cluster_id: str | None = None,
    limit: int = 50,
    auth: AuthContext = Depends(get_auth_context),
) -> list[dict[str, Any]]:
    scoped_org_id = _org_filter_for(auth, org_id)
    scoped_cluster_id = cluster_id
    if auth.role == "operator":
        scoped_cluster_id = auth.cluster_id
    return store.list_operator_events(
        org_id=scoped_org_id,
        cluster_id=scoped_cluster_id,
        receipt_id=receipt_id,
        limit=limit,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, reload=False)
