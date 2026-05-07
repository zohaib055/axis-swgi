from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class SWGIConfig:
    org_id: str
    node_id: str
    policy_id: str = "policy.v1.default"
    schema_version: str = "v1.0"
    strict_mode: bool = True

    @classmethod
    def from_env(cls) -> "SWGIConfig":
        return cls(
            org_id=os.getenv("SWGI_ORG_ID", "default-org"),
            node_id=os.getenv("SWGI_NODE_ID", "default-node"),
            policy_id=os.getenv("SWGI_POLICY_ID", "policy.v1.default"),
            schema_version=os.getenv("SWGI_SCHEMA_VERSION", "v1.0"),
            strict_mode=(os.getenv("SWGI_STRICT_MODE", "true").lower() == "true"),
        )


_REQUIRED_SIGNING_ENV = "SWGI_SIGNING_PRIVATE_KEY_PEM"


def get_signing_private_key_pem() -> str:
    key = os.getenv(_REQUIRED_SIGNING_ENV)
    if not key:
        raise ValueError(
            f"Missing required env var: {_REQUIRED_SIGNING_ENV}. "
            "Generate an Ed25519 keypair and set the private key PEM."
        )
    return key
