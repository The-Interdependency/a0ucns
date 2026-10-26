# ratios: loc_comments=16:52 imports_exports=1:1 calls_definitions=1:0
# === MODULE_BUILD ===
# id: pcta_pkg
#   module_name: pcta
#   module_kind: engine
#   summary: PCTA — circle layer of the layered model; 7 PCNA tensors arranged on a {7/2} heptagram, wrapped in a UCNS structural mirror
#   owner: a0p maintainer
#   public_surface: Circle, CIRCLE_SIZE, HEPTAGRAM_STEP_CIRCLE, heptagram_walk, heptagram_walk_7_2, heptagram_walk_7_3
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcta_circle_holds_seven_holds
#   rollout: default_enabled
#   rollback: revert subpackage from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcta_pkg_boundaries
#   summary: PCTA — circle layer of the layered model; 7 PCNA tensors arranged on a {7/2} heptagram, wrapped in a UCNS structural mirror
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcta_pkg
#   summary: PCTA — circle layer of the layered model; 7 PCNA tensors arranged on a {7/2} heptagram, wrapped in a UCNS structural mirror
#   exposes: Circle, CIRCLE_SIZE, HEPTAGRAM_STEP_CIRCLE, heptagram_walk, heptagram_walk_7_2, heptagram_walk_7_3
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: pcta_circle_holds_seven
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.pcta_circle_holds_seven_holds
# === END CONTRACTS ===
"""PCTA — Prime Circled Tensor Architecture (circle layer of the layered model).

A `Circle` is the second layer of the recursive structure:

    Tensor   (PCNA)  ←  d=53 leaf scalars
    Circle   (PCTA)  ←  this module: 7 tensors + aggregate
    Seed     (PTCA)  ←  7 circles + aggregate
    Core     (ptca.core)  ←  N seeds + aggregate

The circle carries 7 PCNA leaf tensors as payloads AND a UCNS structural
mirror (depth-1, UNIT payloads on each of the 7 positions). The
8th-tensor referent — "all seven together is a tensor" — is computed
on demand by `circle.aggregate()` and is itself a width-53 Tensor.
"""
from .circle import (
    Circle,
    CIRCLE_SIZE,
    HEPTAGRAM_STEP_CIRCLE,
    heptagram_walk,
    heptagram_walk_7_2,
    heptagram_walk_7_3,
)

__all__ = [
    "Circle",
    "CIRCLE_SIZE",
    "HEPTAGRAM_STEP_CIRCLE",
    "heptagram_walk",
    "heptagram_walk_7_2",
    "heptagram_walk_7_3",
]
# ratios: loc_comments=16:52 imports_exports=1:1 calls_definitions=1:0
