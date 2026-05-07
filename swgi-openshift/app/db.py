from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from .config import settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    workload_id TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    result TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    latency_ms DOUBLE PRECISION,
    integrity_classification TEXT,
    reason TEXT,
    schema_version TEXT,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_receipts_org_id ON receipts(org_id);
CREATE INDEX IF NOT EXISTS idx_receipts_node_id ON receipts(node_id);
CREATE INDEX IF NOT EXISTS idx_receipts_timestamp ON receipts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_receipts_policy_id ON receipts(policy_id);
CREATE INDEX IF NOT EXISTS idx_receipts_result ON receipts(result);
"""


class ReceiptStore(Protocol):
    def initialize(self) -> None: ...
    def persist(self, receipt: dict[str, Any]) -> None: ...
    def load(self, receipt_id: str) -> dict[str, Any] | None: ...
    def list_receipts(
        self,
        *,
        org_id: str | None = None,
        node_id: str | None = None,
        result: str | None = None,
        policy_id: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]: ...
    def export_csv(
        self,
        *,
        org_id: str | None = None,
        node_id: str | None = None,
        result: str | None = None,
        policy_id: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
    ) -> str: ...


class ReceiptStorePostgres:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(
            self.dsn,
            row_factory=dict_row,
            connect_timeout=settings.db_connect_timeout_seconds,
        )

    def initialize(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()

    def persist(self, receipt: dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO receipts (
                        receipt_id, org_id, node_id, timestamp, workload_id, policy_id, result,
                        payload_hash, latency_ms, integrity_classification, reason, schema_version, raw_json
                    ) VALUES (
                        %(receipt_id)s, %(org_id)s, %(node_id)s, %(timestamp)s, %(workload_id)s,
                        %(policy_id)s, %(result)s, %(payload_hash)s, %(latency_ms)s,
                        %(integrity_classification)s, %(reason)s, %(schema_version)s, %(raw_json)s::jsonb
                    )
                    ON CONFLICT (receipt_id) DO NOTHING
                    """,
                    {
                        "receipt_id": receipt["receipt_id"],
                        "org_id": receipt["org_id"],
                        "node_id": receipt["node_id"],
                        "timestamp": receipt["timestamp"],
                        "workload_id": receipt.get("workload_id", "unknown"),
                        "policy_id": receipt["policy_id"],
                        "result": receipt["result"],
                        "payload_hash": receipt["payload_hash"],
                        "latency_ms": receipt.get("latency_ms"),
                        "integrity_classification": receipt.get("integrity_classification"),
                        "reason": receipt.get("reason"),
                        "schema_version": receipt.get("schema_version"),
                        "raw_json": json.dumps(receipt, separators=(",", ":"), ensure_ascii=False),
                    },
                )
            conn.commit()

    def load(self, receipt_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT raw_json FROM receipts WHERE receipt_id = %s", (receipt_id,))
                row = cur.fetchone()
                if not row:
                    return None
                raw_json = row["raw_json"]
                if isinstance(raw_json, str):
                    return json.loads(raw_json)
                return dict(raw_json)

    def list_receipts(
        self,
        *,
        org_id: str | None = None,
        node_id: str | None = None,
        result: str | None = None,
        policy_id: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if org_id:
            where.append("org_id = %s")
            params.append(org_id)
        if node_id:
            where.append("node_id = %s")
            params.append(node_id)
        if result:
            where.append("result = %s")
            params.append(result.upper())
        if policy_id:
            where.append("policy_id = %s")
            params.append(policy_id)
        if start_ts:
            where.append('"timestamp" >= %s')
            params.append(start_ts)
        if end_ts:
            where.append('"timestamp" < %s')
            params.append(end_ts)

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        sql = f"""
            SELECT receipt_id, org_id, node_id, timestamp, workload_id, policy_id, result,
                   payload_hash, latency_ms, integrity_classification
            FROM receipts
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    def export_csv(
        self,
        *,
        org_id: str | None = None,
        node_id: str | None = None,
        result: str | None = None,
        policy_id: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
    ) -> str:
        rows = self.list_receipts(
            org_id=org_id,
            node_id=node_id,
            result=result,
            policy_id=policy_id,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=500,
            offset=0,
        )
        header = (
            "receipt_id,org_id,node_id,timestamp,workload_id,policy_id,result,payload_hash,"
            "integrity_classification,latency_ms"
        )
        out = [header]
        for row in rows:
            values: list[str] = []
            for col in (
                "receipt_id",
                "org_id",
                "node_id",
                "timestamp",
                "workload_id",
                "policy_id",
                "result",
                "payload_hash",
                "integrity_classification",
                "latency_ms",
            ):
                value = "" if row[col] is None else str(row[col])
                escaped = value.replace('"', '""')
                values.append(f'"{escaped}"')
            out.append(",".join(values))
        return "\n".join(out) + "\n"


class ReceiptStoreSQLite:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id TEXT PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    workload_id TEXT NOT NULL,
                    policy_id TEXT NOT NULL,
                    result TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    latency_ms REAL,
                    integrity_classification TEXT,
                    reason TEXT,
                    schema_version TEXT,
                    raw_json TEXT NOT NULL,
                    created_at_epoch_ms INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_org_id ON receipts(org_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_node_id ON receipts(node_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_timestamp ON receipts(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_policy_id ON receipts(policy_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_result ON receipts(result)")
            conn.commit()

    def persist(self, receipt: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO receipts (
                    receipt_id, org_id, node_id, timestamp, workload_id, policy_id, result,
                    payload_hash, latency_ms, integrity_classification, reason, schema_version, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt["receipt_id"],
                    receipt["org_id"],
                    receipt["node_id"],
                    receipt["timestamp"],
                    receipt.get("workload_id", "unknown"),
                    receipt["policy_id"],
                    receipt["result"],
                    receipt["payload_hash"],
                    receipt.get("latency_ms"),
                    receipt.get("integrity_classification"),
                    receipt.get("reason"),
                    receipt.get("schema_version"),
                    json.dumps(receipt, separators=(",", ":"), ensure_ascii=False),
                ),
            )
            conn.commit()

    def load(self, receipt_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT raw_json FROM receipts WHERE receipt_id = ?", (receipt_id,)).fetchone()
            if not row:
                return None
            return json.loads(str(row["raw_json"]))

    def list_receipts(
        self,
        *,
        org_id: str | None = None,
        node_id: str | None = None,
        result: str | None = None,
        policy_id: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if org_id:
            where.append("org_id = ?")
            params.append(org_id)
        if node_id:
            where.append("node_id = ?")
            params.append(node_id)
        if result:
            where.append("result = ?")
            params.append(result.upper())
        if policy_id:
            where.append("policy_id = ?")
            params.append(policy_id)
        if start_ts:
            where.append("timestamp >= ?")
            params.append(start_ts)
        if end_ts:
            where.append("timestamp < ?")
            params.append(end_ts)

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        sql = (
            "SELECT receipt_id, org_id, node_id, timestamp, workload_id, policy_id, result, "
            "payload_hash, latency_ms, integrity_classification "
            f"FROM receipts {where_clause} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        )
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def export_csv(
        self,
        *,
        org_id: str | None = None,
        node_id: str | None = None,
        result: str | None = None,
        policy_id: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
    ) -> str:
        rows = self.list_receipts(
            org_id=org_id,
            node_id=node_id,
            result=result,
            policy_id=policy_id,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=500,
            offset=0,
        )
        header = (
            "receipt_id,org_id,node_id,timestamp,workload_id,policy_id,result,payload_hash,"
            "integrity_classification,latency_ms"
        )
        out = [header]
        for row in rows:
            values: list[str] = []
            for col in (
                "receipt_id",
                "org_id",
                "node_id",
                "timestamp",
                "workload_id",
                "policy_id",
                "result",
                "payload_hash",
                "integrity_classification",
                "latency_ms",
            ):
                value = "" if row[col] is None else str(row[col])
                escaped = value.replace('"', '""')
                values.append(f'"{escaped}"')
            out.append(",".join(values))
        return "\n".join(out) + "\n"


def get_receipt_store() -> tuple[ReceiptStore, str]:
    if settings.receipt_store_backend == "postgres":
        return ReceiptStorePostgres(settings.database_url), "postgres"
    return ReceiptStoreSQLite(settings.receipt_db_path), "sqlite"
