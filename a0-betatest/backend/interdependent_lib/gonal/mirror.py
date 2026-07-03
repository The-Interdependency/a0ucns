# ratios: loc_comments=10:50 imports_exports=1:2 calls_definitions=4:1
# === MODULE_BUILD ===
# id: carrier_mirror
#   module_name: mirror
#   module_kind: engine
#   summary: position-reflection mirror of a gonal arrangement across the diameter through position 0 — an involution (mirror_of(mirror_of(x)) == x) that inverts upper and lower arcs while preserving every hard adjacency invariant (no L-L / N-N adjacency survives the reflection)
#   owner: Erin Spencer
#   public_surface: mirror_of
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.gonal_mirror_is_invariant_preserving_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_mirror_boundaries
#   summary: pure function
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_mirror
#   summary: position-reflection across the diameter through position 0
#   exposes: mirror_of
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""Position-reflection mirror of a gonal arrangement.

mirror[0] = arr[0]
mirror[k] = arr[(n - k) mod n]   for k > 0

Properties:
  - involution: mirror_of(mirror_of(x)) == x
  - hard-invariant preserving: no L-L adjacent → no L-L adjacent (adjacency walked backwards)
  - face-inverting: upper arc becomes lower arc and vice versa
"""
from __future__ import annotations


def mirror_of(arr: list[str]) -> list[str]:
    """Return the position-reflection mirror of `arr` across position 0."""
    n = len(arr)
    if n == 0:
        return []
    out = [arr[0]]
    for k in range(1, n):
        out.append(arr[(n - k) % n])
    return out


__all__ = ["mirror_of"]

# === CONTRACTS ===
# id: carrier_mirror_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=10:50 imports_exports=1:2 calls_definitions=4:1
