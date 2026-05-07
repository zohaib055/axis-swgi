from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def load_private_key(pem: str) -> Ed25519PrivateKey:
    pem = _normalize_pem(pem)
    key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("Provided private key is not Ed25519")
    return key


def load_public_key(pem: str) -> Ed25519PublicKey:
    pem = _normalize_pem(pem)
    key = serialization.load_pem_public_key(pem.encode("utf-8"))
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("Provided public key is not Ed25519")
    return key


def sign_bytes(private_key: Ed25519PrivateKey, payload: bytes) -> str:
    signature = private_key.sign(payload)
    return base64.b64encode(signature).decode("utf-8")


def verify_bytes(public_key: Ed25519PublicKey, payload: bytes, signature_b64: str) -> bool:
    try:
        public_key.verify(base64.b64decode(signature_b64), payload)
        return True
    except Exception:
        return False


def export_public_key_pem(private_key: Ed25519PrivateKey) -> str:
    public_key = private_key.public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def generate_private_key_pem() -> str:
    private_key = Ed25519PrivateKey.generate()
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _normalize_pem(pem: str) -> str:
    # Supports .env single-line values with escaped newlines.
    pem = pem.strip().strip("'").strip('"')
    if "\\n" in pem:
        pem = pem.replace("\\n", "\n")
    return pem
