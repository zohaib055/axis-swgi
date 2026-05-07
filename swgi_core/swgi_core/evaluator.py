from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .config import SWGIConfig, get_signing_private_key_pem
from .metrics import SWGIMetrics
from .models import EvaluationInput
from .policy_engine import PolicyEngine
from .receipt_emitter import ReceiptEmitter


class SWGIEnforcementNode:
    """
    Single integration surface for host systems.

    evaluate(intent, context, action, ...) -> (ALLOW|DENY, receipt)
    """

    def __init__(
        self,
        config: SWGIConfig | None = None,
        signing_private_key_pem: str | None = None,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        self.config = config or SWGIConfig.from_env()
        private_key = signing_private_key_pem or get_signing_private_key_pem()

        self.policy_engine = policy_engine or PolicyEngine(policy_id=self.config.policy_id)
        self.receipt_emitter = ReceiptEmitter(config=self.config, signing_private_key_pem=private_key)
        self.metrics = SWGIMetrics()

    def evaluate(
        self,
        intent: str,
        context: dict[str, Any],
        action: str,
        authority: dict[str, Any] | None = None,
        workload_id: str = "unknown",
    ) -> tuple[str, dict[str, Any]]:
        payload = EvaluationInput(
            intent=intent,
            context=context,
            action=action,
            authority=authority or {},
            workload_id=workload_id,
        )

        decision = self.policy_engine.evaluate(payload)
        receipt = self.receipt_emitter.emit(payload, decision)

        self.metrics.record(decision.result.value)
        return decision.result.value, asdict(receipt)


def evaluate(
    intent: str,
    context: dict[str, Any],
    action: str,
    authority: dict[str, Any] | None = None,
    workload_id: str = "unknown",
    node: SWGIEnforcementNode | None = None,
) -> tuple[str, dict[str, Any]]:
    runtime_node = node or SWGIEnforcementNode()
    return runtime_node.evaluate(
        intent=intent,
        context=context,
        action=action,
        authority=authority,
        workload_id=workload_id,
    )
