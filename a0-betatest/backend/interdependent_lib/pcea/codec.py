# ratios: loc_comments=27:48 imports_exports=0:3 calls_definitions=7:3
# === MODULE_BUILD ===
# id: pcea_codec
#   module_name: codec
#   module_kind: engine
#   summary: bijective base-p codec — encodes an integer into digits drawn from {1..p} (the bijective numeration that has no leading-zero ambiguity) and back, plus the key-digit stream PCEA shifts by; this is the reversible number representation the cipher operates on
#   owner: a0p maintainer
#   public_surface: to_bijective, from_bijective, key_digits
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcea_codec_boundaries
#   summary: bijective base-p codec — digits in {1..p}, plus standard key-digit stream
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcea_codec
#   summary: bijective base-p codec — digits in {1..p}, plus standard key-digit stream
#   exposes: to_bijective, from_bijective, key_digits
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Bijective base-p codec — digits in {1..p}, not {0..p-1}."""


# === CONTRACTS ===
# id: pcea_codec_round_trip
#   given: state of arbitrary non-negative integers and a shared seed
#   then: decrypt(encrypt(state)) == state with the same last_state
#   class: correctness
#   call: a0p_skills.contracts.pcea_round_trip_53
# === END CONTRACTS ===


def to_bijective(n: int, p: int) -> list[int]:
    """Decompose non-negative int n into bijective base-p digits (lsb first).

    Bijective convention: n=0 has the empty representation. Every other n
    has a unique non-empty digit string with digits in {1..p}.
    """
    if n < 0:
        raise ValueError("bijective codec requires non-negative input")
    if n == 0:
        return []
    digits: list[int] = []
    x = n
    while x > 0:
        x, r = divmod(x - 1, p)
        digits.append(r + 1)
    return digits


def from_bijective(digits: list[int], p: int) -> int:
    """Reconstruct an int from bijective base-p digits (lsb first)."""
    n = 0
    mult = 1
    for d in digits:
        if d < 1 or d > p:
            raise ValueError(f"digit {d} out of range for bijective base {p}")
        n += d * mult
        mult *= p
    return n


def key_digits(value: int, p: int, length: int) -> list[int]:
    """Standard base-p digits of value as a key stream of `length` digits (lsb first)."""
    out = []
    v = max(value, 0)
    for _ in range(length):
        out.append((v % p) + 1)  # shifted into {1..p} for additive use
        v //= p
    return out
# ratios: loc_comments=27:48 imports_exports=0:3 calls_definitions=7:3
