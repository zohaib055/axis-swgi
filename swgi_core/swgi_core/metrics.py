from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SWGIMetrics:
    authorize_total: int = 0
    allow_total: int = 0
    deny_total: int = 0

    def record(self, result: str) -> None:
        self.authorize_total += 1
        if result == "ALLOW":
            self.allow_total += 1
        else:
            self.deny_total += 1

    def to_dict(self) -> dict[str, int]:
        return {
            "swgi_authorize_total": self.authorize_total,
            "swgi_allow_total": self.allow_total,
            "swgi_deny_total": self.deny_total,
        }
