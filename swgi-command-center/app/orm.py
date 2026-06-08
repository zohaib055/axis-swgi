from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Organization(Base):
    __tablename__ = "organizations"

    org_id: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="active")
    plan_code: Mapped[str] = mapped_column(Text, default="starter")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Cluster(Base):
    __tablename__ = "clusters"

    cluster_id: Mapped[str] = mapped_column(Text, primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    runtime: Mapped[str] = mapped_column(Text, default="kubernetes")
    display_name: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending")
    install_token_hash: Mapped[str | None] = mapped_column(Text)
    heartbeat_namespace: Mapped[str | None] = mapped_column(Text)
    health: Mapped[str | None] = mapped_column(Text)
    operator_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_seen_at: Mapped[datetime | None]
    last_heartbeat_at: Mapped[datetime | None]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Namespace(Base):
    __tablename__ = "namespaces"

    cluster_id: Mapped[str] = mapped_column(ForeignKey("clusters.cluster_id"), primary_key=True)
    namespace: Mapped[str] = mapped_column(Text, primary_key=True)
    org_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Policy(Base):
    __tablename__ = "policies"

    policy_id: Mapped[str] = mapped_column(Text, primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    version: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class TrustReceipt(Base):
    __tablename__ = "trust_receipts"

    receipt_id: Mapped[str] = mapped_column(Text, primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    cluster_id: Mapped[str] = mapped_column(Text, nullable=False)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)
    workload_id: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    policy_id: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(Text, nullable=False)
    authority_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(Text, default="ed25519")
    integrity_classification: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    latency_ms: Mapped[float | None] = mapped_column(Float)
    receipt_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class UsageMetering(Base):
    __tablename__ = "usage_metering"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    cluster_id: Mapped[str] = mapped_column(Text, nullable=False)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_id: Mapped[str] = mapped_column(ForeignKey("trust_receipts.receipt_id"), nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    billable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class OperatorEvent(Base):
    __tablename__ = "operator_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.org_id"))
    receipt_id: Mapped[str] = mapped_column(Text, nullable=False)
    cluster_id: Mapped[str] = mapped_column(Text, nullable=False)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)
    workload_id: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement_status: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_summary: Mapped[str | None] = mapped_column(Text)
    operator_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class BillingPeriod(Base):
    __tablename__ = "billing_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    period_start: Mapped[datetime]
    period_end: Mapped[datetime]
    plan_code: Mapped[str] = mapped_column(Text, nullable=False)
    execution_limit: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"

    api_key_id: Mapped[str] = mapped_column(Text, primary_key=True)
    org_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.org_id"))
    cluster_id: Mapped[str | None] = mapped_column(ForeignKey("clusters.cluster_id"))
    key_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(Text, default="active")
    expires_at: Mapped[datetime | None]
    rotated_from_api_key_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_used_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    org_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.org_id"))
    status: Mapped[str] = mapped_column(Text, default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login_at: Mapped[datetime | None]


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(Text, default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]


class Plan(Base):
    __tablename__ = "plans"

    plan_code: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    monthly_execution_limit: Mapped[int | None] = mapped_column(Integer)
    cluster_limit: Mapped[int | None] = mapped_column(Integer)
    namespace_limit: Mapped[int | None] = mapped_column(Integer)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ExecutionRequest(Base):
    __tablename__ = "execution_requests"

    execution_id: Mapped[str] = mapped_column(Text, primary_key=True)
    receipt_id: Mapped[str] = mapped_column(ForeignKey("trust_receipts.receipt_id"), nullable=False)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("clusters.cluster_id"), nullable=False)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)
    workload_id: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="pending")
    claimed_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    error_code: Mapped[str | None] = mapped_column(Text)
    error_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str | None] = mapped_column(Text)
    cluster_id: Mapped[str | None] = mapped_column(Text)
    actor_role: Mapped[str] = mapped_column(Text, nullable=False)
    actor_org_id: Mapped[str | None] = mapped_column(Text)
    actor_cluster_id: Mapped[str | None] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class FailedAuthEvent(Base):
    __tablename__ = "failed_auth_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
