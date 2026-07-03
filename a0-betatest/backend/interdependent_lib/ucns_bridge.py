# ratios: loc_comments=55:79 imports_exports=4:9 calls_definitions=16:8
# === MODULE_BUILD ===
# id: ucns_bridge
#   module_name: ucns_bridge
#   module_kind: adapter
#   summary: thin A0-safe wrapper around the ucns package — will route through ucns.a0_safe when v1.0 ships on PyPI
#   owner: a0p maintainer
#   public_surface: is_unit, multiply, left_quotient, right_quotient, object_record, describe, seq_prime_safe, UNIT, UCNSObject, lcm, has_a0_safe_facade
#   internal_surface: _A0_SAFE_AVAILABLE
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ucns_bridge_unit_holds
#   rollout: default_enabled
#   rollback: remove module and call sites
#   ucns_version_pin: 0.8.3
#   unresolved: switch to `from ucns import a0_safe` when PyPI publishes v1.0
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ucns_bridge_boundaries
#   summary: thin A0-safe wrapper around the ucns package — will route through ucns.a0_safe when v1.0 ships on PyPI
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ucns_bridge
#   summary: thin A0-safe wrapper around the ucns package — will route through ucns.a0_safe when v1.0 ships on PyPI
#   exposes: is_unit, multiply, object_record, describe, seq_prime_safe, UNIT, has_a0_safe_facade
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""A0-safe bridge to the ucns package.

The upstream `ucns` v1.0 ships an `a0_safe` submodule with the inspection
facade. PyPI 0.8.3 (current pin) exposes the underlying functions but
not the submodule. This bridge gives a0p one stable import surface that
will switch transparently to `ucns.a0_safe.*` when PyPI catches up.

Per the upstream A0 rule:
  - SEQ-PRIME is only absolute inside `ucns.VERIFIED_DOMAIN_LABELS`.
  - A0-facing consumers should consult `domain_status_metadata` and
    treat SEQ-PRIME outside verified domains as non-absolute.
"""
from __future__ import annotations
import ucns

# === CONTRACTS ===
# id: ucns_bridge_unit_consistency
#   given: bridge.UNIT and bridge.is_unit
#   then: is_unit(UNIT) is True and the unit identity has the canonical ucns shape
#   class: correctness
#   call: a0p_skills.contracts.ucns_bridge_unit_holds
# === END CONTRACTS ===

# Try to use the canonical A0-safe facade if upstream is new enough.
try:
    from ucns import a0_safe as _a0_safe  # type: ignore[attr-defined]
    _A0_SAFE_AVAILABLE = True
except ImportError:
    _a0_safe = None
    _A0_SAFE_AVAILABLE = False


# UCNS "unit" identity — payload-None per upstream canon.
UNIT = None

# Re-export the core algebraic object + scalar lcm so consumers (the morphology
# depth-ladder) construct carriers and read carrier widths through one surface.
UCNSObject = ucns.UCNSObject
from ucns_recursive.canonical import lcm


def has_a0_safe_facade() -> bool:
    """Did the installed ucns version ship the a0_safe submodule?"""
    return _A0_SAFE_AVAILABLE


def is_unit(obj) -> bool:
    """UCNS unit predicate."""
    if obj is None:
        return True
    return bool(ucns.is_unit(obj))


def multiply(a, b):
    """UCNS multiplication. Pure structural composition, non-differentiable.

    This is the carrier-LCM operator ⊠ (the runtime shadow of the Lean
    `multiplyFuel` / `carrier_lcm_law`): nMin(A⊠B) divides lcm(nMin A, nMin B).
    """
    return ucns.multiply(a, b)


def left_quotient(p, a):
    """Constructive left quotient: B such that A ⊠ B ≡_seq P (None if none).

    Recoverability of this inverse is the `multiply_left_cancellative`
    guarantee — DEFENDED in prose, NOT yet machine-verified (a `sorry`-stub
    in `ucns/formal/Ucns/Core.lean`). Callers in the morphology decomposition
    path stay gated behind that proof.
    """
    return ucns.left_quotient(p, a)


def right_quotient(p, b):
    """Constructive right quotient: A such that A ⊠ B ≡_seq P (None if none)."""
    return ucns.right_quotient(p, b)


def object_record(obj) -> dict | None:
    """A0-safe inspection record — identity, depth, canonical hash, etc.

    Returns None if the installed ucns version can't produce one.
    """
    if _A0_SAFE_AVAILABLE and hasattr(_a0_safe, "object_record"):
        return _a0_safe.object_record(obj)
    if hasattr(ucns, "object_record"):
        return ucns.object_record(obj)
    return None


def describe(obj) -> str:
    """Human-readable description; safe to log."""
    if _A0_SAFE_AVAILABLE and hasattr(_a0_safe, "describe"):
        return str(_a0_safe.describe(obj))
    return repr(obj)


def seq_prime_safe(obj, domain_label: str) -> bool | None:
    """Return SEQ-PRIME truth value ONLY when domain_label is verified.

    Returns None for unverified domains — callers must not treat None
    as False; it means "not absolute in this scope."
    """
    if not isinstance(domain_label, str) or not domain_label:
        return None
    verified = getattr(ucns, "VERIFIED_DOMAIN_LABELS", frozenset())
    if domain_label not in verified:
        return None
    if hasattr(ucns, "seq_prime_requires_scope"):
        return bool(ucns.seq_prime_requires_scope(obj, domain_label))
    # Conservative fallback: any unhandled case is non-absolute
    return None


__all__ = [
    "UNIT",
    "UCNSObject",
    "lcm",
    "is_unit",
    "multiply",
    "left_quotient",
    "right_quotient",
    "object_record",
    "describe",
    "seq_prime_safe",
    "has_a0_safe_facade",
]
# ratios: loc_comments=55:79 imports_exports=4:9 calls_definitions=16:8
