# ratios: loc_comments=27:18 imports_exports=2:4 calls_definitions=8:4
"""Symmetric encryption for user-supplied secrets (BYOK provider keys).

Provider keys must not be persisted in plaintext: a DB dump, backup, or
read-only access would otherwise expose usable secrets. Values are stored as
``enc:v1:<fernet-token>``; the ``enc:v1:`` prefix lets legacy plaintext values
remain readable during migration and get replaced with ciphertext the next
time the user sets a key.

Encryption requires ``API_KEY_ENCRYPTION_KEY`` (a urlsafe base64-encoded
32-byte Fernet key, e.g. ``Fernet.generate_key()``). When it is unset,
encryption is unavailable and callers must refuse to store a new secret rather
than write plaintext.
"""
from __future__ import annotations

import os

from cryptography.fernet import Fernet

_PREFIX = "enc:v1:"


class SecretDecryptionError(RuntimeError):
    """A stored ciphertext could not be decrypted (missing/rotated/invalid key).

    Callers should convert this into a structured error for the caller (e.g. an
    ``[ERROR]`` stream chunk or a failed verification) rather than falling back
    to a shared key or letting it surface as an unhandled 500.
    """


def _fernet() -> Fernet | None:
    key = os.environ.get("API_KEY_ENCRYPTION_KEY")
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encryption_available() -> bool:
    """True when API_KEY_ENCRYPTION_KEY is configured and usable."""
    try:
        return _fernet() is not None
    except Exception:
        return False


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a plaintext secret, returning an ``enc:v1:``-prefixed token."""
    f = _fernet()
    if f is None:
        raise RuntimeError("API_KEY_ENCRYPTION_KEY is not configured; refusing to store secret")
    return _PREFIX + f.encrypt(plaintext.encode()).decode()


def decrypt_secret(value: str) -> str:
    """Decrypt a stored secret. Non-prefixed (legacy plaintext) values and empty
    values are returned unchanged so existing records keep working."""
    if not value or not value.startswith(_PREFIX):
        return value
    try:
        f = _fernet()
    except Exception as exc:
        # Malformed API_KEY_ENCRYPTION_KEY (wrong length/encoding) makes
        # Fernet(...) raise before we can decrypt; surface it as a decryption
        # error so callers produce a structured response, not a 500.
        raise SecretDecryptionError("API_KEY_ENCRYPTION_KEY is invalid; cannot decrypt stored secret") from exc
    if f is None:
        raise SecretDecryptionError("API_KEY_ENCRYPTION_KEY is not configured; cannot decrypt stored secret")
    try:
        return f.decrypt(value[len(_PREFIX):].encode()).decode()
    except Exception as exc:
        raise SecretDecryptionError("stored secret could not be decrypted (wrong API_KEY_ENCRYPTION_KEY?)") from exc
# ratios: loc_comments=27:18 imports_exports=2:4 calls_definitions=8:4
