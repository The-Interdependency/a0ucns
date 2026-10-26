# ratios: loc_comments=11:52 imports_exports=2:1 calls_definitions=4:1
# === MODULE_BUILD ===
# id: carrier_classes
#   module_name: classes
#   module_kind: schema
#   summary: public type-class enumeration (L literal, N aggregate, P, X) for the 157 carrier slots — the distinction between literal-type positions and aggregate-slot positions that the adjacency and face invariants are defined over
#   owner: Erin Spencer
#   public_surface: ClassTag, FACE_PLUS_CLASSES, FACE_MINUS_CLASSES, LITERAL_TYPES, AGGREGATE_SLOTS
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_class_tags_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_classes_boundaries
#   summary: public type-class enumeration (L, N, P, X) for the carrier slots; literal-type vs aggregate-slot distinction
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_classes
#   summary: public type-class enumeration (L, N, P, X) for the carrier slots; literal-type vs aggregate-slot distinction
#   exposes: ClassTag, FACE_PLUS_CLASSES, FACE_MINUS_CLASSES, LITERAL_TYPES, AGGREGATE_SLOTS
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_class_tags
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_class_tags_holds
# === END CONTRACTS ===
"""Public type-class enumeration for the 157-gonal carrier."""
from __future__ import annotations
from enum import Enum


class ClassTag(str, Enum):
    """Public type-class tags for carrier slots.

    L = letters / structural units                  (literal type — hard invariant)
    N = numerals / quantitative units               (literal type — hard invariant)
    P = punctuation / connective units              (aggregate slot — resolved at runtime)
    X = primitive operators / structural primitives (aggregate slot — resolved at runtime)
    """
    L = "L"
    N = "N"
    P = "P"
    X = "X"


# Per the public spec: face +1 holds structural/relational (L, X);
# face -1 holds connective/quantitative (N, P).
FACE_PLUS_CLASSES: frozenset[ClassTag] = frozenset({ClassTag.L, ClassTag.X})
FACE_MINUS_CLASSES: frozenset[ClassTag] = frozenset({ClassTag.N, ClassTag.P})

# Literal types: hard invariant holds at the slot level (no L-L, no N-N).
LITERAL_TYPES: frozenset[ClassTag] = frozenset({ClassTag.L, ClassTag.N})

# Aggregate slots: hard invariant applies only after runtime resolution.
AGGREGATE_SLOTS: frozenset[ClassTag] = frozenset({ClassTag.P, ClassTag.X})
# ratios: loc_comments=11:52 imports_exports=2:1 calls_definitions=4:1
