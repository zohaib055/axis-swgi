from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .config import settings
from .db_url import normalize_psycopg_dsn
from .migrations import run_migrations
from .security import hash_token


class CommandCenterStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = normalize_psycopg_dsn(dsn)

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(
            self.dsn,
            row_factory=dict_row,
            connect_timeout=settings.db_connect_timeout_seconds,
        )

    def initialize(self) -> None:
        run_migrations(self.dsn)

    def health_check(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() is not None

    def resolve_api_key(self, token: str) -> dict[str, Any] | None:
        token_hash = hash_token(token, settings.api_key_hash_secret)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT api_key_id, org_id, cluster_id, key_name, role
                    FROM api_keys
                    WHERE token_hash = %s
                      AND status = 'active'
                      AND revoked_at IS NULL
                      AND (expires_at IS NULL OR expires_at > NOW())
                    """,
                    (token_hash,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute("UPDATE api_keys SET last_used_at = NOW() WHERE api_key_id = %s", (row["api_key_id"],))
            conn.commit()
            return dict(row)

    def create_org(self, org: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO organizations (org_id, display_name, status, plan_code)
                    VALUES (%(org_id)s, %(display_name)s, %(status)s, %(plan_code)s)
                    RETURNING org_id, display_name, status, plan_code, created_at, updated_at
                    """,
                    org,
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row)

    def get_org(self, org_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT org_id, display_name, status, plan_code, created_at, updated_at
                    FROM organizations
                    WHERE org_id = %s
                    """,
                    (org_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_orgs(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT org_id, display_name, status, plan_code, created_at, updated_at
                    FROM organizations
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (max(1, min(limit, 500)), max(0, offset)),
                )
                return [dict(row) for row in cur.fetchall()]

    def update_org(self, org_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_org(org_id)
        if not current:
            return None
        values = {
            "org_id": org_id,
            "display_name": patch.get("display_name", current.get("display_name")),
            "status": patch.get("status", current.get("status")),
            "plan_code": patch.get("plan_code", current.get("plan_code")),
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE organizations
                    SET display_name = %(display_name)s,
                        status = %(status)s,
                        plan_code = %(plan_code)s,
                        updated_at = NOW()
                    WHERE org_id = %(org_id)s
                    RETURNING org_id, display_name, status, plan_code, created_at, updated_at
                    """,
                    values,
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None

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
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO api_keys (
                        api_key_id, org_id, cluster_id, key_name, role, token_hash,
                        expires_at, rotated_from_api_key_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING api_key_id, org_id, cluster_id, key_name, role, status,
                              created_at, expires_at, last_used_at, revoked_at
                    """,
                    (
                        api_key_id,
                        org_id,
                        cluster_id,
                        key_name,
                        role,
                        token_hash,
                        expires_at,
                        rotated_from_api_key_id,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row)

    def list_api_keys(self, org_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT api_key_id, org_id, cluster_id, key_name, role, status,
                           created_at, expires_at, last_used_at, revoked_at
                    FROM api_keys
                    WHERE org_id = %s
                    ORDER BY created_at DESC
                    """,
                    (org_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def get_api_key(self, org_id: str, api_key_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT api_key_id, org_id, cluster_id, key_name, role, status,
                           created_at, expires_at, last_used_at, revoked_at
                    FROM api_keys
                    WHERE org_id = %s AND api_key_id = %s
                    """,
                    (org_id, api_key_id),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def revoke_api_key(self, org_id: str, api_key_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE api_keys
                    SET status = 'revoked', revoked_at = NOW()
                    WHERE org_id = %s AND api_key_id = %s AND revoked_at IS NULL
                    """,
                    (org_id, api_key_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
            return updated

    def rotate_api_key(self, org_id: str, api_key_id: str, token: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT org_id, cluster_id, key_name, role
                    FROM api_keys
                    WHERE org_id = %s AND api_key_id = %s AND revoked_at IS NULL
                    """,
                    (org_id, api_key_id),
                )
                old = cur.fetchone()
                if not old:
                    return None
                cur.execute(
                    """
                    UPDATE api_keys
                    SET status = 'rotated', revoked_at = NOW(), updated_at = NOW()
                    WHERE api_key_id = %s
                    """,
                    (api_key_id,),
                )
                new_key = self.create_api_key(
                    api_key_id=f"{api_key_id}-r",
                    org_id=old["org_id"],
                    cluster_id=old["cluster_id"],
                    key_name=f"{old['key_name']} rotated",
                    role=old["role"],
                    token=token,
                    rotated_from_api_key_id=api_key_id,
                )
            conn.commit()
            return new_key

    def create_cluster(self, cluster: dict[str, Any], install_token: str) -> dict[str, Any]:
        install_token_hash = hash_token(install_token, settings.api_key_hash_secret)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT org_id FROM organizations WHERE org_id = %s", (cluster["org_id"],))
                if not cur.fetchone():
                    return {}
                cur.execute(
                    """
                    INSERT INTO clusters (
                        cluster_id, org_id, runtime, display_name, status, install_token_hash
                    ) VALUES (
                        %(cluster_id)s, %(org_id)s, %(runtime)s, %(display_name)s, 'pending', %(install_token_hash)s
                    )
                    RETURNING cluster_id, org_id, runtime, display_name, status, created_at,
                              last_seen_at, health, operator_version, heartbeat_namespace,
                              last_heartbeat_at, updated_at
                    """,
                    {**cluster, "install_token_hash": install_token_hash},
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else {}

    def get_cluster(self, org_id: str, cluster_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT cluster_id, org_id, runtime, display_name, status, created_at,
                           last_seen_at, health, operator_version, heartbeat_namespace,
                           last_heartbeat_at, updated_at
                    FROM clusters
                    WHERE org_id = %s AND cluster_id = %s
                    """,
                    (org_id, cluster_id),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def persist_receipt(self, receipt: dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO organizations (org_id, status, plan_code)
                    VALUES (%s, 'active', 'starter')
                    ON CONFLICT DO NOTHING
                    """,
                    (receipt["org_id"],),
                )
                cur.execute(
                    """
                    INSERT INTO clusters (cluster_id, org_id, runtime, last_seen_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (cluster_id) DO UPDATE SET last_seen_at = NOW(), status = 'active'
                    """,
                    (receipt["cluster_id"], receipt["org_id"], receipt.get("runtime", "kubernetes")),
                )
                cur.execute(
                    """
                    INSERT INTO namespaces (org_id, cluster_id, namespace)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (receipt["org_id"], receipt["cluster_id"], receipt["namespace"]),
                )
                cur.execute(
                    """
                    INSERT INTO policies (policy_id, org_id, version)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (receipt["policy_id"], receipt["org_id"], receipt.get("schema_version")),
                )
                cur.execute(
                    """
                    INSERT INTO trust_receipts (
                        receipt_id, org_id, cluster_id, namespace, workload_id, action, decision,
                        reason, policy_id, payload_hash, authority_token_hash, signature,
                        signature_algorithm, integrity_classification, created_at, expires_at,
                        latency_ms, receipt_metadata
                    ) VALUES (
                        %(receipt_id)s, %(org_id)s, %(cluster_id)s, %(namespace)s, %(workload_id)s,
                        %(action)s, %(decision)s, %(reason)s, %(policy_id)s, %(payload_hash)s,
                        %(authority_token_hash)s, %(signature)s, %(signature_algorithm)s,
                        %(integrity_classification)s, %(created_at)s, %(expires_at)s,
                        %(latency_ms)s, %(receipt_metadata)s::jsonb
                    )
                    ON CONFLICT (receipt_id) DO NOTHING
                    """,
                    {
                        **receipt,
                        "receipt_metadata": json.dumps(receipt, separators=(",", ":"), ensure_ascii=False),
                    },
                )
                if receipt["decision"] in {"ALLOW", "MODIFY"}:
                    cur.execute(
                        """
                        INSERT INTO execution_requests (
                            execution_id, receipt_id, org_id, cluster_id, namespace,
                            workload_id, action, decision, payload_hash, receipt_metadata
                        ) VALUES (
                            %(execution_id)s, %(receipt_id)s, %(org_id)s, %(cluster_id)s,
                            %(namespace)s, %(workload_id)s, %(action)s, %(decision)s,
                            %(payload_hash)s, %(receipt_metadata)s::jsonb
                        )
                        ON CONFLICT (execution_id) DO NOTHING
                        """,
                        {
                            **receipt,
                            "execution_id": receipt["receipt_id"],
                            "receipt_metadata": json.dumps(receipt, separators=(",", ":"), ensure_ascii=False),
                        },
                    )
                cur.execute(
                    """
                    INSERT INTO usage_metering (org_id, cluster_id, namespace, receipt_id, decision, billable)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        receipt["org_id"],
                        receipt["cluster_id"],
                        receipt["namespace"],
                        receipt["receipt_id"],
                        receipt["decision"],
                        receipt["decision"] == "ALLOW",
                    ),
                )
            conn.commit()

    def load_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT receipt_metadata FROM trust_receipts WHERE receipt_id = %s", (receipt_id,))
                row = cur.fetchone()
                if not row:
                    return None
                value = row["receipt_metadata"]
                return json.loads(value) if isinstance(value, str) else dict(value)

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
        where: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("org_id", org_id),
            ("cluster_id", cluster_id),
            ("namespace", namespace),
            ("workload_id", workload_id),
            ("decision", decision.upper() if decision else None),
            ("policy_id", policy_id),
        ):
            if value:
                where.append(f"{column} = %s")
                params.append(value)
        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        sql = f"""
            SELECT receipt_id, org_id, cluster_id, namespace, workload_id, action, decision,
                   reason, policy_id, payload_hash, integrity_classification, created_at,
                   expires_at, latency_ms
            FROM trust_receipts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    def usage_summary(self, org_id: str | None = None) -> dict[str, int]:
        where = "WHERE org_id = %s" if org_id else ""
        params = [org_id] if org_id else []
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        COUNT(*)::int AS total_executions,
                        COUNT(*) FILTER (WHERE decision = 'ALLOW')::int AS allowed_executions,
                        COUNT(*) FILTER (WHERE decision = 'DENY')::int AS denied_attempts,
                        COUNT(*) FILTER (WHERE decision = 'MODIFY')::int AS modified_executions,
                        COUNT(DISTINCT cluster_id)::int AS cluster_count,
                        COUNT(DISTINCT namespace)::int AS namespace_count
                    FROM usage_metering
                    {where}
                    """,
                    params,
                )
                row = cur.fetchone() or {}
                return {
                    "total_executions": row.get("total_executions", 0),
                    "allowed_executions": row.get("allowed_executions", 0),
                    "denied_attempts": row.get("denied_attempts", 0),
                    "modified_executions": row.get("modified_executions", 0),
                    "cluster_count": row.get("cluster_count", 0),
                    "namespace_count": row.get("namespace_count", 0),
                }

    def list_clusters(self, org_id: str | None = None) -> list[dict[str, Any]]:
        where = "WHERE org_id = %s" if org_id else ""
        params = [org_id] if org_id else []
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT cluster_id, org_id, runtime, display_name, status, created_at,
                           last_seen_at, health, operator_version, heartbeat_namespace,
                           last_heartbeat_at, updated_at
                    FROM clusters
                    {where}
                    ORDER BY last_seen_at DESC NULLS LAST, created_at DESC
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def list_policies(self, org_id: str | None = None) -> list[dict[str, Any]]:
        where = "WHERE org_id = %s" if org_id else ""
        params = [org_id] if org_id else []
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT policy_id, org_id, version, active, created_at FROM policies {where} ORDER BY created_at DESC",
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def persist_operator_event(self, event: dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO operator_events (
                        org_id, receipt_id, cluster_id, namespace, workload_id, enforcement_status,
                        error_code, error_summary, operator_version
                    ) VALUES (
                        %(org_id)s, %(receipt_id)s, %(cluster_id)s, %(namespace)s, %(workload_id)s,
                        %(enforcement_status)s, %(error_code)s, %(error_summary)s,
                        %(operator_version)s
                    )
                    """,
                    event,
                )
            conn.commit()

    def record_heartbeat(self, heartbeat: dict[str, Any]) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE clusters
                    SET status = 'active',
                        health = %(health)s,
                        operator_version = %(operator_version)s,
                        heartbeat_namespace = %(namespace)s,
                        last_heartbeat_at = NOW(),
                        last_seen_at = NOW(),
                        updated_at = NOW()
                    WHERE org_id = %(org_id)s AND cluster_id = %(cluster_id)s
                    RETURNING cluster_id, org_id, runtime, display_name, status, created_at,
                              last_seen_at, health, operator_version, heartbeat_namespace,
                              last_heartbeat_at, updated_at
                    """,
                    heartbeat,
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None

    def list_pending_executions(self, org_id: str, cluster_id: str, limit: int = 25) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT execution_id, receipt_id, org_id, cluster_id, namespace, workload_id,
                           action, decision, payload_hash, receipt_metadata, status, claimed_at,
                           completed_at, error_code, error_summary, created_at, updated_at
                    FROM execution_requests
                    WHERE org_id = %s
                      AND cluster_id = %s
                      AND status = 'pending'
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (org_id, cluster_id, max(1, min(limit, 100))),
                )
                return [dict(row) for row in cur.fetchall()]

    def update_execution_status(
        self,
        org_id: str,
        cluster_id: str,
        execution_id: str,
        status: str,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> dict[str, Any] | None:
        claimed_expr = "NOW()" if status in {"claimed", "running"} else "claimed_at"
        completed_expr = "NOW()" if status in {"succeeded", "failed", "rejected"} else "completed_at"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE execution_requests
                    SET status = %s,
                        claimed_at = {claimed_expr},
                        completed_at = {completed_expr},
                        error_code = %s,
                        error_summary = %s,
                        updated_at = NOW()
                    WHERE org_id = %s
                      AND cluster_id = %s
                      AND execution_id = %s
                    RETURNING execution_id, receipt_id, org_id, cluster_id, namespace, workload_id,
                              action, decision, payload_hash, receipt_metadata, status, claimed_at,
                              completed_at, error_code, error_summary, created_at, updated_at
                    """,
                    (status, error_code, error_summary, org_id, cluster_id, execution_id),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None

    def list_plans(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT plan_code, display_name, monthly_execution_limit, cluster_limit,
                           namespace_limit, retention_days
                    FROM plans
                    ORDER BY created_at ASC
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def persist_audit_log(self, event: dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_logs (
                        org_id, cluster_id, actor_role, actor_org_id, actor_cluster_id,
                        action, resource_type, resource_id, outcome, request_id
                    ) VALUES (
                        %(org_id)s, %(cluster_id)s, %(actor_role)s, %(actor_org_id)s,
                        %(actor_cluster_id)s, %(action)s, %(resource_type)s, %(resource_id)s,
                        %(outcome)s, %(request_id)s
                    )
                    """,
                    event,
                )
            conn.commit()

    def list_audit_logs(self, org_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        where = "WHERE org_id = %s" if org_id else ""
        params: list[Any] = [org_id] if org_id else []
        params.append(max(1, min(limit, 500)))
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT audit_id, org_id, cluster_id, actor_role, actor_org_id,
                           actor_cluster_id, action, resource_type, resource_id,
                           outcome, request_id, created_at
                    FROM audit_logs
                    {where}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]

    def record_failed_auth(self, token_hash: str | None, reason: str, request_id: str | None = None) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO failed_auth_events (token_hash, reason, request_id)
                    VALUES (%s, %s, %s)
                    """,
                    (token_hash, reason, request_id),
                )
            conn.commit()

    def list_operator_events(
        self,
        *,
        org_id: str | None = None,
        cluster_id: str | None = None,
        receipt_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if org_id:
            where.append("org_id = %s")
            params.append(org_id)
        if cluster_id:
            where.append("cluster_id = %s")
            params.append(cluster_id)
        if receipt_id:
            where.append("receipt_id = %s")
            params.append(receipt_id)
        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        params.append(max(1, min(limit, 500)))
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT org_id, receipt_id, cluster_id, namespace, workload_id, enforcement_status,
                           error_code, error_summary, operator_version, created_at
                    FROM operator_events
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]
