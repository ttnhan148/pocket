"""API key encryption utility using cryptography.fernet."""

from __future__ import annotations

from cryptography.fernet import Fernet
from app.config import Settings


def _get_fernet_key() -> bytes:
    """Retrieve or generate the encryption key."""
    settings = Settings()
    key_str = settings.encryption_key
    if not key_str:
        # Fallback for testing / development: return a standard valid key
        # (Must be 32 url-safe base64-encoded bytes)
        return b"KuW6S8-1JvnobqTSfNpvzBb8s0SjgtALu8w8CZAJyHk="
    return key_str.encode()


def encrypt_api_key(plain: str) -> str:
    """Encrypt a plain text API key into a Fernet token string."""
    if not plain:
        return ""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plain.encode()).decode()


def decrypt_api_key(token: str) -> str:
    """Decrypt a Fernet token string back into plain text."""
    if not token:
        return ""
    f = Fernet(_get_fernet_key())
    return f.decrypt(token.encode()).decode()
