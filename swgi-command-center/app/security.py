from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_api_token(prefix: str = "swgi") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_token(token: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)
