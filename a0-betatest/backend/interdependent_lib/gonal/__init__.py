# ratios: loc_comments=14:51 imports_exports=6:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: carrier_pkg
#   module_name: carrier
#   module_kind: engine
#   summary: 157-gonal carrier — public structural invariants (face, chirality, class tags, adjacency, bones); private disk material loaded only via theta_microkernel
#   owner: Erin Spencer
#   public_surface: face, chirality, n_plus, n_minus, ClassTag, CarrierDisk, CarrierDiskUnavailable, hard_invariant_holds, face_crossing, build_public_fixture_disk
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_pkg_exports_holds
#   rollout: default_enabled
#   rollback: revert subpackage from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_pkg_boundaries
#   summary: 157-gonal carrier — public structural invariants (face, chirality, class tags, adjacency, bones); private disk material loaded only via theta_microkernel
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_pkg
#   summary: 157-gonal carrier — public structural invariants (face, chirality, class tags, adjacency, bones); private disk material loaded only via theta_microkernel
#   exposes: face, chirality, n_plus, n_minus, ClassTag, CarrierDisk, CarrierDiskUnavailable, hard_invariant_holds, face_crossing, build_public_fixture_disk
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_pkg_exports
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_pkg_exports_holds
# === END CONTRACTS ===
"""157-gonal carrier — public invariants only.

This package exposes the carrier's PUBLIC structure: face values,
chirality, type-class enumeration, adjacency formulas, and bone
face-crossing detection. It also includes the PUBLIC FIXTURE
generator (binary-order rule) for testing.

The CANONICAL disk arrangement is private key material. It is never
constructed by code in this package, never committed to source, and
is loaded only by `interdependent_lib.network.theta_microkernel` from
an external private path.
"""
from .faces import face, chirality, n_plus, n_minus, ARITY, ORIGIN
from .classes import ClassTag, FACE_PLUS_CLASSES, FACE_MINUS_CLASSES
from .disk_protocol import CarrierDisk, CarrierDiskUnavailable
from .adjacency import hard_invariant_holds, find_L_L_violations, find_N_N_violations
from .bones import face_crossing
from .public_fixture import build_public_fixture_disk

__all__ = [
    "face", "chirality", "n_plus", "n_minus", "ARITY", "ORIGIN",
    "ClassTag", "FACE_PLUS_CLASSES", "FACE_MINUS_CLASSES",
    "CarrierDisk", "CarrierDiskUnavailable",
    "hard_invariant_holds", "find_L_L_violations", "find_N_N_violations",
    "face_crossing",
    "build_public_fixture_disk",
]
# ratios: loc_comments=14:51 imports_exports=6:1 calls_definitions=0:0
