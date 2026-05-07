from __future__ import annotations

import json
from typing import Any

from .models import Decision, EvaluationInput, EvaluationResult


class PolicyEngine:
    """
    Deterministic policy gate with bounded logic.

    The default policy is intentionally conservative:
    - Deny if authority token is missing.
    - Deny if action or workload is blocked in context.
    - Allow otherwise.
    """

    def __init__(
        self,
        policy_id: str = "policy.v1.default",
        default: str = "DENY",
        rules: list[dict[str, Any]] | None = None,
        integrity_labels: dict[str, str] | None = None,
    ) -> None:
        self.policy_id = policy_id
        self.default = default.upper()
        self.rules = rules or []
        self.integrity_labels = integrity_labels or {
            "ALLOW": "HIGH",
            "DENY": "LOW",
        }

    @classmethod
    def from_file(cls, path: str) -> "PolicyEngine":
        with open(path, "r", encoding="utf-8") as handle:
            policy = json.load(handle)
        return cls(
            policy_id=policy.get("policy_id", "policy.v1.default"),
            default=policy.get("default", "DENY"),
            rules=policy.get("rules", []),
            integrity_labels=policy.get("integrity_labels", {}),
        )

    def evaluate(self, payload: EvaluationInput) -> EvaluationResult:
        # If explicit rules exist, evaluate against the static rule set first.
        if self.rules:
            decision = self._evaluate_rules(payload)
            if decision:
                return decision

            if self.default == "ALLOW":
                return EvaluationResult(
                    result=Decision.ALLOW,
                    reason="default_allow",
                    integrity_classification=self._integrity("ALLOW"),
                )
            return EvaluationResult(
                result=Decision.DENY,
                reason="default_deny",
                integrity_classification=self._integrity("DENY"),
            )

        # Backward-compatible fallback policy.
        authority_token = str(payload.authority.get("token", "")).strip()
        blocked_actions = set(self._safe_list(payload.context.get("blocked_actions", [])))
        blocked_workloads = set(self._safe_list(payload.context.get("blocked_workloads", [])))

        if not authority_token:
            return EvaluationResult(
                result=Decision.DENY,
                reason="missing_authority_token",
                integrity_classification="LOW",
            )

        if payload.action in blocked_actions:
            return EvaluationResult(
                result=Decision.DENY,
                reason="action_blocked_by_policy",
                integrity_classification="HIGH",
            )

        if payload.workload_id in blocked_workloads:
            return EvaluationResult(
                result=Decision.DENY,
                reason="workload_blocked_by_policy",
                integrity_classification="HIGH",
            )

        return EvaluationResult(
            result=Decision.ALLOW,
            reason="authorized",
            integrity_classification="HIGH",
        )

    def _evaluate_rules(self, payload: EvaluationInput) -> EvaluationResult | None:
        for rule in self.rules:
            if str(rule.get("action", "")).strip() != payload.action:
                continue

            mode = str(rule.get("intent", "")).strip().upper()
            if mode == "DENY_ALWAYS":
                return EvaluationResult(
                    result=Decision.DENY,
                    reason="policy_deny_always",
                    integrity_classification=self._integrity("DENY"),
                )

            if mode == "ALLOW_IF":
                allow_if = rule.get("allow_if", {}) or {}
                roles = set(self._safe_list(allow_if.get("authority_role_in", [])))
                if roles:
                    role = str(payload.authority.get("role", "")).strip()
                    if role in roles:
                        return EvaluationResult(
                            result=Decision.ALLOW,
                            reason="policy_allow_role_match",
                            integrity_classification=self._integrity("ALLOW"),
                        )
                    return EvaluationResult(
                        result=Decision.DENY,
                        reason="policy_deny_role_mismatch",
                        integrity_classification=self._integrity("DENY"),
                    )

                if allow_if.get("authority_token_present") is True:
                    token = str(payload.authority.get("token", "")).strip()
                    if token:
                        return EvaluationResult(
                            result=Decision.ALLOW,
                            reason="policy_allow_token_present",
                            integrity_classification=self._integrity("ALLOW"),
                        )
                    return EvaluationResult(
                        result=Decision.DENY,
                        reason="policy_deny_token_missing",
                        integrity_classification=self._integrity("DENY"),
                    )
        return None

    def _integrity(self, decision: str) -> str:
        configured = self.integrity_labels.get(decision, "")
        if not configured:
            return "HIGH" if decision == "ALLOW" else "LOW"
        upper = configured.upper()
        if upper in {"HIGH", "LOW", "MEDIUM", "UNVERIFIED", "PENDING_REVALIDATION"}:
            return upper
        if decision == "ALLOW":
            return "HIGH"
        return "LOW"

    @staticmethod
    def _safe_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        return []
