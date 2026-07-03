# ratios: loc_comments=18:45 imports_exports=4:3 calls_definitions=7:3
# === MODULE_BUILD ===
# id: carrier_adjacency
#   module_name: adjacency
#   module_kind: engine
#   summary: hard invariants on the carrier — no L-L adjacent, no N-N adjacent; works against any CarrierDisk implementation
#   owner: Erin Spencer
#   public_surface: hard_invariant_holds, find_L_L_violations, find_N_N_violations
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_adjacency_hard_invariant_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_adjacency_boundaries
#   summary: hard invariants on the carrier — no L-L adjacent, no N-N adjacent; works against any CarrierDisk implementation
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_adjacency
#   summary: hard invariants on the carrier — no L-L adjacent, no N-N adjacent; works against any CarrierDisk implementation
#   exposes: hard_invariant_holds, find_L_L_violations, find_N_N_violations
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_adjacency_hard_invariant
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_adjacency_hard_invariant_holds
# === END CONTRACTS ===
"""Hard-invariant checks against any CarrierDisk."""
from __future__ import annotations
from .classes import ClassTag, LITERAL_TYPES
from .disk_protocol import CarrierDisk
from .faces import ARITY, n_plus


def find_L_L_violations(disk: CarrierDisk) -> list[tuple[int, int]]:
    """Return all (k, k+1 mod 157) pairs where both are L."""
    out: list[tuple[int, int]] = []
    for k in range(ARITY):
        if disk.class_at(k) == ClassTag.L and disk.class_at(n_plus(k)) == ClassTag.L:
            out.append((k, n_plus(k)))
    return out


def find_N_N_violations(disk: CarrierDisk) -> list[tuple[int, int]]:
    """Return all (k, k+1 mod 157) pairs where both are N."""
    out: list[tuple[int, int]] = []
    for k in range(ARITY):
        if disk.class_at(k) == ClassTag.N and disk.class_at(n_plus(k)) == ClassTag.N:
            out.append((k, n_plus(k)))
    return out


def hard_invariant_holds(disk: CarrierDisk) -> bool:
    """True iff no L-L adjacencies AND no N-N adjacencies anywhere on the disk."""
    return not find_L_L_violations(disk) and not find_N_N_violations(disk)
# ratios: loc_comments=18:45 imports_exports=4:3 calls_definitions=7:3
