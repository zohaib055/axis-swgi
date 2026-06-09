from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import case, distinct, func, select

from .config import settings
from .database import create_session_factory, session_scope
from .db_url import normalize_psycopg_dsn
from .migrations import run_migrations
from .orm import (
    ApiKey,
    AuditLog,
    Cluster,
    ControlPlaneSetting,
    ExecutionRequest,
    FailedAuthEvent,
    Namespace,
    OperatorEvent,
    Organization,
    Plan,
    Policy,
    TrustReceipt,
    UsageMetering,
    User,
    UserActionToken,
    UserSession,
)
from .security import hash_token


def _as_dict(model: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(model, field) for field in fields}


ORG_FIELDS = ("org_id", "display_name", "status", "plan_code", "created_at", "updated_at")
CLUSTER_FIELDS = (
    "cluster_id",
    "org_id",
    "runtime",
    "display_name",
    "status",
    "created_at",
    "last_seen_at",
    "health",
    "operator_version",
    "heartbeat_namespace",
    "last_heartbeat_at",
    "updated_at",
)
API_KEY_FIELDS = (
    "api_key_id",
    "org_id",
    "cluster_id",
    "key_name",
    "role",
    "status",
    "created_at",
    "expires_at",
    "last_used_at",
    "revoked_at",
)
USER_FIELDS = (
    "user_id",
    "email",
    "display_name",
    "role",
    "org_id",
    "status",
    "created_at",
    "updated_at",
    "last_login_at",
)
EXECUTION_FIELDS = (
    "execution_id",
    "receipt_id",
    "org_id",
    "cluster_id",
    "namespace",
    "workload_id",
    "action",
    "decision",
    "payload_hash",
    "receipt_metadata",
    "status",
    "claimed_at",
    "completed_at",
    "error_code",
    "error_summary",
    "created_at",
    "updated_at",
)


class CommandCenterStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = normalize_psycopg_dsn(dsn)
        self.session_factory = create_session_factory(self.dsn)

    def initialize(self) -> None:
        run_migrations(self.dsn)

    def health_check(self) -> bool:
        with session_scope(self.session_factory) as session:
            return session.execute(select(1)).scalar_one() == 1

    def resolve_api_key(self, token: str) -> dict[str, Any] | None:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        now = datetime.now(tz=timezone.utc)
        with session_scope(self.session_factory) as session:
            api_key = session.scalars(
                select(ApiKey).where(
                    ApiKey.token_hash == token_hash,
                    ApiKey.status == "active",
                    ApiKey.revoked_at.is_(None),
                    (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > now),
                )
            ).first()
            if not api_key:
                return None
            api_key.last_used_at = now
            return _as_dict(api_key, ("api_key_id", "org_id", "cluster_id", "key_name", "role"))

    def resolve_user_session(self, token: str) -> dict[str, Any] | None:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        now = datetime.now(tz=timezone.utc)
        with session_scope(self.session_factory) as session:
            row = session.execute(
                select(UserSession, User)
                .join(User, User.user_id == UserSession.user_id)
                .where(
                    UserSession.token_hash == token_hash,
                    UserSession.status == "active",
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > now,
                    User.status == "active",
                )
            ).first()
            if not row:
                return None
            user_session, user = row
            user_session.last_seen_at = now
            return {
                **_as_dict(user, USER_FIELDS),
                "session_id": user_session.session_id,
                "expires_at": user_session.expires_at,
            }

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            user = session.scalars(select(User).where(User.email == email.strip().lower())).first()
            if not user:
                return None
            data = _as_dict(user, USER_FIELDS)
            data["password_hash"] = user.password_hash
            return data

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        with session_scope(self.session_factory) as session:
            user = User(**payload)
            session.add(user)
            session.flush()
            return _as_dict(user, USER_FIELDS)

    def create_self_service_signup(self, *, org: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        with session_scope(self.session_factory) as session:
            organization = Organization(**org)
            admin = User(**user)
            session.add(organization)
            session.add(admin)
            session.flush()
            return {
                "org": _as_dict(organization, ORG_FIELDS),
                "user": _as_dict(admin, USER_FIELDS),
            }

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            user = session.get(User, user_id)
            if not user:
                return None
            data = _as_dict(user, USER_FIELDS)
            data["password_hash"] = user.password_hash
            return data

    def list_users(self, org_id: str | None = None, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        stmt = select(User)
        if org_id:
            stmt = stmt.where(User.org_id == org_id)
        stmt = stmt.order_by(User.created_at.desc()).limit(max(1, min(limit, 500))).offset(max(0, offset))
        with session_scope(self.session_factory) as session:
            return [_as_dict(row, USER_FIELDS) for row in session.scalars(stmt).all()]

    def update_user(self, user_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            user = session.get(User, user_id)
            if not user:
                return None
            for field in ("display_name", "role", "org_id", "status"):
                if field in patch:
                    setattr(user, field, patch[field])
            user.updated_at = datetime.now(tz=timezone.utc)
            session.flush()
            return _as_dict(user, USER_FIELDS)

    def update_user_password(self, user_id: str, password_hash: str, *, revoke_existing_sessions: bool = True) -> bool:
        now = datetime.now(tz=timezone.utc)
        with session_scope(self.session_factory) as session:
            user = session.get(User, user_id)
            if not user:
                return False
            user.password_hash = password_hash
            user.updated_at = now
            if revoke_existing_sessions:
                sessions = session.scalars(
                    select(UserSession).where(
                        UserSession.user_id == user_id,
                        UserSession.status == "active",
                        UserSession.revoked_at.is_(None),
                    )
                ).all()
                for row in sessions:
                    row.status = "revoked"
                    row.revoked_at = now
            return True

    def create_user_session(self, user_id: str, token: str, expires_at: datetime) -> dict[str, Any] | None:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        now = datetime.now(tz=timezone.utc)
        with session_scope(self.session_factory) as session:
            user = session.get(User, user_id)
            if not user or user.status != "active":
                return None
            row = UserSession(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            user.last_login_at = now
            user.updated_at = now
            session.add(row)
            session.flush()
            return {
                "session_id": row.session_id,
                "expires_at": row.expires_at,
                "user": _as_dict(user, USER_FIELDS),
            }

    def revoke_user_session(self, token: str) -> bool:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        now = datetime.now(tz=timezone.utc)
        with session_scope(self.session_factory) as session:
            row = session.scalars(
                select(UserSession).where(
                    UserSession.token_hash == token_hash,
                    UserSession.status == "active",
                    UserSession.revoked_at.is_(None),
                )
            ).first()
            if not row:
                return False
            row.status = "revoked"
            row.revoked_at = now
            return True

    def create_user_action_token(self, user_id: str, token: str, purpose: str, expires_at: datetime) -> dict[str, Any] | None:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        with session_scope(self.session_factory) as session:
            if not session.get(User, user_id):
                return None
            row = UserActionToken(
                token_id=str(uuid.uuid4()),
                user_id=user_id,
                token_hash=token_hash,
                purpose=purpose,
                expires_at=expires_at,
            )
            session.add(row)
            session.flush()
            return {
                "token_id": row.token_id,
                "user_id": row.user_id,
                "purpose": row.purpose,
                "expires_at": row.expires_at,
            }

    def consume_user_action_token(self, token: str, purpose: str) -> dict[str, Any] | None:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        now = datetime.now(tz=timezone.utc)
        with session_scope(self.session_factory) as session:
            row = session.scalars(
                select(UserActionToken).where(
                    UserActionToken.token_hash == token_hash,
                    UserActionToken.purpose == purpose,
                    UserActionToken.status == "active",
                    UserActionToken.expires_at > now,
                )
            ).first()
            if not row:
                return None
            user = session.get(User, row.user_id)
            if not user or user.status != "active":
                return None
            row.status = "used"
            row.used_at = now
            return {"user": _as_dict(user, USER_FIELDS), "token_id": row.token_id}

    def get_settings(self) -> dict[str, Any]:
        with session_scope(self.session_factory) as session:
            rows = session.scalars(select(ControlPlaneSetting)).all()
            return {row.setting_key: row.setting_value for row in rows}

    def update_setting(self, key: str, value: dict[str, Any]) -> dict[str, Any]:
        with session_scope(self.session_factory) as session:
            row = session.get(ControlPlaneSetting, key)
            if not row:
                row = ControlPlaneSetting(setting_key=key, setting_value=value)
                session.add(row)
            else:
                row.setting_value = value
                row.updated_at = datetime.now(tz=timezone.utc)
            session.flush()
            return {row.setting_key: row.setting_value}

    def create_org(self, org: dict[str, Any]) -> dict[str, Any]:
        with session_scope(self.session_factory) as session:
            organization = Organization(**org)
            session.add(organization)
            session.flush()
            return _as_dict(organization, ORG_FIELDS)

    def get_org(self, org_id: str) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            org = session.get(Organization, org_id)
            return _as_dict(org, ORG_FIELDS) if org else None

    def list_orgs(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with session_scope(self.session_factory) as session:
            rows = session.scalars(
                select(Organization)
                .order_by(Organization.created_at.desc())
                .limit(max(1, min(limit, 500)))
                .offset(max(0, offset))
            ).all()
            return [_as_dict(row, ORG_FIELDS) for row in rows]

    def update_org(self, org_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            org = session.get(Organization, org_id)
            if not org:
                return None
            for field in ("display_name", "status", "plan_code"):
                if field in patch:
                    setattr(org, field, patch[field])
            org.updated_at = datetime.now(tz=timezone.utc)
            session.flush()
            return _as_dict(org, ORG_FIELDS)

    def create_api_key(
        self,
        *,
        api_key_id: str,
        org_id: str | None,
        cluster_id: str | None,
        key_name: str,
        role: str,
        token: str,
        expires_at: str | None = None,
        rotated_from_api_key_id: str | None = None,
    ) -> dict[str, Any]:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        with session_scope(self.session_factory) as session:
            api_key = ApiKey(
                api_key_id=api_key_id,
                org_id=org_id,
                cluster_id=cluster_id,
                key_name=key_name,
                role=role,
                token_hash=token_hash,
                expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
                rotated_from_api_key_id=rotated_from_api_key_id,
            )
            session.add(api_key)
            session.flush()
            return _as_dict(api_key, API_KEY_FIELDS)

    def list_api_keys(self, org_id: str) -> list[dict[str, Any]]:
        with session_scope(self.session_factory) as session:
            rows = session.scalars(
                select(ApiKey).where(ApiKey.org_id == org_id).order_by(ApiKey.created_at.desc())
            ).all()
            return [_as_dict(row, API_KEY_FIELDS) for row in rows]

    def get_api_key(self, org_id: str, api_key_id: str) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            api_key = session.scalars(
                select(ApiKey).where(ApiKey.org_id == org_id, ApiKey.api_key_id == api_key_id)
            ).first()
            return _as_dict(api_key, API_KEY_FIELDS) if api_key else None

    def revoke_api_key(self, org_id: str, api_key_id: str) -> bool:
        with session_scope(self.session_factory) as session:
            api_key = session.scalars(
                select(ApiKey).where(
                    ApiKey.org_id == org_id,
                    ApiKey.api_key_id == api_key_id,
                    ApiKey.revoked_at.is_(None),
                )
            ).first()
            if not api_key:
                return False
            api_key.status = "revoked"
            api_key.revoked_at = datetime.now(tz=timezone.utc)
            api_key.updated_at = datetime.now(tz=timezone.utc)
            return True

    def create_cluster(self, cluster: dict[str, Any], install_token: str) -> dict[str, Any]:
        install_token_hash = hash_token(install_token, settings.api_key_hash_secret)
        with session_scope(self.session_factory) as session:
            if not session.get(Organization, cluster["org_id"]):
                return {}
            row = Cluster(
                cluster_id=cluster["cluster_id"],
                org_id=cluster["org_id"],
                runtime=cluster["runtime"],
                display_name=cluster["display_name"],
                status="pending",
                install_token_hash=install_token_hash,
            )
            session.add(row)
            session.flush()
            return _as_dict(row, CLUSTER_FIELDS)

    def get_cluster(self, org_id: str, cluster_id: str) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            cluster = session.scalars(
                select(Cluster).where(Cluster.org_id == org_id, Cluster.cluster_id == cluster_id)
            ).first()
            return _as_dict(cluster, CLUSTER_FIELDS) if cluster else None

    def persist_receipt(self, receipt: dict[str, Any]) -> None:
        with session_scope(self.session_factory) as session:
            org = session.get(Organization, receipt["org_id"])
            if not org:
                session.add(Organization(org_id=receipt["org_id"], status="active", plan_code="starter"))

            cluster = session.get(Cluster, receipt["cluster_id"])
            now = datetime.now(tz=timezone.utc)
            if not cluster:
                session.add(
                    Cluster(
                        cluster_id=receipt["cluster_id"],
                        org_id=receipt["org_id"],
                        runtime=receipt.get("runtime", "kubernetes"),
                        status="active",
                        last_seen_at=now,
                    )
                )
            else:
                cluster.status = "active"
                cluster.last_seen_at = now

            namespace_key = {"cluster_id": receipt["cluster_id"], "namespace": receipt["namespace"]}
            if not session.get(Namespace, namespace_key):
                session.add(
                    Namespace(
                        org_id=receipt["org_id"],
                        cluster_id=receipt["cluster_id"],
                        namespace=receipt["namespace"],
                    )
                )

            if not session.get(Policy, receipt["policy_id"]):
                session.add(
                    Policy(
                        policy_id=receipt["policy_id"],
                        org_id=receipt["org_id"],
                        version=receipt.get("schema_version"),
                    )
                )

            if not session.get(TrustReceipt, receipt["receipt_id"]):
                session.add(
                    TrustReceipt(
                        receipt_id=receipt["receipt_id"],
                        org_id=receipt["org_id"],
                        cluster_id=receipt["cluster_id"],
                        namespace=receipt["namespace"],
                        workload_id=receipt["workload_id"],
                        action=receipt["action"],
                        decision=receipt["decision"],
                        reason=receipt.get("reason"),
                        policy_id=receipt["policy_id"],
                        payload_hash=receipt["payload_hash"],
                        authority_token_hash=receipt["authority_token_hash"],
                        signature=receipt["signature"],
                        signature_algorithm=receipt["signature_algorithm"],
                        integrity_classification=receipt.get("integrity_classification"),
                        created_at=datetime.fromisoformat(receipt["created_at"]),
                        expires_at=datetime.fromisoformat(receipt["expires_at"]),
                        latency_ms=receipt.get("latency_ms"),
                        receipt_metadata=receipt,
                    )
                )

            if receipt["decision"] in {"ALLOW", "MODIFY"} and not session.get(ExecutionRequest, receipt["receipt_id"]):
                session.add(
                    ExecutionRequest(
                        execution_id=receipt["receipt_id"],
                        receipt_id=receipt["receipt_id"],
                        org_id=receipt["org_id"],
                        cluster_id=receipt["cluster_id"],
                        namespace=receipt["namespace"],
                        workload_id=receipt["workload_id"],
                        action=receipt["action"],
                        decision=receipt["decision"],
                        payload_hash=receipt["payload_hash"],
                        receipt_metadata=receipt,
                    )
                )

            exists_usage = session.scalars(
                select(UsageMetering).where(UsageMetering.receipt_id == receipt["receipt_id"])
            ).first()
            if not exists_usage:
                session.add(
                    UsageMetering(
                        org_id=receipt["org_id"],
                        cluster_id=receipt["cluster_id"],
                        namespace=receipt["namespace"],
                        receipt_id=receipt["receipt_id"],
                        decision=receipt["decision"],
                        billable=receipt["decision"] == "ALLOW",
                    )
                )

    def load_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            receipt = session.get(TrustReceipt, receipt_id)
            return dict(receipt.receipt_metadata) if receipt else None

    def list_receipts(
        self,
        *,
        org_id: str | None = None,
        cluster_id: str | None = None,
        namespace: str | None = None,
        workload_id: str | None = None,
        decision: str | None = None,
        policy_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        stmt = select(TrustReceipt)
        if org_id:
            stmt = stmt.where(TrustReceipt.org_id == org_id)
        if cluster_id:
            stmt = stmt.where(TrustReceipt.cluster_id == cluster_id)
        if namespace:
            stmt = stmt.where(TrustReceipt.namespace == namespace)
        if workload_id:
            stmt = stmt.where(TrustReceipt.workload_id == workload_id)
        if decision:
            stmt = stmt.where(TrustReceipt.decision == decision.upper())
        if policy_id:
            stmt = stmt.where(TrustReceipt.policy_id == policy_id)
        stmt = stmt.order_by(TrustReceipt.created_at.desc()).limit(max(1, min(limit, 500))).offset(max(0, offset))
        with session_scope(self.session_factory) as session:
            rows = session.scalars(stmt).all()
            return [
                {
                    "receipt_id": row.receipt_id,
                    "org_id": row.org_id,
                    "cluster_id": row.cluster_id,
                    "namespace": row.namespace,
                    "workload_id": row.workload_id,
                    "action": row.action,
                    "decision": row.decision,
                    "reason": row.reason,
                    "policy_id": row.policy_id,
                    "payload_hash": row.payload_hash,
                    "integrity_classification": row.integrity_classification,
                    "created_at": row.created_at,
                    "expires_at": row.expires_at,
                    "latency_ms": row.latency_ms,
                }
                for row in rows
            ]

    def usage_summary(self, org_id: str | None = None) -> dict[str, int]:
        stmt = select(
            func.count(UsageMetering.id).label("total_executions"),
            func.sum(case((UsageMetering.decision == "ALLOW", 1), else_=0)).label("allowed_executions"),
            func.sum(case((UsageMetering.decision == "DENY", 1), else_=0)).label("denied_attempts"),
            func.sum(case((UsageMetering.decision == "MODIFY", 1), else_=0)).label("modified_executions"),
            func.count(distinct(UsageMetering.cluster_id)).label("cluster_count"),
            func.count(distinct(UsageMetering.namespace)).label("namespace_count"),
        )
        if org_id:
            stmt = stmt.where(UsageMetering.org_id == org_id)
        with session_scope(self.session_factory) as session:
            row = session.execute(stmt).one()
            return {
                "total_executions": int(row.total_executions or 0),
                "allowed_executions": int(row.allowed_executions or 0),
                "denied_attempts": int(row.denied_attempts or 0),
                "modified_executions": int(row.modified_executions or 0),
                "cluster_count": int(row.cluster_count or 0),
                "namespace_count": int(row.namespace_count or 0),
            }

    def list_clusters(self, org_id: str | None = None) -> list[dict[str, Any]]:
        stmt = select(Cluster)
        if org_id:
            stmt = stmt.where(Cluster.org_id == org_id)
        stmt = stmt.order_by(Cluster.last_seen_at.desc().nullslast(), Cluster.created_at.desc())
        with session_scope(self.session_factory) as session:
            return [_as_dict(row, CLUSTER_FIELDS) for row in session.scalars(stmt).all()]

    def list_policies(self, org_id: str | None = None) -> list[dict[str, Any]]:
        stmt = select(Policy)
        if org_id:
            stmt = stmt.where(Policy.org_id == org_id)
        stmt = stmt.order_by(Policy.created_at.desc())
        with session_scope(self.session_factory) as session:
            return [
                {
                    "policy_id": row.policy_id,
                    "org_id": row.org_id,
                    "version": row.version,
                    "active": row.active,
                    "created_at": row.created_at,
                }
                for row in session.scalars(stmt).all()
            ]

    def persist_operator_event(self, event: dict[str, Any]) -> None:
        with session_scope(self.session_factory) as session:
            session.add(OperatorEvent(**event))

    def record_heartbeat(self, heartbeat: dict[str, Any]) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            cluster = session.scalars(
                select(Cluster).where(
                    Cluster.org_id == heartbeat["org_id"],
                    Cluster.cluster_id == heartbeat["cluster_id"],
                )
            ).first()
            if not cluster:
                return None
            now = datetime.now(tz=timezone.utc)
            cluster.status = "active"
            cluster.health = heartbeat["health"]
            cluster.operator_version = heartbeat["operator_version"]
            cluster.heartbeat_namespace = heartbeat["namespace"]
            cluster.last_heartbeat_at = now
            cluster.last_seen_at = now
            cluster.updated_at = now
            session.flush()
            return _as_dict(cluster, CLUSTER_FIELDS)

    def list_pending_executions(self, org_id: str, cluster_id: str, limit: int = 25) -> list[dict[str, Any]]:
        with session_scope(self.session_factory) as session:
            rows = session.scalars(
                select(ExecutionRequest)
                .where(
                    ExecutionRequest.org_id == org_id,
                    ExecutionRequest.cluster_id == cluster_id,
                    ExecutionRequest.status == "pending",
                )
                .order_by(ExecutionRequest.created_at.asc())
                .limit(max(1, min(limit, 100)))
            ).all()
            return [_as_dict(row, EXECUTION_FIELDS) for row in rows]

    def update_execution_status(
        self,
        org_id: str,
        cluster_id: str,
        execution_id: str,
        status: str,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> dict[str, Any] | None:
        with session_scope(self.session_factory) as session:
            execution = session.scalars(
                select(ExecutionRequest).where(
                    ExecutionRequest.org_id == org_id,
                    ExecutionRequest.cluster_id == cluster_id,
                    ExecutionRequest.execution_id == execution_id,
                )
            ).first()
            if not execution:
                return None
            now = datetime.now(tz=timezone.utc)
            execution.status = status
            if status in {"claimed", "running"}:
                execution.claimed_at = now
            if status in {"succeeded", "failed", "rejected"}:
                execution.completed_at = now
            execution.error_code = error_code
            execution.error_summary = error_summary
            execution.updated_at = now
            session.flush()
            return _as_dict(execution, EXECUTION_FIELDS)

    def list_plans(self) -> list[dict[str, Any]]:
        with session_scope(self.session_factory) as session:
            rows = session.scalars(select(Plan).order_by(Plan.created_at.asc())).all()
            return [
                {
                    "plan_code": row.plan_code,
                    "display_name": row.display_name,
                    "monthly_execution_limit": row.monthly_execution_limit,
                    "cluster_limit": row.cluster_limit,
                    "namespace_limit": row.namespace_limit,
                    "retention_days": row.retention_days,
                }
                for row in rows
            ]

    def persist_audit_log(self, event: dict[str, Any]) -> None:
        with session_scope(self.session_factory) as session:
            session.add(AuditLog(**event))

    def list_audit_logs(self, org_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        stmt = select(AuditLog)
        if org_id:
            stmt = stmt.where(AuditLog.org_id == org_id)
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(max(1, min(limit, 500)))
        with session_scope(self.session_factory) as session:
            return [
                {
                    "audit_id": row.audit_id,
                    "org_id": row.org_id,
                    "cluster_id": row.cluster_id,
                    "actor_role": row.actor_role,
                    "actor_org_id": row.actor_org_id,
                    "actor_cluster_id": row.actor_cluster_id,
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id,
                    "outcome": row.outcome,
                    "request_id": row.request_id,
                    "created_at": row.created_at,
                }
                for row in session.scalars(stmt).all()
            ]

    def record_failed_auth(self, token_hash: str | None, reason: str, request_id: str | None = None) -> None:
        with session_scope(self.session_factory) as session:
            session.add(FailedAuthEvent(token_hash=token_hash, reason=reason, request_id=request_id))

    def list_operator_events(
        self,
        *,
        org_id: str | None = None,
        cluster_id: str | None = None,
        receipt_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        stmt = select(OperatorEvent)
        if org_id:
            stmt = stmt.where(OperatorEvent.org_id == org_id)
        if cluster_id:
            stmt = stmt.where(OperatorEvent.cluster_id == cluster_id)
        if receipt_id:
            stmt = stmt.where(OperatorEvent.receipt_id == receipt_id)
        stmt = stmt.order_by(OperatorEvent.created_at.desc()).limit(max(1, min(limit, 500)))
        with session_scope(self.session_factory) as session:
            return [
                {
                    "org_id": row.org_id,
                    "receipt_id": row.receipt_id,
                    "cluster_id": row.cluster_id,
                    "namespace": row.namespace,
                    "workload_id": row.workload_id,
                    "enforcement_status": row.enforcement_status,
                    "error_code": row.error_code,
                    "error_summary": row.error_summary,
                    "operator_version": row.operator_version,
                    "created_at": row.created_at,
                }
                for row in session.scalars(stmt).all()
            ]
