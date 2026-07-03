# 20:14
"""
theta_gate — capability-gated view of a UCNSObject.

Granted capability → full object returned.
Ungrouped/missing capability → class-only view (anchors and faces cleared).

hmmm: capability taxonomy not yet defined.
      Current allowlist is empty — all capabilities ungrouped by default
      until taxonomy is pinned.
"""
from __future__ import annotations

try:
    from ucns_v04 import UCNSObject
    _EDCMBONE_AVAILABLE = True
except ImportError:
    _EDCMBONE_AVAILABLE = False

# hmmm: capability allowlist not yet specified.
_GRANTED_CAPABILITIES: frozenset[str] = frozenset()


def gate(obj, capability: str) -> object:
    """
    Return a capability-filtered view of obj.

    If capability is in the granted set: return full obj.
    Otherwise: return class-only view with anchors_pos=() and faces_pos=().
    """
    if not _EDCMBONE_AVAILABLE:
        raise RuntimeError(
            "edcmbone not importable. Resolve edcmbone issue #46."
        )
    if capability in _GRANTED_CAPABILITIES:
        return obj
    return UCNSObject(
        n_dec=obj.n_dec,
        n_min=obj.n_min,
        anchors_pos=(),
        faces_pos=(),
    )
# 20:14
