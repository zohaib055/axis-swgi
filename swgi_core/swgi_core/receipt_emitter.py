from __future__ import annotations

import hashlib
import json
from typing import Any

from .config import SWGIConfig
from .models import EvaluationInput, EvaluationResult, TrustReceipt
from .signature import load_private_key, sign_bytes


class ReceiptEmitter:
    def __init__(self, config: SWGIConfig, signing_private_key_pem: str) -> None:
        self._config = config
        self._signing_key = load_private_key(signing_private_key_pem)

    def emit(self, payload: EvaluationInput, decision: EvaluationResult) -> TrustReceipt:
        receipt_id = TrustReceipt.new_receipt_id()
        timestamp = TrustReceipt.now_utc_iso()

        payload_hash = self._hash_payload(
            {
                "intent": payload.intent,
                "context": payload.context,
                "action": payload.action,
                "authority": payload.authority,
                "workload_id": payload.workload_id,
                "result": decision.result.value,
                "reason": decision.reason,
            }
        )
        authority_token_hash = self._hash_token(payload.authority.get("token"))

        signable = {
            "receipt_id": receipt_id,
            "schema_version": self._config.schema_version,
            "org_id": self._config.org_id,
            "node_id": self._config.node_id,
            "timestamp": timestamp,
            "action": payload.action,
            "workload_id": payload.workload_id,
            "policy_id": self._config.policy_id,
            "result": decision.result.value,
            "reason": decision.reason,
            "payload_hash": payload_hash,
            "authority_token_hash": authority_token_hash,
            "integrity_classification": decision.integrity_classification,
        }
        signature = sign_bytes(self._signing_key, self._canonical_json(signable))

        return TrustReceipt(
            receipt_id=receipt_id,
            schema_version=self._config.schema_version,
            org_id=self._config.org_id,
            node_id=self._config.node_id,
            timestamp=timestamp,
            action=payload.action,
            workload_id=payload.workload_id,
            policy_id=self._config.policy_id,
            result=decision.result.value,
            reason=decision.reason,
            payload_hash=payload_hash,
            authority_token_hash=authority_token_hash,
            integrity_classification=decision.integrity_classification,
            signature=signature,
        )

    @staticmethod
    def _canonical_json(value: dict[str, Any]) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _hash_payload(self, value: dict[str, Any]) -> str:
        return hashlib.sha256(self._canonical_json(value)).hexdigest()

    @staticmethod
    def _hash_token(token: Any) -> str:
        normalized = str(token or "")
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
