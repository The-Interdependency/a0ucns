# ratios: loc_comments=129:64 imports_exports=5:3 calls_definitions=22:8
# === MODULE_BUILD ===
# id: fiq_sentinels
#   module_name: sentinels
#   module_kind: engine
#   summary: 9 sentinels (S1-S9) + R0 orchestration root + fiques_time probe; each enforces a χ indicator family or governs an outbound policy
#   owner: Erin Spencer
#   public_surface: Sentinel, SentinelRegistry, S1_AUDIT, S2_PARSER, S3_CONSTRAINT, S4_SAFETY, S5_DRIFT, S6_COHERENCE, S7_RECALL, S8_BUDGET, S9_OUTPUT, R0_ROOT, FIQUES_TIME, REGISTRY
#   internal_surface: none
#   auth_boundary: admin
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.sentinel_registry_complete_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_sentinels_boundaries
#   summary: 9 sentinels (S1-S9) + R0 orchestration root + fiques_time probe; each enforces a χ indicator family or governs an outbound policy
#   auth_boundary: admin
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_sentinels
#   summary: 9 sentinels (S1-S9) + R0 orchestration root + fiques_time probe; each enforces a χ indicator family or governs an outbound policy
#   exposes: Sentinel, SentinelRegistry, S1_AUDIT, S2_PARSER, S3_CONSTRAINT, S4_SAFETY, S5_DRIFT, S6_COHERENCE, S7_RECALL, S8_BUDGET, S9_OUTPUT, R0_ROOT, FIQUES_TIME, REGISTRY
#   boundaries: auth:admin, storage:read, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: sentinel_registry_complete
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.sentinel_registry_complete_holds
# === END CONTRACTS ===
"""Fiq motion sentinels — S1 through S9 + R0 + fiques_time.

Mapping per `fiq_sentinel_mapping_v01`:
  S1  audit             — provenance & audit gatekeeper      → χ_audit
  S2  parser            — route-table integrity              → χ_route
  S3  constraint        — EDCM overload + attention align    → χ_support, χ_attention
  S4  safety            — p_max ceiling + approval           → permeability
  S5  drift             — tick-schedule drift + carrier guard → tick attention
  S6  coherence         — support widening; carrier coherence → χ_support
  S7  recall            — last-known-good snapshots
  S8  budget            — κ_a capacity + ρ load
  S9  output            — outbound policy on FIQ_BLOCKED
  R0  root              — A0 orchestration root; unowned-hmmm escalation
  fiques_time           — ψ-core in ω-stratum (LCM 21ms); detection-only probe
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional

from .gate import FiqGate
from .events import AuditEvent, FIQ_BLOCKED


@dataclass
class Sentinel:
    """Base sentinel record. Each sentinel may inspect a gate event and emit a verdict."""
    name: str
    role: str
    indicators: tuple[str, ...] = ()
    authority: str = "advisory"   # 'advisory' | 'gate' | 'detection_only'
    can_emit_blocked: bool = True
    check: Optional[Callable[[FiqGate, dict], Optional[FIQ_BLOCKED]]] = field(default=None, repr=False)

    def evaluate(self, gate: FiqGate, context: dict) -> Optional[FIQ_BLOCKED]:
        """Return a FIQ_BLOCKED event iff this sentinel objects; None otherwise."""
        if self.check is None:
            return None
        return self.check(gate, context)


# ---- the canonical sentinel set --------------------------------------

S1_AUDIT = Sentinel(
    name="S1",
    role="audit",
    indicators=("chi_audit",),
    authority="gate",
)

S2_PARSER = Sentinel(
    name="S2",
    role="parser",
    indicators=("chi_route",),
    authority="gate",
)

S3_CONSTRAINT = Sentinel(
    name="S3",
    role="constraint",
    indicators=("chi_support", "chi_attention"),
    authority="gate",
)

S4_SAFETY = Sentinel(
    name="S4",
    role="safety",
    indicators=("permeability",),
    authority="gate",
)


def _s5_drift_check(gate: FiqGate, context: dict) -> Optional[FIQ_BLOCKED]:
    """Carrier-invariant guard: any update that would create an L-L or N-N adjacency
    is BLOCKED with reason `carrier_invariant_violation`."""
    violation = context.get("carrier_violation")
    if violation:
        return FIQ_BLOCKED(
            event_type="FIQ_BLOCKED",
            gate_a=gate.a,
            gate_b=gate.b,
            support=gate.support,
            tick_ms=context.get("tick_ms", 0),
            reason="carrier_invariant_violation",
            failing_indicator="carrier_invariant",
            payload={"violation": violation},
        ).seal()
    return None


S5_DRIFT = Sentinel(
    name="S5",
    role="drift",
    indicators=("tick_schedule", "carrier_invariant"),
    authority="gate",
    check=_s5_drift_check,
)

S6_COHERENCE = Sentinel(
    name="S6",
    role="coherence",
    indicators=("chi_support",),
    authority="gate",
)

S7_RECALL = Sentinel(
    name="S7",
    role="recall",
    indicators=(),
    authority="advisory",
    can_emit_blocked=False,
)

S8_BUDGET = Sentinel(
    name="S8",
    role="budget",
    indicators=("kappa", "rho"),
    authority="gate",
)

S9_OUTPUT = Sentinel(
    name="S9",
    role="output",
    indicators=(),
    authority="advisory",
    can_emit_blocked=False,
)

R0_ROOT = Sentinel(
    name="R0",
    role="orchestration_root",
    indicators=(),
    authority="advisory",
    can_emit_blocked=False,
)

# fiques_time probe — ψ-core in ω-stratum (LCM = 3 × 7 = 21 ms).
# Per spec: detection-only. May signal S1/S3/S5/S8 but MAY NOT emit FIQ_BLOCKED directly.
FIQUES_TIME = Sentinel(
    name="fiques_time",
    role="psi_in_omega_probe",
    indicators=("tick_schedule",),
    authority="detection_only",
    can_emit_blocked=False,
)


class SentinelRegistry:
    """Holds the canonical sentinel set + an evaluation walker."""

    def __init__(self):
        self._sentinels: list[Sentinel] = [
            S1_AUDIT, S2_PARSER, S3_CONSTRAINT, S4_SAFETY, S5_DRIFT,
            S6_COHERENCE, S7_RECALL, S8_BUDGET, S9_OUTPUT, R0_ROOT, FIQUES_TIME,
        ]

    def all(self) -> tuple[Sentinel, ...]:
        return tuple(self._sentinels)

    def by_name(self, name: str) -> Sentinel:
        for s in self._sentinels:
            if s.name == name:
                return s
        raise KeyError(name)

    def evaluate(self, gate: FiqGate, context: dict) -> list[FIQ_BLOCKED]:
        """Return all BLOCKED verdicts from sentinels that object."""
        out: list[FIQ_BLOCKED] = []
        for s in self._sentinels:
            verdict = s.evaluate(gate, context)
            if verdict is not None:
                out.append(verdict)
        return out


REGISTRY = SentinelRegistry()


__all__ = [
    "Sentinel", "SentinelRegistry", "REGISTRY",
    "S1_AUDIT", "S2_PARSER", "S3_CONSTRAINT", "S4_SAFETY", "S5_DRIFT",
    "S6_COHERENCE", "S7_RECALL", "S8_BUDGET", "S9_OUTPUT",
    "R0_ROOT", "FIQUES_TIME",
]
# ratios: loc_comments=129:64 imports_exports=5:3 calls_definitions=22:8
