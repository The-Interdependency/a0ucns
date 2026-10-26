# ratios: loc_comments=32:44 imports_exports=2:2 calls_definitions=15:3
# === MODULE_BUILD ===
# id: pcea_cipher
#   module_name: cipher
#   module_kind: engine
#   summary: PCEA core cipher — prime-circular bijective encrypt/decrypt where each state element is recoded in bijective base-p (p the i-th of the first 53 primes) and circularly shifted by key digits derived from the previous state, so the transform is keyed entirely by last_state and is exactly invertible
#   owner: a0p maintainer
#   public_surface: encrypt_state, decrypt_state
#   internal_surface: _shift
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcea_round_trip_53
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcea_cipher_boundaries
#   summary: prime-circular bijective encrypt/decrypt over a previous-state key
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcea_cipher
#   summary: prime-circular bijective encrypt/decrypt over a previous-state key
#   exposes: encrypt_state, decrypt_state
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: pcea_round_trip_53
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.pcea_round_trip_53
# === END CONTRACTS ===
"""PCEA core cipher."""
from .primes import PRIME_CIRCLE
from .codec import to_bijective, from_bijective, key_digits


def _shift(digits: list[int], keys: list[int], p: int, sign: int) -> list[int]:
    out = []
    for j, d in enumerate(digits):
        k = keys[j] if j < len(keys) else 1
        # shift in {1..p} space: ((d - 1 + sign*(k-1)) mod p) + 1
        out.append(((d - 1 + sign * (k - 1)) % p) + 1)
    return out


def encrypt_state(state: list[int], last_state: list[int]) -> list[int]:
    """Encrypt state[i] using last_state[i % L] as the keying material."""
    if not last_state:
        last_state = [1]
    L = len(last_state)
    enc: list[int] = []
    for i, v in enumerate(state):
        p = PRIME_CIRCLE[i % 53]
        digits = to_bijective(int(v), p)
        keys = key_digits(int(last_state[i % L]), p, len(digits))
        shifted = _shift(digits, keys, p, sign=+1)
        enc.append(from_bijective(shifted, p))
    return enc


def decrypt_state(enc: list[int], last_state: list[int]) -> list[int]:
    if not last_state:
        last_state = [1]
    L = len(last_state)
    out: list[int] = []
    for i, v in enumerate(enc):
        p = PRIME_CIRCLE[i % 53]
        digits = to_bijective(int(v), p)
        keys = key_digits(int(last_state[i % L]), p, len(digits))
        unshifted = _shift(digits, keys, p, sign=-1)
        out.append(from_bijective(unshifted, p))
    return out
# ratios: loc_comments=32:44 imports_exports=2:2 calls_definitions=15:3
