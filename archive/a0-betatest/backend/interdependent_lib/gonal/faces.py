# ratios: loc_comments=20:47 imports_exports=1:4 calls_definitions=1:4
# === MODULE_BUILD ===
# id: carrier_faces
#   module_name: faces
#   module_kind: schema
#   summary: face + chirality + adjacency formulas over the 157-gonal carrier; no disk material
#   owner: Erin Spencer
#   public_surface: face, chirality, n_plus, n_minus, ARITY, ORIGIN, UPPER_ARC_RANGE, LOWER_ARC_RANGE
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_face_chirality_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_faces_boundaries
#   summary: face + chirality + adjacency formulas over the 157-gonal carrier; no disk material
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_faces
#   summary: face + chirality + adjacency formulas over the 157-gonal carrier; no disk material
#   exposes: face, chirality, n_plus, n_minus, ARITY, ORIGIN, UPPER_ARC_RANGE, LOWER_ARC_RANGE
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_face_chirality
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_face_chirality_holds
# === END CONTRACTS ===
"""Face, chirality, and adjacency formulas over the 157-gonal carrier."""
from __future__ import annotations

# Public canon constants — arity is the prime; structural anchors are public.
ARITY: int = 157
ORIGIN: int = 0
UPPER_ARC_RANGE: tuple[int, int] = (1, 78)   # inclusive both ends
LOWER_ARC_RANGE: tuple[int, int] = (79, 156)  # inclusive both ends


def face(k: int) -> int:
    """Public face value: +1 for origin + upper arc, -1 for lower arc."""
    k = k % ARITY
    if k == ORIGIN:
        return +1
    if UPPER_ARC_RANGE[0] <= k <= UPPER_ARC_RANGE[1]:
        return +1
    return -1


def chirality(k: int, direction: int) -> int:
    """Neighbor in `direction` (+1 clockwise, -1 counterclockwise) mod 157."""
    if direction not in (+1, -1):
        raise ValueError(f"direction must be +1 or -1; got {direction}")
    return (k + direction) % ARITY


def n_plus(k: int) -> int:
    """Clockwise neighbor."""
    return (k + 1) % ARITY


def n_minus(k: int) -> int:
    """Counterclockwise neighbor."""
    return (k - 1) % ARITY
# ratios: loc_comments=20:47 imports_exports=1:4 calls_definitions=1:4
