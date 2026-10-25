"""Ed25519 signing service — generates/loads vault keys, signs/verifies JWS."""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption,
    load_pem_private_key,
)
import jwt

from app.core.config import settings

_KID = "key-2026-10-a"
_PRIVATE_KEY: Ed25519PrivateKey | None = None
_PUBLIC_KEY_PEM: bytes | None = None


def _vault_dir() -> Path:
    p = Path(settings.VAULT_DIR)
    if not p.is_absolute():
        # Resolve relative to backend dir
        p = Path(__file__).parent.parent.parent / settings.VAULT_DIR.lstrip("./")
    return p


def _ensure_keys() -> tuple[Ed25519PrivateKey, bytes]:
    global _PRIVATE_KEY, _PUBLIC_KEY_PEM
    if _PRIVATE_KEY is not None:
        return _PRIVATE_KEY, _PUBLIC_KEY_PEM  # type: ignore[return-value]

    vault = _vault_dir()
    vault.mkdir(parents=True, exist_ok=True)
    priv_path = vault / f"{_KID}.pem"
    pub_path = vault / f"{_KID}.pub.pem"

    if priv_path.exists():
        with open(priv_path, "rb") as f:
            _PRIVATE_KEY = load_pem_private_key(f.read(), password=None)
    else:
        _PRIVATE_KEY = Ed25519PrivateKey.generate()
        with open(priv_path, "wb") as f:
            f.write(_PRIVATE_KEY.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))

    pub_pem = _PRIVATE_KEY.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    if not pub_path.exists():
        with open(pub_path, "wb") as f:
            f.write(pub_pem)

    _PUBLIC_KEY_PEM = pub_pem
    return _PRIVATE_KEY, pub_pem


def sign_credential(claims: dict) -> str:
    """Sign a dict of claims with Ed25519 and return a compact JWS string."""
    private_key, _ = _ensure_keys()
    payload = claims.copy()
    payload["kid"] = _KID
    return jwt.encode(payload, private_key, algorithm="EdDSA", headers={"kid": _KID})


def verify_credential(token: str) -> dict:
    """Verify an EdDSA JWS and return claims. Raises jwt.InvalidTokenError on failure."""
    _, pub_pem = _ensure_keys()
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    public_key = load_pem_public_key(pub_pem)
    return jwt.decode(token, public_key, algorithms=["EdDSA"])
