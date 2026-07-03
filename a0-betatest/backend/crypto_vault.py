# ratios: loc_comments=19:42 imports_exports=2:3 calls_definitions=8:3
# === MODULE_BUILD ===
# id: a0p_crypto_vault
#   module_name: crypto_vault
#   module_kind: service
#   summary: Fernet encrypt/decrypt + mask for at-rest BYOK credentials
#   owner: a0p maintainer
#   public_surface: encrypt, decrypt, mask
#   internal_surface: _fernet, _SECRET
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove imports from server.py; user re-enters BYOK keys
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: a0p_crypto_vault_boundaries
#   summary: Fernet encrypt/decrypt + mask for at-rest BYOK credentials
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: a0p_crypto_vault
#   summary: Fernet encrypt/decrypt + mask for at-rest BYOK credentials
#   exposes: encrypt, decrypt, mask
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Fernet-encrypted at-rest storage for BYOK keys."""
import os
from cryptography.fernet import Fernet, InvalidToken

_SECRET = os.environ.get("A0P_KEY_VAULT_SECRET")
if not _SECRET:
    raise RuntimeError("A0P_KEY_VAULT_SECRET missing from environment")

_fernet = Fernet(_SECRET.encode("utf-8"))


def encrypt(plain: str) -> str:
    return _fernet.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt(cipher: str) -> str:
    try:
        return _fernet.decrypt(cipher.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("invalid encrypted token") from e


def mask(plain: str) -> str:
    if not plain:
        return ""
    if len(plain) <= 8:
        return "*" * len(plain)
    return f"{plain[:4]}...{plain[-4:]}"

# === CONTRACTS ===
# id: a0p_crypto_vault_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=19:42 imports_exports=2:3 calls_definitions=8:3
