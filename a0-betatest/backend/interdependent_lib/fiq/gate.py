# ratios: loc_comments=15:43 imports_exports=3:2 calls_definitions=3:3
# === MODULE_BUILD ===
# id: fiq_gate
#   module_name: gate
#   module_kind: schema
#   summary: FiqGate — the smallest auditable boundary gate r = (a, b, S, mode); not motion, the law that permits/blocks/meters motion
#   owner: Erin Spencer
#   public_surface: FiqGate, GateMode
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.fiq_gate_shape_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_gate_boundaries
#   summary: FiqGate — the smallest auditable boundary gate r = (a, b, S, mode); not motion, the law that permits/blocks/meters motion
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_gate
#   summary: FiqGate — the smallest auditable boundary gate r = (a, b, S, mode); not motion, the law that permits/blocks/meters motion
#   exposes: FiqGate, GateMode
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: fiq_gate_shape
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.fiq_gate_shape_holds
# === END CONTRACTS ===
"""FiqGate dataclass."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class GateMode(str, Enum):
    DIRECTED = "directed"
    BIDIRECTIONAL = "bidirectional"


@dataclass(frozen=True)
class FiqGate:
    """r = (a, b, S, mode) — boundary gate between distinctions a and b under support S."""
    a: str                          # source distinction id
    b: str                          # target distinction id
    support: str                    # support id (e.g. ring name, stratum, channel)
    mode: GateMode = GateMode.DIRECTED
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"FiqGate({self.a}→{self.b} @ {self.support} {self.mode.value})"
# ratios: loc_comments=15:43 imports_exports=3:2 calls_definitions=3:3
