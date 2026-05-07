from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(slots=True)
class EvaluationInput:
    intent: str
    context: dict[str, Any]
    action: str
    authority: dict[str, Any] = field(default_factory=dict)
    workload_id: str = "unknown"


@dataclass(slots=True)
class EvaluationResult:
    result: Decision
    reason: str
    integrity_classification: str


@dataclass(slots=True)
class TrustReceipt:
    receipt_id: str
    schema_version: str
    org_id: str
    node_id: str
    timestamp: str
    action: str
    workload_id: str
    policy_id: str
    result: str
    reason: str
    payload_hash: str
    authority_token_hash: str
    integrity_classification: str
    signature: str

    @staticmethod
    def new_receipt_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.now(tz=timezone.utc).isoformat()
