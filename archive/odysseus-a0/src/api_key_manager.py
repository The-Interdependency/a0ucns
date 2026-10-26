# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 57:49
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 30:8
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: api_key_manager
#   module_name: api_key_manager
#   module_kind: hmmm
#   summary: hmmm
#   owner: hmmm
#   public_surface: APIKeyManager
#   internal_surface: none
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: api_key_manager_boundaries
#   summary: hmmm
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: api_key_manager
#   summary: hmmm
#   exposes: APIKeyManager
# === END CAPABILITIES ===
import os
import json
import logging
from typing import Dict
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

class APIKeyManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.api_keys_file = os.path.join(data_dir, "api_keys.json")
        self.key_file = os.path.join(data_dir, ".key")
        
    def get_or_create_key(self) -> bytes:
        """Get or create encryption key for API keys"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key"""
        if not api_key:
            return ""
        f = Fernet(self.get_or_create_key())
        return f.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key"""
        if not encrypted_key:
            return ""
        f = Fernet(self.get_or_create_key())
        return f.decrypt(encrypted_key.encode()).decode()
    
    def _load_raw(self) -> Dict[str, str]:
        """Load the raw, still-encrypted keys dict from disk.

        Tolerates a missing/corrupt/wrong-shaped file by returning {} — the
        same robustness load() relies on at startup.
        """
        if not os.path.exists(self.api_keys_file):
            return {}
        try:
            with open(self.api_keys_file, 'r', encoding="utf-8") as f:
                encrypted_keys = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # A corrupt/truncated api_keys.json must not crash load() (called on
            # startup via app_initializer) — treat it as no stored keys.
            logger.warning("Failed to read API keys file: %s", e)
            return {}
        if not isinstance(encrypted_keys, dict):
            # Legacy/wrong shape (e.g. a list) — .items() would raise. Ignore it.
            logger.warning("API keys file has unexpected shape (%s); ignoring", type(encrypted_keys).__name__)
            return {}
        return encrypted_keys

    def save(self, provider: str, api_key: str):
        """Save encrypted API key to file.

        Operates on the raw (still-encrypted) on-disk dict so other providers'
        keys stay encrypted. Loading via load() first would decrypt them and
        write them back as plaintext, which then fails to decrypt on the next
        load() and silently drops those providers.
        """
        keys = self._load_raw()
        keys[provider] = self.encrypt_api_key(api_key)
        with open(self.api_keys_file, 'w', encoding="utf-8") as f:
            json.dump(keys, f)

    def load(self) -> Dict[str, str]:
        """Load and decrypt API keys"""
        encrypted_keys = self._load_raw()
        decrypted = {}
        for provider, key in encrypted_keys.items():
            try:
                decrypted[provider] = self.decrypt_api_key(key)
            except (InvalidToken, ValueError) as e:
                logger.warning("Failed to decrypt API key for %s: %s", provider, e)
        return decrypted

# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 57:49
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 30:8
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
