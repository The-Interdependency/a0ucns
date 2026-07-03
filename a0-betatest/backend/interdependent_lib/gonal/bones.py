# ratios: loc_comments=6:47 imports_exports=3:1 calls_definitions=2:1
# === MODULE_BUILD ===
# id: carrier_bones
#   module_name: bones
#   module_kind: engine
#   summary: face-crossing detection over a bone's constituent positions; measurable structural property, not a violation
#   owner: Erin Spencer
#   public_surface: face_crossing
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_face_crossing_bone_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_bones_boundaries
#   summary: face-crossing detection over a bone's constituent positions; measurable structural property, not a violation
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_bones
#   summary: face-crossing detection over a bone's constituent positions; measurable structural property, not a violation
#   exposes: face_crossing
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_face_crossing_bone
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_face_crossing_bone_holds
# === END CONTRACTS ===
"""Bone face-crossing detection over the carrier."""
from __future__ import annotations
from collections.abc import Iterable
from .faces import face


def face_crossing(constituent_positions: Iterable[int]) -> bool:
    """True iff the bone's constituents span both face +1 and face -1.

    Per the public canon spec: face-crossing is a measurable bone property,
    not a violation. Use this to classify a bone as pure-structural,
    pure-connective, or face-crossing.
    """
    faces = {face(int(k)) for k in constituent_positions}
    return len(faces) > 1
# ratios: loc_comments=6:47 imports_exports=3:1 calls_definitions=2:1
